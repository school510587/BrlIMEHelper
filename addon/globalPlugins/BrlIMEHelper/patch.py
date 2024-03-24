# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2024 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from ctypes import *
from ctypes.wintypes import *

try:
    from functools import partialmethod
    monkey_method = lambda m, cls: partialmethod(m)
except: # Python 2 does not have partialmethod.
    from types import MethodType
    monkey_method = lambda m, cls: MethodType(m, None, cls)

# api.copyToClip
try: # NVDA 2019.3 and later. The code only runs on Python 3 (and later).
    from winUser import openClipboard, emptyClipboard, setClipboardData, CF_UNICODETEXT
    def copyToClip(text):
        if not isinstance(text, str):
            raise TypeError("str required")
        import gui
        with openClipboard(gui.mainFrame.Handle):
            emptyClipboard()
            if text:
                setClipboardData(CF_UNICODETEXT, text)
except ImportError: # Earlier versions of NVDA (Python 2).
    from win32con import CF_TEXT, CF_UNICODETEXT
    import win32clipboard
    def copyToClip(text):
        if not isinstance(text, basestring):
            raise TypeError("basestring required")
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            if text:
                win32clipboard.SetClipboardData(CF_TEXT if isinstance(text, bytes) else CF_UNICODETEXT, text)
        finally:
            win32clipboard.CloseClipboard()

class _CLIENT_ID(Structure):
    _fields_ = [
        ("UniqueProcess", HANDLE),
        ("UniqueThread", HANDLE),
    ]

class _THREAD_BASIC_INFORMATION(Structure):
    _fields_ = [
        ("ExitStatus", LONG),
        ("TebBaseAddress", LPVOID),
        ("ClientId", _CLIENT_ID),
        ("AffinityMask", POINTER(ULONG)),
        ("Priority", LONG),
        ("BasePriority", LONG),
    ]

def getProcessIdOfThread(threadID):
    hThread, pid = windll.kernel32.OpenThread(0x40, False, threadID), 0
    if not hThread: raise WinError() # OpenThread() failed.
    try:
        pid = windll.kernel32.GetProcessIdOfThread(hThread)
    except: # Alternative implementation for GetProcessIdOfThread().
        tbi = _THREAD_BASIC_INFORMATION()
        status = LONG(windll.ntdll.NtQueryInformationThread(hThread, 0, byref(tbi), sizeof(tbi), None)).value
        if status < 0:
            raise WindowsError("NtQueryInformationThread() returns NTSTATUS({0}).".format(status))
        pid = DWORD(tbi.ClientId.UniqueProcess).value
        if not pid: raise WindowsError("NtQueryInformationThread() got invalid process ID.")
    else:
        if not pid: raise WinError() # GetProcessIdOfThread() failed.
    finally:
        if not windll.kernel32.CloseHandle(hThread): raise WinError()
    return pid

# speech.speakMessage, speech.priorities.SpeechPriority
import speech
try: # NVDA 2019.3 and later. The code only runs on Python 3 (and later).
    from speech.priorities import SpeechPriority
    def spellWithHighestPriority(ch):
        return speech.speakSpelling(ch, priority=SpeechPriority.NOW)
except ImportError: # Earlier versions of NVDA (Python 2).
    def spellWithHighestPriority(ch):
        speech.cancelSpeech()
        return speech.speakSpelling(ch)
