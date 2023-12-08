# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2023 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

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
