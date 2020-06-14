# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2020 Bo-Cheng Jhan <school510587@yahoo.com.tw>
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
from threading import Timer
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

from .brl_tables import *
from .runtime_state import thread_states
from .sounds import *
from . import configure
from . import hack_IME
from . import keyboard

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    SCRCAT_BrlIMEHelper = _("Braille IME Helper")

    # ACC_KEYS is the universe of all processed characters. BRL_KEYS and
    # SEL_KEYS must be its subsets. Note that they are currently replaced
    # by BRAILLE_KEYS and IGNORED_KEYS options, respectively. If the same
    # key is present in both options, the former takes precedence.
    ACC_KEYS = set(string.ascii_letters + string.digits + string.punctuation + " ")

    def __init__(self):
        super(GlobalPlugin, self).__init__()
        self.brl_state = brl_buf_state(os.path.join(os.path.dirname(__file__), str("bopomofo.json")), lambda m: log.error(m, exc_info=True))
        self.last_foreground = INVALID_HANDLE_VALUE
        thread_states.start_scan()
        self.timer = [None, ""] # A 2-tuple [timer object, string].
        configure.read()
        self.config_r = {
            "kbbrl_deactivated": False,
            "kbbrl_enabled": False,
            "no_ASCII_kbbrl": configure.get("DEFAULT_NO_ALPHANUMERIC_BRL_KEY"),
        }
        hack_IME.install()
        thread_states.cbrlkb = configure.get("AUTO_BRL_KEY")
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
        self.applyConfig()

    def terminate(self):
        try:
            gui.mainFrame.sysTrayIcon.toolsMenu.RemoveItem(self.BrlIMEHelper_item)
        except:
            pass
        hack_IME.uninstall()
        self.clear()
        thread_states.stop_scan()
        try:
            self.disable()
        except:
            pass
        configure.write()

    def applyConfig(self):
        thread_states.reset_cbrlkb_state()
        self.synchronize_cbrlkb_states(configure.get("CBRLKB_AUTO_TOGGLE_HINT"))
        self.kbmap = keyboard.Translator(*keyboard.layout[configure.get("KEYBOARD_MAPPING")])

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
        self.touched_mainKB_keys = OrderedDict()
        self._modifiedKeys = set()
        self._trappedKeys = set()
        self._trappedNVDAModifiers = set()
        self._gesture = None
        self._uncommittedDots = 0 # Dots recorded by NumPad keys.

    def enable(self, beep=False):
        if self.config_r["kbbrl_enabled"]:
            raise RuntimeError("Invalid call of enable().")
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
        if beep:
            beep_enable()

    def disable(self, beep=False):
        if not self.config_r["kbbrl_enabled"]:
            raise RuntimeError("Invalid call of disable().")
        winInputHook.keyDownCallback = self._oldKeyDown
        winInputHook.keyUpCallback = self._oldKeyUp
        KeyboardInputGesture.send = self.real_kb_send
        self._gesture = None
        self._trappedKeys = None
        self.config_r["kbbrl_enabled"] = False
        if beep:
            beep_disable()

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
            key_id, dots = vkCode & 0x0F, 0
            try:
                if currentModifiers or self._trappedNVDAModifiers or not configure.get("ALLOW_DOT_BY_DOT_BRL_INPUT_VIA_NUMPAD"):
                    raise NotImplementedError # Modified numpad keys, or the feature is not enabled.
                elif 0x00 <= key_id <= 0x08: # VK_NUMPAD0 to VK_NUMPAD8
                    dots = self._uncommittedDots | (1 << key_id)
                elif key_id == 0x09: # VK_NUMPAD9 = 0x69
                    pass # self._uncommittedDots is cleared.
                elif key_id == 0x0E: # VK_DECIMAL = 0x6E
                    if not self._uncommittedDots:
                        raise NotImplementedError # No uncommitted dots.
                    self._gesture = brailleInput.BrailleInputGesture()
                    self._gesture.space = bool(self._uncommittedDots & 0x01)
                    self._gesture.dots = self._uncommittedDots >> 1
                elif key_id == 0x0F: # VK_DIVIDE = 0x6F
                    dots = self._uncommittedDots
                    scriptHandler.queueScript(self.script_viewBRLbuffer, None)
                else:
                    raise NotImplementedError # Unused numpad keys.
            except NotImplementedError:
                self._modifiedKeys.add((vkCode, extended))
                return self._oldKeyDown(vkCode, scanCode, extended, injected)
            finally:
                self._uncommittedDots = dots
            self._trappedKeys.add((vkCode, extended))
            return False
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
        if (vkCode, extended) not in self.touched_mainKB_keys:
            self.touched_mainKB_keys[(vkCode, extended)] = ch
        if dot:
            if not self._gesture:
                self._gesture = brailleInput.BrailleInputGesture()
            log.debug("keydown: dots|space = {0:09b}".format(dot))
            if dot == 1:
                self._gesture.space = True
            self._gesture.dots |= dot >> 1
        else:
            log.debug("keydown: ignored = %s" % (ch,))
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
                if self.touched_mainKB_keys:
                    if self.config_r["no_ASCII_kbbrl"] and not(self.inferBRLmode() & 1) and not(self._gesture and self._gesture.dots and self._gesture.space):
                        self.send_keys(self.touched_mainKB_keys)
                    else:
                        touched_chars = set(self.touched_mainKB_keys.values())
                        k_brl, k_ign = set(configure.get("BRAILLE_KEYS")) & touched_chars, touched_chars
                        if self.inferBRLmode() & 1 or not configure.get("FREE_ALL_NON_BRL_KEYS_IN_ALPHANUMERIC_MODE"):
                            k_ign = set(configure.get("IGNORED_KEYS")) & k_ign # Not &= to avoid tamper of touched_chars.
                        if k_brl == touched_chars:
                            log.debug("keyup: send dot {0:08b} {1}".format(self._gesture.dots, self._gesture.space))
                            inputCore.manager.emulateGesture(self._gesture)
                        elif len(k_ign) == 1 and k_ign == touched_chars:
                            (ch,) = k_ign
                            self.send_keys(ch.lower())
                        else:
                            beep_typo()
                        self._uncommittedDots = 0
                else:
                    if self._gesture is not None:
                        inputCore.manager.emulateGesture(self._gesture)
            except inputCore.NoInputGestureAction:
                pass
            self._gesture = None
            self.touched_mainKB_keys.clear()
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
            cmd_list = self.kbmap.convert(string)
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

    def event_foreground(self, obj, nextHandler):
        fg = getForegroundWindow()
        if fg != self.last_foreground and not((getKeyState(VK_LMENU) | getKeyState(VK_RMENU)) & 32768):
            self.clear(join_timer=False)
            self.last_foreground = fg
            pid = getWindowThreadProcessID(self.last_foreground)[0]
            if thread_states.foreground_process_change_notify(pid):
                self.synchronize_cbrlkb_states(configure.get("CBRLKB_AUTO_TOGGLE_HINT"))
        nextHandler()

    def synchronize_cbrlkb_states(self, feedback):
        try:
            if thread_states.cbrlkb:
                if feedback == "audio":
                    self.enable(beep=True)
                else:
                    self.enable(beep=False)
                    if feedback == "ui.message":
                        # Translators: Reported when braille input from the PC keyboard is enabled.
                        ui.message(_("Enabled: Simulating braille keyboard by a computer keyboard."))
            else:
                if feedback == "audio":
                    self.disable(beep=True)
                else:
                    self.disable(beep=False)
                    if feedback == "ui.message":
                        # Translators: Reported when braille input from the PC keyboard is disabled.
                        ui.message(_("Disabled: Simulating braille keyboard by a computer keyboard."))
        except:
            pass

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
        gui.mainFrame._popupSettingsDialog(BrlIMEHelperSettingsDialog, set_deactivate_flag, self.applyConfig)

    def script_toggleBRLsimulation(self, gesture):
        thread_states.cbrlkb = not thread_states.cbrlkb
        self.synchronize_cbrlkb_states(configure.get("CBRLKB_MANUAL_TOGGLE_HINT"))
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
        numpad_state = "".join(str(i) for i in range(configure.NUM_BRAILLE_KEYS) if self._uncommittedDots & (1 << i))
        info = (("{0} ", "")[hint == ""] + ("#{1}", "")[numpad_state == ""]).format(hint, numpad_state)
        if info:
            queueHandler.queueFunction(queueHandler.eventQueue, ui.message, info)
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
