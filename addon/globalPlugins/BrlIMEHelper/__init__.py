# -*- coding: UTF-8 -*-
# Copyright (C) 2019 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from collections import OrderedDict
from ctypes import *
from ctypes.wintypes import *
from functools import partial
try:
    from functools import partialmethod
    monkey_method = lambda m, cls: partialmethod(m)
except: # Python 2 does not have partialmethod.
    from types import MethodType
    monkey_method = lambda m, cls: MethodType(m, None, cls)
from serial.win32 import INVALID_HANDLE_VALUE
from threading import Thread, Timer
import os
import string
import winsound
import wx
try: unichr
except NameError: unichr = chr
from keyboardHandler import KeyboardInputGesture, getInputHkl, isNVDAModifierKey, currentModifiers
from logHandler import log
from treeInterceptorHandler import DocumentTreeInterceptor
from winUser import *
from winVersion import winVersion
import addonHandler
import api
import brailleInput
import globalCommands
import globalPluginHandler
import gui
import inputCore
import queueHandler
import scriptHandler
import winInputHook
import ui

try:
    addonHandler.initTranslation()
except:
    log.warning("Exception occurred when loading translation.", exc_info=True)

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
    new_record = dict(zip(("mode", "layout"), (None, layoutString)))
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
from .sounds import *
from . import configure

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
    # SEL_KEYS must be its subsets. Note that they are currently replaced
    # by BRAILLE_KEYS and IGNORED_KEYS options, respectively. If the same
    # key is present in both options, the former takes precedence.
    ACC_KEYS = set(string.ascii_letters + string.digits + string.punctuation + " ")

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
        self.brl_state = brl_buf_state(os.path.join(os.path.dirname(__file__), str("bopomofo.json")), lambda m: log.error(m, exc_info=True))
        self.last_foreground = INVALID_HANDLE_VALUE
        self.running = True
        self.scanner = Thread(target=scan_thread_ids, args=(self,))
        self.scanner.start()
        self.timer = [None, ""] # A 2-tuple [timer object, string].
        configure.read()
        self.config_r = {
            "kbbrl_deactivated": False,
            "kbbrl_enabled": False,
            "no_ASCII_kbbrl": configure.get("DEFAULT_NO_ALPHANUMERIC_BRL_KEY"),
        }
        _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", hack_nvdaControllerInternal_inputConversionModeUpdate)
        _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", hack_nvdaControllerInternal_inputLangChangeNotify)
        if winVersion.major < 6: # WinXP
            del self.symb2gesture["UNICODE_SUFFIX"]
        if configure.get("AUTO_BRL_KEY"):
            self.enable()
        self.menu = wx.Menu()
        # Translators: Menu item of BrlIMEHelper settings.
        self.menuitem4Settings = self.menu.Append(wx.ID_ANY, _("&Settings..."))
        gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onSettings, self.menuitem4Settings)
        # Translators: Menu item to show the About window.
        self.menuitem4About = self.menu.Append(wx.ID_ANY, _("&About..."))
        gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onAbout, self.menuitem4About)
        self.BrlIMEHelper_item = gui.mainFrame.sysTrayIcon.toolsMenu.AppendSubMenu(self.menu,
            # Translators: Item of BrlIMEHelper configuration in NVDA tools menu.
            _("Braille IME Helper"),
            # Translators: Tooltip of BrlIMEHelper configuration item in NVDA tools menu.
            _("Configure Braille IME Helper"))

    def terminate(self):
        try:
            gui.mainFrame.sysTrayIcon.toolsMenu.RemoveItem(self.BrlIMEHelper_item)
        except:
            pass
        _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", nvdaControllerInternal_inputConversionModeUpdate)
        _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", nvdaControllerInternal_inputLangChangeNotify)
        self.clear()
        self.running = False
        self.scanner.join()
        self.disable()
        configure.write()

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
        self.touched_keys = OrderedDict()
        self._modifiedKeys = set()
        self._trappedKeys = set()
        self._trappedNVDAModifiers = set()
        self._gesture = None

    def enable(self):
        if self.config_r["kbbrl_enabled"]:
            return
        self.initKBBRL()
        def hack_kb_send(addon, *args):
            log.debug("Running monkeyed KeyboardInputGesture.send")
            if not args[0].isModifier and not args[0].modifiers and addon.config_r["kbbrl_enabled"]:
                addon.ignore_injected_keys[0].append((args[0].vkCode, args[0].scanCode, args[0].isExtended))
                addon.ignore_injected_keys[1].append(addon.ignore_injected_keys[0][-1])
            return addon.real_kb_send(*args)
        self.real_kb_send = KeyboardInputGesture.send
        KeyboardInputGesture.send = monkey_method(partial(hack_kb_send, self), KeyboardInputGesture)
        # Monkey patch keyboard handling callbacks.
        # This is pretty evil, but we need low level keyboard handling.
        self._oldKeyDown = winInputHook.keyDownCallback
        winInputHook.keyDownCallback = self._keyDown
        self._oldKeyUp = winInputHook.keyUpCallback
        winInputHook.keyUpCallback = self._keyUp
        self.config_r["kbbrl_enabled"] = True

    def disable(self):
        if not self.config_r["kbbrl_enabled"]:
            return False
        winInputHook.keyDownCallback = self._oldKeyDown
        winInputHook.keyUpCallback = self._oldKeyUp
        KeyboardInputGesture.send = self.real_kb_send
        self._gesture = None
        self._trappedKeys = None
        self.config_r["kbbrl_enabled"] = False

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
        # (3) The "kbbrl_deactivated" flag is set.
        def on_browse_mode():
            try:
                obj = api.getFocusObject()
                return (isinstance(obj.treeInterceptor, DocumentTreeInterceptor) and not obj.treeInterceptor.passThrough)
            except:
                pass
            return False
        if currentModifiers or self._trappedNVDAModifiers or on_browse_mode() or self.config_r["kbbrl_deactivated"]:
            if (vkCode, extended) not in self._trappedKeys:
                self._modifiedKeys.add((vkCode, extended))
                return self._oldKeyDown(vkCode, scanCode, extended, injected)
        charCode = user32.MapVirtualKeyExW(vkCode, MAPVK_VK_TO_CHAR, getInputHkl())
        if HIWORD(charCode) != 0:
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        ch = unichr(LOWORD(charCode))
        log.debug('char code: %d' % (charCode,))
        try:
            dot = 1 << configure.get("BRAILLE_KEYS").index(ch)
        except: # not found
            if ch not in self.ACC_KEYS:
                return self._oldKeyDown(vkCode, scanCode, extended, injected)
            dot = 0
        self._trappedKeys.add((vkCode, extended))
        if (vkCode, extended) not in self.touched_keys:
            self.touched_keys[(vkCode, extended)] = ch
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
            self._trappedKeys.remove((vkCode, extended))
        except KeyError:
            self._trappedNVDAModifiers.discard((vkCode, extended))
            self._modifiedKeys.discard((vkCode, extended))
            return self._oldKeyUp(vkCode, scanCode, extended, injected)
        if not self._trappedKeys: # A session ends.
            try: # Select an action to perform, either BRL or SEL.
                if self.config_r["no_ASCII_kbbrl"] and not(self.inferBRLmode() & 1) and not(self._gesture and self._gesture.dots and self._gesture.space):
                    self.send_keys(self.touched_keys)
                else:
                    touched_chars = set(self.touched_keys.values())
                    k_brl, k_sel = set(configure.get("BRAILLE_KEYS")) & touched_chars, set(configure.get("IGNORED_KEYS")) & touched_chars
                    if k_brl == touched_chars:
                        log.debug("keyup: send dot {0:08b} {1}".format(self._gesture.dots, self._gesture.space))
                        inputCore.manager.emulateGesture(self._gesture)
                    elif len(k_sel) == 1 and k_sel == touched_chars:
                        (ch,) = k_sel
                        self.send_keys(ch.lower())
                    else:
                        beep_typo()
            except inputCore.NoInputGestureAction:
                pass
            self._gesture = None
            self.touched_keys.clear()
        return False

    def send_keys(self, keys):
        try:
            if isinstance(keys, str) or isinstance(keys, unicode):
                keys = keys.split("|")
        except NameError: # Python 3 does not have unicode class.
            pass
        for k in keys:
            if not k: continue
            if isinstance(k, int):
                kbd_gesture = KeyboardInputGesture([], k, 1, False)
            elif isinstance(k, tuple):
                kbd_gesture = KeyboardInputGesture([], k[0], 1, k[1])
            else:
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
            beep_typo()

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

    def onAbout(self, evt):
        # Translators: The About message.
        gui.messageBox(_("""Braille IME Helper (BrlIMEHelper)
Copyright (C) 2019 Bo-Cheng Jhan and other contributors
BrlIMEHelper is covered by the GNU General Public License (Version 3). You are free to share or change this software in any way you like as long as it is accompanied by the license and you make all source code available to anyone who wants it. This applies to both original and modified copies of this software, plus any derivative works.
BrlIMEHelper is currently sponsored by "Taiwan Visually Impaired People Association" (vipastaiwan@gmail.com), hereby express my sincere appreciation.
If you feel this add-on is helpful, please don't hesitate to give support to "Taiwan Visually Impaired People Association" and authors."""),
            # Translators: Title of the About window.
            _("About BrlIMEHelper"), wx.OK)

    def onSettings(self, evt):
        from .dialogs import BrlIMEHelperSettingsDialog
        def set_deactivate_flag(b):
            self.config_r["kbbrl_deactivated"] = b
        gui.mainFrame._popupSettingsDialog(BrlIMEHelperSettingsDialog, set_deactivate_flag)

    def script_toggleBRLsimulation(self, gesture):
        if self.config_r["kbbrl_enabled"]:
            self.disable()
            # Translators: Reported when braille input from the PC keyboard is disabled.
            ui.message(_("Disabled: Simulating braille keyboard by a computer keyboard."))
        else:
            self.enable()
            # Translators: Reported when braille input from the PC keyboard is enabled.
            ui.message(_("Enabled: Simulating braille keyboard by a computer keyboard."))
    # Translators: Name of a command to toggle braille input from a computer keyboard.
    script_toggleBRLsimulation.__doc__ = _("Toggles braille input from a computer keyboard.")
    script_toggleBRLsimulation.category = SCRCAT_BrlIMEHelper

    def script_toggleAlphaModeBRLsimulation(self, gesture):
        self.config_r["no_ASCII_kbbrl"] = not self.config_r["no_ASCII_kbbrl"]
        if self.config_r["no_ASCII_kbbrl"]:
            # Translators: Reported when non-braille alphanumeric input during braille keyboard simulation is enabled.
            ui.message(_("Enabled: Don't simulate braille input in IME alphanumeric mode."))
        else:
            # Translators: Reported when non-braille alphanumeric input during braille keyboard simulation is disabled.
            ui.message(_("Disabled: Don't simulate braille input in IME alphanumeric mode."))
    # Translators: Name of a command to toggle braille simulation during alphanumeric input.
    # This means braille input simulation is disabled in alphanumeric IME mode.
    script_toggleAlphaModeBRLsimulation.__doc__ = _("Toggles non-braille alphanumeric input during braille keyboard simulation.")
    script_toggleAlphaModeBRLsimulation.category = SCRCAT_BrlIMEHelper

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
                beep_typo()
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
    # Translators: Name of a command to perform braille composition.
    script_BRLdots.__doc__ = _("Handles braille composition.")
    script_BRLdots.category = SCRCAT_BrlIMEHelper

    def script_clearBRLbuffer(self, gesture):
        self.clear()
    # Translators: Name of a command to clear braille buffer.
    script_clearBRLbuffer.__doc__ = _("Clear braille buffer.")
    script_clearBRLbuffer.category = SCRCAT_BrlIMEHelper

    def script_switchIMEmode(self, gesture):
        self.send_keys("Shift")
    # Translators: Name of a command to switch IME mode.
    script_switchIMEmode.__doc__ = _("Switches IME mode.")
    script_switchIMEmode.category = SCRCAT_BrlIMEHelper

    def script_viewBRLbuffer(self, gesture):
        hint = self.brl_state.hint_msg(self.brl_str, "")
        if hint:
            queueHandler.queueFunction(queueHandler.eventQueue, ui.message, hint)
        else:
            winsound.MessageBeep()
    # Translators: Name of a command to view braille buffer.
    script_viewBRLbuffer.__doc__ = _("View braille buffer.")
    script_viewBRLbuffer.category = SCRCAT_BrlIMEHelper

    __gestures = {
        "kb:NVDA+x": "toggleBRLsimulation",
        "bk:dots": "BRLdots",
        "bk:dot2+dot4+dot5+space": "clearBRLbuffer",
        "bk:dot1+dot2+dot3+space": "toggleAlphaModeBRLsimulation",
        "bk:dot4+dot5+dot6+space": "switchIMEmode",
        "bk:dot1+space": "viewBRLbuffer",
    }
