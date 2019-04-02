# -*- coding: UTF-8 -*-
# Copyright (C) 2019 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from ctypes import *
from ctypes.wintypes import *
from functools import partial
from serial.win32 import INVALID_HANDLE_VALUE
from threading import Thread, Timer
from types import MethodType
import os
import string
import winsound
try: unichr
except NameError: unichr = chr
from keyboardHandler import KeyboardInputGesture, getInputHkl, isNVDAModifierKey
from logHandler import log
from treeInterceptorHandler import DocumentTreeInterceptor
from winUser import *
from winVersion import winVersion
import addonHandler
import api
import brailleInput
import globalCommands
import globalPluginHandler
import inputCore
import queueHandler
import scriptHandler
import winInputHook
import ui

addonHandler.initTranslation()

from NVDAHelper import localLib
from NVDAHelper import nvdaControllerInternal_inputConversionModeUpdate
from NVDAHelper import nvdaControllerInternal_inputLangChangeNotify
from NVDAHelper import _setDllFuncPointer
thread_states = {}
kl, layout = None, None
# Note: Monkeying handleInputConversionModeUpdate does not work.
@WINFUNCTYPE(c_long, c_long, c_long, c_ulong)
def hack_nvdaControllerInternal_inputConversionModeUpdate(oldFlags, newFlags, lcid):
    global thread_states
    pid = getWindowThreadProcessID(getForegroundWindow())[0]
    new_record = dict(zip(("mode", "layout"), (newFlags, "")))
    if pid in thread_states: new_record["layout"] = thread_states[pid]["layout"]
    thread_states[pid] = new_record
    log.debug('Logged IME mode change: pid={pid}, layout="{layout}", mode={mode}'.format(pid=pid, **thread_states[pid]))
    return nvdaControllerInternal_inputConversionModeUpdate(c_long(oldFlags), c_long(newFlags), c_ulong(lcid))
@WINFUNCTYPE(c_long, c_long, c_ulong, c_wchar_p)
def hack_nvdaControllerInternal_inputLangChangeNotify(threadID, hkl, layoutString):
    global thread_states
    pid = getWindowThreadProcessID(getForegroundWindow())[0]
    new_record = dict(zip(("mode", "layout"), (0, layoutString)))
    if pid in thread_states: new_record["mode"] = thread_states[pid]["mode"]
    thread_states[pid] = new_record
    log.debug('Logged IME language change: pid={pid}, layout="{layout}", mode={mode}'.format(pid=pid, **thread_states[pid]))
    return nvdaControllerInternal_inputLangChangeNotify(threadID, hkl, layoutString)

def scan_thread_ids(addon_inst):
    from time import sleep
    global thread_states
    while addon_inst.running:
        try:
            for pid in list(thread_states): # Use list() to avoid runtime error by size change.
                h = windll.Kernel32.OpenProcess(0x100000, 0, pid) # With SYNCHRONIZE access.
                if h: # The process exists.
                    windll.Kernel32.CloseHandle(h)
                else:
                    del thread_states[pid]
                    log.debug("Killed pid=%d" % (pid,))
        except:
            log.error("scan_thread_ids", exc_info=True)
        sleep(0.01)

from .brl_tables import *

bopomofo_to_keys = { # 標準注音鍵盤
        "ㄅ": "1",
        "ㄆ": "q",
        "ㄇ": "a",
        "ㄈ": "z",
        "ㄉ": "2",
        "ㄊ": "w",
        "ㄋ": "s",
        "ㄌ": "x",
        "ㄍ": "e",
        "ㄎ": "d",
        "ㄏ": "c",
        "ㄐ": "r",
        "ㄑ": "f",
        "ㄒ": "v",
        "ㄓ": "5",
        "ㄔ": "t",
        "ㄕ": "g",
        "ㄖ": "b",
        "ㄗ": "y",
        "ㄘ": "h",
        "ㄙ": "n",
        "ㄧ": "u",
        "ㄨ": "j",
        "ㄩ": "m",
        "ㄚ": "8",
        "ㄛ": "i",
        "ㄜ": "k",
        "ㄝ": ",",
        "ㄞ": "9",
        "ㄟ": "o",
        "ㄠ": "l",
        "ㄡ": ".",
        "ㄢ": "0",
        "ㄣ": "p",
        "ㄤ": ";",
        "ㄥ": "/",
        "ㄦ": "-",
        "˙": "7",
        "ˊ": "6",
        "ˇ": "3",
        "ˋ": "4",
        " ": " ",
}

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    SCRCAT_BrlIMEHelper = _("Braille IME Helper")

    # ACC_KEYS is the universe of all processed characters. BRL_KEYS and
    # SEL_KEYS must be its two disjoint subsets. Note that BRL_KEYS must
    # be ordered.
    ACC_KEYS = set(string.ascii_letters + string.digits + string.punctuation + " ")
    BRL_KEYS = " FDSJKLA;"
    SEL_KEYS = set("0123456789")

    symb2gesture = {
        "UNICODE_PREFIX": "`u",
        "UNICODE_SUFFIX": " ",
        "※": "Control+Alt+,|r",
        "←": "Control+Alt+,|b",
        "↑": "Control+Alt+,|h",
        "→": "Control+Alt+,|n",
        "↓": "Control+Alt+,|j",
        "─": "Control+Alt+,|z",
        "、": "Control+'",
        "。": "Control+.",
        "「": "Control+Alt+,|=",
        "」": "Control+Alt+,|\\",
        "『": "Control+Alt+,|0",
        "』": "Control+Alt+,|-",
        "【": "Control+[",
        "】": "Control+]",
        "！": "Control+!",
        "，": "Control+,",
        "：": "Control+:",
        "；": "Control+;",
        "？": "Control+?",
        "｛": "Control+{",
        "｝": "Control+}",
    }

    def __init__(self):
        super(GlobalPlugin, self).__init__()
        self.kbbrl_enabled = False
        self.brl_state = brl_buf_state(os.path.join(os.path.dirname(__file__), "bopomofo.json"), lambda m: log.error(m, exc_info=True))
        self.last_foreground = INVALID_HANDLE_VALUE
        self.running = True
        self.scanner = Thread(target=scan_thread_ids, args=(self,))
        self.scanner.start()
        self.timer = [None, ""] # A 2-tuple [timer object, string].
        _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", hack_nvdaControllerInternal_inputConversionModeUpdate)
        _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", hack_nvdaControllerInternal_inputLangChangeNotify)
        if winVersion.major < 6: # WinXP
            del self.symb2gesture["UNICODE_SUFFIX"]

    def terminate(self):
        _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", nvdaControllerInternal_inputConversionModeUpdate)
        _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", nvdaControllerInternal_inputLangChangeNotify)
        self.clear()
        self.running = False
        self.scanner.join()
        self.disable()

    def clear(self, brl_buffer=True, join_timer=True):
        if self.timer[0]:
            self.timer[0].cancel()
            if join_timer:
                self.timer[0].join()
            self.timer[0] = None
        if brl_buffer:
            self.timer[1] = ""
            self.brl_str = ""

    def initKBBRL(self): # Members for keyboard BRL simulation.
        self.ignore_injected_keys = ([], [])
        self.touched_chars = set()
        self._modifiedKeys = set()
        self._trappedKeys = set()
        self._trappedNVDAModifiers = set()
        self._gesture = None

    def enable(self):
        if self.kbbrl_enabled:
            return
        self.initKBBRL()
        def hack_kb_send(addon, *args):
            log.debug("Running monkeyed KeyboardInputGesture.send")
            if not args[0].isModifier and not args[0].modifiers and addon.kbbrl_enabled:
                addon.ignore_injected_keys[0].append((args[0].vkCode, args[0].scanCode, args[0].isExtended))
                addon.ignore_injected_keys[1].append(addon.ignore_injected_keys[0][-1])
            return addon.real_kb_send(*args)
        self.real_kb_send = KeyboardInputGesture.send
        try:
            KeyboardInputGesture.send = MethodType(partial(hack_kb_send, self), None, KeyboardInputGesture)
        except TypeError: # Python 3: Unbound method no longer exists.
            KeyboardInputGesture.send = MethodType(partial(hack_kb_send, self), None, KeyboardInputGesture)
        # Monkey patch keyboard handling callbacks.
        # This is pretty evil, but we need low level keyboard handling.
        self._oldKeyDown = winInputHook.keyDownCallback
        winInputHook.keyDownCallback = self._keyDown
        self._oldKeyUp = winInputHook.keyUpCallback
        winInputHook.keyUpCallback = self._keyUp
        self.kbbrl_enabled = True

    def disable(self):
        if not self.kbbrl_enabled:
            return False
        winInputHook.keyDownCallback = self._oldKeyDown
        winInputHook.keyUpCallback = self._oldKeyUp
        KeyboardInputGesture.send = self.real_kb_send
        self._gesture = None
        self._trappedKeys = None
        self.kbbrl_enabled = False

    def _keyDown(self, vkCode, scanCode, extended, injected):
        log.debug("keydown: vk = 0x%02X%s" % (vkCode, ", injected" if injected else ""))
        # Fix: Ctrl+X followed by X.
        try: # Check for keys that must be ignored.
            if self.ignore_injected_keys[0][0] != (vkCode, scanCode, bool(extended)):
                raise ValueError
            log.debug("keydown: pass injected key 0x%02X" % (vkCode,))
            del self.ignore_injected_keys[0][0]
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        except: pass
        # Note: 2017.3 doesn't support getNVDAModifierKeys.
        if isNVDAModifierKey(vkCode, extended) or vkCode in KeyboardInputGesture.NORMAL_MODIFIER_KEYS:
            self._trappedNVDAModifiers.add((vkCode, extended))
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        # Don't process vkCode if it is previously modified.
        if (vkCode, extended) in self._modifiedKeys:
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        # Don't process any numpad key.
        if vkCode & 0xF0 == 0x60:
            self._modifiedKeys.add((vkCode, extended))
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        # In some cases, a key not previously trapped must be passed
        # directly to NVDA:
        # (1) Any modifier key is held down.
        # (2) NVDA is in browse mode.
        obj = api.getFocusObject()
        if self._trappedNVDAModifiers or isinstance(obj.treeInterceptor, DocumentTreeInterceptor) and not obj.treeInterceptor.passThrough:
            if (vkCode, extended) not in self._trappedKeys:
                self._modifiedKeys.add((vkCode, extended))
                return self._oldKeyDown(vkCode, scanCode, extended, injected)
        charCode = user32.MapVirtualKeyExW(vkCode, MAPVK_VK_TO_CHAR, getInputHkl())
        if HIWORD(charCode) != 0:
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        ch = unichr(LOWORD(charCode))
        log.debug('char code: %d' % (charCode,))
        try:
            dot = 1 << self.BRL_KEYS.index(ch)
        except: # not found
            if ch not in self.ACC_KEYS:
                return self._oldKeyDown(vkCode, scanCode, extended, injected)
            dot = 0
        self._trappedKeys.add(vkCode)
        self.touched_chars.add(ch)
        if dot:
            if not self._gesture:
                self._gesture = brailleInput.BrailleInputGesture()
            log.debug("keydown: dots|space = {0:09b}".format(dot))
            if dot == 1:
                self._gesture.space = True
            self._gesture.dots |= dot >> 1
        else: log.debug("keydown: num = %s" % (ch,))
        return False

    def _keyUp(self, vkCode, scanCode, extended, injected):
        log.debug("keyup: vk = 0x%02X%s" % (vkCode, ", injected" if injected else ""))
        try:
            if self.ignore_injected_keys[1][0] != (vkCode, scanCode, bool(extended)):
                raise ValueError
            log.debug("keyup: pass injected key 0x%02X" % (vkCode,))
            del self.ignore_injected_keys[1][0]
            return self._oldKeyUp(vkCode, scanCode, extended, injected)
        except: pass
        try:
            self._trappedKeys.remove(vkCode)
        except KeyError:
            self._trappedNVDAModifiers.discard((vkCode, extended))
            self._modifiedKeys.discard((vkCode, extended))
            return self._oldKeyUp(vkCode, scanCode, extended, injected)
        if not self._trappedKeys: # A session ends.
            k_brl, k_sel = set(self.BRL_KEYS) & self.touched_chars, self.SEL_KEYS & self.touched_chars
            try: # Select an action to perform, either BRL or SEL.
                if k_brl == self.touched_chars:
                    log.debug("keyup: send dot {0:08b} {1}".format(self._gesture.dots, self._gesture.space))
                    inputCore.manager.emulateGesture(self._gesture)
                elif len(k_sel) == 1 and k_sel == self.touched_chars:
                    (ch,) = k_sel
                    self.send_keys(ch)
                else: winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except inputCore.NoInputGestureAction:
                pass
            self._gesture = None
            self.touched_chars.clear()
        return False

    def send_keys(self, key_name_str):
        for k in key_name_str.split("|"):
            if not k: continue
            kbd_gesture = KeyboardInputGesture.fromName(k)
            inputCore.manager.emulateGesture(kbd_gesture)

    def send_input_commands(self, string):
        try:
            cmd_list = []
            for c in string:
                key_name_str = self.symb2gesture.get(c, bopomofo_to_keys.get(c))
                if key_name_str is None: # Lookup failure.
                    key_name_str = "%s%04x%s" % (self.symb2gesture["UNICODE_PREFIX"], ord(c), self.symb2gesture.get("UNICODE_SUFFIX", ""))
                    key_name_str = "|".join(key_name_str) # Insert "|" between characters.
                cmd_list.append(key_name_str)
            for cmd in cmd_list:
                log.debug('Sending "%s"' % (cmd,))
                self.send_keys(cmd)
        except:
            log.warning('Undefined input gesture of "%s"' % (string,))
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

    def send_input_and_clear(self, string):
        queueHandler.queueFunction(queueHandler.eventQueue, self.send_input_commands, string)
        self.timer[0] = None
        self.timer[1] = ""
        self.brl_str = ""

    def event_gainFocus(self, obj, nextHandler):
        fg = getForegroundWindow()
        if fg != self.last_foreground:
            self.clear(join_timer=False)
            self.last_foreground = fg
        nextHandler()

    def script_toggleInput(self, gesture):
        if self.kbbrl_enabled:
            self.disable()
            # Translators: Reported when braille input from the PC keyboard is disabled.
            ui.message(_("Disabled: Simulating braille keyboard by a computer keyboard."))
        else:
            self.enable()
            # Translators: Reported when braille input from the PC keyboard is enabled.
            ui.message(_("Enabled: Simulating braille keyboard by a computer keyboard."))
    # Translators: Describes the toggling braille input from a computer keyboard command.
    script_toggleInput.__doc__ = _("Toggles braille input from a computer keyboard.")
    script_toggleInput.category = SCRCAT_BrlIMEHelper

    def inferBRLmode(self):
        global thread_states
        pid, tid = getWindowThreadProcessID(getForegroundWindow())
        kl = getKeyboardLayout(tid)
        if winVersion.major < 6 and kl == 0x04040404: # WinXP
            return 0
        elif pid not in thread_states or thread_states[pid]["mode"] is None:
            return 2
        elif thread_states[pid]["mode"] & 1 and LOWORD(kl) == 0x0404:
            return 1
        return 0 # ENG

    def brl_composition(self, ubrl, mode):
        try: # Normal input progress.
            if not (mode & 1):
                raise NotImplementedError
            brl_input = self.brl_str + ubrl
            state = self.brl_state.brl_check(brl_input)
            self.timer[1] = "" # Purge the pending input.
            self.brl_str = brl_input
        except NotImplementedError: # ENG mode, or input is rejected by brl parser.
            if self.timer[1]:
                self.send_input_and_clear(self.timer[1])
                if not (mode & 1): # No braille composition in ENG mode.
                    raise
                brl_input = ubrl # Retry after sending the pending input.
            elif len(self.brl_str) >= len(ubrl) and self.brl_str != ubrl:
                brl_input = self.brl_str[:-len(ubrl)] + ubrl # Retry substitution of the most recent braille input.
            else: # No pending braille input, and no retry.
                raise
            state = self.brl_state.brl_check(brl_input)
            self.brl_str = brl_input
        return state

    def script_BRLdots(self, gesture):
        mode, mode_msgs, new_brl = self.inferBRLmode(), [], ""
        if mode & 2: mode_msgs.append("assumed")
        mode_msgs.append(("ENG", "CHI")[mode & 1])
        log.debug("BRLkeys: Mode is " + (" ".join(mode_msgs)))
        if mode & 1: # CHI
            self.clear(brl_buffer=False)
        try:
            state = self.brl_composition(unichr(0x2800 | gesture.dots), mode)
        except NotImplementedError: # ENG mode, or input is rejected by brl parser.
            if gesture.dots == 0b01000000:
                log.debug("BRLkeys: dot7 default")
                scriptHandler.queueScript(globalCommands.commands.script_braille_eraseLastCell, gesture)
            elif gesture.dots == 0b10000000:
                log.debug("BRLkeys: dot8 default")
                scriptHandler.queueScript(globalCommands.commands.script_braille_enter, gesture)
            elif gesture.dots == 0b11000000:
                log.debug("BRLkeys: dot7+dot8 default")
                scriptHandler.queueScript(globalCommands.commands.script_braille_translate, gesture)
            elif mode & 1:
                log.debug("BRLkeys: input rejected")
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            else:
                log.debug("BRLkeys: dots default")
                self.clear()
                scriptHandler.queueScript(globalCommands.commands.script_braille_dots, gesture)
            return
        except:
            log.error("BRLkeys: Unexpected error.", exc_info=True)
            self.clear()
            winsound.MessageBeep(winsound.MB_ICONHAND)
            return
        log.debug('BRLkeys: Done composition "{0}"'.format(state[0]))
        if state[0]: # Composition completed with non-empty output.
            if state[1]: # The co-exist intermediate state.
                self.timer = [Timer(0.25, self.send_input_and_clear, (state[0],)), state[0]]
                self.timer[0].start()
            else:
                self.send_input_and_clear(state[0])
    # Translators: Describes the braille composition command.
    script_BRLdots.__doc__ = _("Handles braille composition.")
    script_BRLdots.category = SCRCAT_BrlIMEHelper

    def script_BRLfnkeys(self, gesture):
        if gesture.dots == 0b00000001: # bk:dot1
            hint = self.brl_state.hint_msg(self.brl_str, "")
            if hint: queueHandler.queueFunction(queueHandler.eventQueue, ui.message, hint)
            else: winsound.MessageBeep()
        elif gesture.dots == 0b00011010: # bk:dot2+dot4+dot5
            self.clear()
        elif gesture.dots == 0b00111000: # bk:dot4+dot5+dot6
            log.debug("456+space")
            self.send_keys("Shift")
    # Translators: Describes the braille function keys command.
    script_BRLfnkeys.__doc__ = _("Handles braille function keys.")
    script_BRLfnkeys.category = SCRCAT_BrlIMEHelper

    __gestures = {
        "kb:NVDA+x": "toggleInput",
        "bk:dots": "BRLdots",
        "bk:space+dots": "BRLfnkeys",
    }
