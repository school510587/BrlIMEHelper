# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2024 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from collections import OrderedDict
from ctypes import *
from ctypes.wintypes import *
from functools import partial
from serial.win32 import INVALID_HANDLE_VALUE
from threading import Timer
import louis
import os
import re
import sys
import winsound
import wx
try: unichr
except NameError: unichr = chr
from NVDAObjects.behaviors import CandidateItem
from brailleTables import getTable as getBRLtable
from eventHandler import queueEvent
from keyboardHandler import KeyboardInputGesture, getInputHkl
from logHandler import log
from winUser import *
import addonHandler
import api
import braille
import brailleInput
import globalCommands
import globalPluginHandler
import gui
import inputCore
import queueHandler
import scriptHandler
import speech
import ui

try:
    addonHandler.initTranslation()
except:
    log.warning("Exception occurred when loading translation.", exc_info=True)

from .brl_tables import *
from .msctf import *
from .runtime_state import *
from .sounds import *
from . import configure
from . import hack_IME
from . import keyboard
from . import keyboard_hook
from . import patch

# A helper function to construct GlobalPlugin.default_bk_gestures.
def _make_bk_gesture_set(dots, main, var1="kb:control+", var2="kb:alt+", var3="kb:control+alt+", key=None):
    if dots < 0 or dots % 10 > 6:
        raise ValueError("Invalid dots: {0}".format(dots))
    elif dots == 0 and main is not None: # This causes command binding to bk:space.
        raise ValueError("Invalid: dots is 0 and main is not None")
    def int2bk_gesture(i):
        bk_dots = "%d" % i
        if not all(ord(bk_dots[j]) < ord(bk_dots[j+1]) for j in range(len(bk_dots) - 1)):
            log.error("Ill-formed dot pattern: " + bk_dots)
        return "+".join(["space"] + [("dot" + d) for d in bk_dots])
    def parse_name(s):
        l = s.split(".")
        if len(l) == 1: # The default module and class.
            l = ["globalCommands", "GlobalCommands"] + l
        elif len(l) == 2:
            if l[0] != "GlobalPlugin":
                raise ValueError("Both module and class must be assigned: " + s)
            l = ["globalPlugins.BrlIMEHelper"] + l
        elif len(l) > 3:
            l = [".".join(l[:-2]), l[-2], l[-1]]
        return tuple(l)
    result = []
    if key is None and main is not None and main.startswith("kb:"):
        key = main[3:]
    if main is not None:
        result.append((int2bk_gesture(dots), parse_name(main)))
    if var1 is not None:
        if var1.endswith("+"):
            var1 = None if key is None else (var1 + key)
        if var1 is not None:
            result.append((int2bk_gesture(dots * 10 + 7), parse_name(var1)))
    if var2 is not None:
        if var2.endswith("+"):
            var2 = None if key is None else (var2 + key)
        if var2 is not None:
            result.append((int2bk_gesture(dots * 10 + 8), parse_name(var2)))
    if var3 is not None:
        if var3.endswith("+"):
            var3 = None if key is None else (var3 + key)
        if var3 is not None:
            result.append((int2bk_gesture(dots * 100 + 78), parse_name(var3)))
    return result

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    SCRCAT_BrlIMEHelper = addonHandler.getCodeAddon().manifest["summary"]

    def __init__(self):
        super(GlobalPlugin, self).__init__()
        keyboard.initialize()
        self.brl_state = brl_buf_state(os.path.join(os.path.dirname(__file__), str("bopomofo.json")), lambda m: log.error(m, exc_info=True))
        self.last_foreground = INVALID_HANDLE_VALUE
        thread_states.start_scan()
        self.timer = [None, ""] # A 2-tuple [timer object, string].
        self.old_louis_translate = None
        self.originalBRLtable = None
        configure.read()
        self.config_r = {
            "copy_raw_text_from_BRL_display": True,
            "kbbrl_deactivated": False,
            "kbbrl_enabled": False,
            "kbbrl_ASCII_mode": [
                configure.get("DEFAULT_NO_ALPHANUMERIC_BRL_KEY"),
                False,
            ],
        }
        self.kbh = None
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
        def hack_bd_driver_init(real_init, self, *args):
            if real_init is not None:
                real_init(self, *args)
            keyboard_hook.DummyBrailleInputGesture.update_brl_display_gesture_map(GlobalPlugin, self)
        try: # Python 3
            self.real_bd_driver_init = braille.BrailleDisplayDriver.__init__
        except: # Python 2
            self.real_bd_driver_init = None
        braille.BrailleDisplayDriver.__init__ = patch.monkey_method(partial(hack_bd_driver_init, self.real_bd_driver_init), braille.BrailleDisplayDriver)
        keyboard_hook.DummyBrailleInputGesture.update_brl_display_gesture_map(GlobalPlugin) # The current built one.
        hack_IME.install()

    def terminate(self):
        hack_IME.uninstall()
        if self.old_louis_translate is not None:
            try: # Cancel the internal code braille.
                self.script_internalCodeBRL(None)
            except:
                pass
        if self.real_bd_driver_init is None: # Python 2
            del braille.BrailleDisplayDriver.__init__ 
        else: # Python 3
            braille.BrailleDisplayDriver.__init__ = self.real_bd_driver_init
        try:
            gui.mainFrame.sysTrayIcon.toolsMenu.RemoveItem(self.BrlIMEHelper_item)
        except:
            pass
        self.clear()
        thread_states.stop_scan()
        try:
            self.disable()
        except:
            pass
        configure.write()

    def applyConfig(self, dirty=None):
        if dirty is None or "ONE_CBRLKB_TOGGLE_STATE" in dirty:
            thread_states.reset_cbrlkb_state()
            self.synchronize_cbrlkb_states(configure.get("CBRLKB_AUTO_TOGGLE_HINT"))
        if dirty is None or "KEYBOARD_MAPPING" in dirty:
            self.kbmap = keyboard.Translator(*keyboard.layout[configure.get("KEYBOARD_MAPPING")])

    def clear(self, brl_buffer=True, join_timer=True):
        action = False
        if self.timer[0]:
            self.timer[0].cancel()
            if join_timer:
                self.timer[0].join()
            self.timer[0] = None
        if brl_buffer:
            action = action or bool(self.timer[1])
            self.timer[1] = ""
            try: action = action or bool(self.brl_str)
            except AttributeError: pass
            self.brl_str = ""
            if self.kbh:
                reset_numpad = self.kbh.reset_numpad_state()
                action = action or reset_numpad
        return action

    def enable(self, beep=False):
        if self.config_r["kbbrl_enabled"]:
            raise RuntimeError("Invalid call of enable().")
        # Monkey patch keyboard handling callbacks.
        # This is pretty evil, but we need low level keyboard handling.
        self.kbh = keyboard_hook.KeyboardHook(self)
        self.config_r["kbbrl_enabled"] = True
        if beep:
            beep_enable()

    def disable(self, beep=False):
        if not self.config_r["kbbrl_enabled"]:
            raise RuntimeError("Invalid call of disable().")
        self.kbh.terminate()
        self.kbh = None
        self.config_r["kbbrl_enabled"] = False
        if beep:
            beep_disable()

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
            elif len(k) > 1:
                kbd_gesture = KeyboardInputGesture.fromName(k)
            else:
                brailleInput.handler.sendChars(k)
                continue
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
            if self.clear(join_timer=False):
                log.debug("self.clear() in event_foreground()")
                beep_typo()
            self.last_foreground = fg
            pid = getWindowThreadProcessID(self.last_foreground)[0]
            if thread_states.foreground_process_change_notify(pid):
                self.synchronize_cbrlkb_states(configure.get("CBRLKB_AUTO_TOGGLE_HINT"))
        nextHandler()

    def event_gainFocus(self, obj, nextHandler):
        if isinstance(obj, CandidateItem):
            queueEvent("interruptBRLcomposition", api.getFocusObject())
        nextHandler()

    def event_interruptBRLcomposition(self, obj, nextHandler):
        log.debug("Running event_interruptBRLcomposition")
        if self.clear():
            log.debug("self.clear() in event_interruptBRLcomposition()")
            beep_typo()
        nextHandler()

    def event_showInputConversionMode(self, obj, nextHandler, ui_message=ui.message, args=(), kwargs={}):
        log.debug("Running event_showInputConversionMode")
        if len(args) > 0 and self.kbh is not None and not self.kbh.disabled():
            try:
                IME_state = keyboard.infer_IME_state(obj.windowHandle)
            except ValueError as e:
                IME_state = e.args[0]
            args = ("{0} {1}".format(args[0], keyboard_hook.input_mode_name(IME_state, self.config_r["kbbrl_ASCII_mode"])),) + args[1:]
        ui_message(*args, **kwargs)
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

    def brl_composition(self, ubrl, IME_state):
        try: # Normal input progress.
            if not IME_state.is_native:
                raise NotImplementedError
            brl_input = self.brl_str + ubrl
            state = self.brl_state.brl_check(brl_input)
            self.timer[1] = "" # Purge the pending input.
            self.brl_str = brl_input
        except NotImplementedError: # The alphanumeric mode, or the input is rejected by the brl parser.
            if self.timer[1]:
                self.send_input_and_clear(self.timer[1])
                if not IME_state.is_native: # No braille composition in the alphanumeric mode.
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

    def script_switchMainKBInputManner(self, gesture):
        if self.kbh is None or self.kbh.disabled():
            ui.message(_("Failed to change the input manner of the main keyboard."))
            return
        try:
            IME_state = keyboard.infer_IME_state()
        except ValueError as e:
            IME_state = e.args[0]
        self.config_r["kbbrl_ASCII_mode"][IME_state.is_native] = not self.config_r["kbbrl_ASCII_mode"][IME_state.is_native]
        ui.message(keyboard_hook.input_mode_name(IME_state, self.config_r["kbbrl_ASCII_mode"]))
    # Translators: Name of a command to switch the input manner of the main keyboard.
    script_switchMainKBInputManner.__doc__ = _("Switch the input manner of the main keyboard.")
    script_switchMainKBInputManner.category = SCRCAT_BrlIMEHelper

    def script_toggleUnicodeBRL(self, gesture):
        try:
            unicodeBRLtable = getBRLtable("unicode-braille.utb")
        except:
            log.error("Cannot find unicode-braille.utb", exc_info=True)
            return
        try:
            if brailleInput.handler.table is not unicodeBRLtable:
                brailleInput.handler.table, self.originalBRLtable = unicodeBRLtable, brailleInput.handler.table
            elif self.originalBRLtable is not None and self.originalBRLtable is not unicodeBRLtable:
                brailleInput.handler.table, self.originalBRLtable = self.originalBRLtable, None
            else: # The user has never set the braille input table to any other table since NVDA started.
                us_comp8_table = getBRLtable("en-us-comp8-ext.utb")
                brailleInput.handler.table, self.originalBRLtable = us_comp8_table, None
            ui.message(_('The braille input translation table has been changed to "{0}"').format(brailleInput.handler.table.displayName))
        except:
            log.error("script_toggleUnicodeBRL performs no action.", exc_info=True)
            play_NVDA_sound("error")
    # Translators: Name of a command to switch between unicode-braille.utb and any other braille input translation table.
    script_toggleUnicodeBRL.__doc__ = _("Switches between the Unicode braille input translation table and any other input translation table.")
    script_toggleUnicodeBRL.category = SCRCAT_BrlIMEHelper

    def script_BRLdots(self, gesture):
        mode_msgs, new_brl = [], ""
        try:
            IME_state = keyboard.infer_IME_state()
        except ValueError as e:
            IME_state = e.args[0]
            mode_msgs.append("assumed")
        mode_msgs.append(("ENG", "CHI")[bool(IME_state.mode & TF_CONVERSIONMODE_NATIVE)])
        log.debug("BRLkeys: Mode is " + (" ".join(mode_msgs)))
        if IME_state.is_native:
            self.clear(brl_buffer=False)
        try:
            ucbrl = unichr(0x2800 | gesture.dots)
            state = self.brl_composition(ucbrl, IME_state)
            if configure.get("REPORT_BRL_BUFFER_CHANGES"):
                speech.speakMessage(gesture.displayName)
        except NotImplementedError: # The alphanumeric mode, or the input is rejected by the brl parser.
            done = False
            if gesture.dots == 0b01000000:
                if IME_state.is_native or not isinstance(gesture, keyboard_hook.DummyBrailleInputGesture) or brailleInput.handler.table.fileName.lower() != "unicode-braille.utb":
                    log.debug("BRLkeys: dot7 default")
                    scriptHandler.queueScript(globalCommands.commands.script_braille_eraseLastCell, gesture)
                    done = True
            elif gesture.dots == 0b10000000:
                if IME_state.is_native or not isinstance(gesture, keyboard_hook.DummyBrailleInputGesture) or brailleInput.handler.table.fileName.lower() != "unicode-braille.utb":
                    log.debug("BRLkeys: dot8 default")
                    scriptHandler.queueScript(globalCommands.commands.script_braille_enter, gesture)
                    done = True
            elif gesture.dots == 0b11000000:
                if IME_state.is_native or not isinstance(gesture, keyboard_hook.DummyBrailleInputGesture) or brailleInput.handler.table.fileName.lower() != "unicode-braille.utb":
                    log.debug("BRLkeys: dot7+dot8 default")
                    scriptHandler.queueScript(globalCommands.commands.script_braille_translate, gesture)
                    done = True
            elif IME_state.is_native:
                log.debug("BRLkeys: input rejected")
                beep_typo()
                done = True
            if not done:
                log.debug("BRLkeys: dots default")
                self.clear()
                scriptHandler.queueScript(globalCommands.commands.script_braille_dots, gesture)
            if braille.handler.buffer is braille.handler.messageBuffer:
                braille.handler._dismissMessage()
            return
        except:
            log.error("BRLkeys: Unexpected error.", exc_info=True)
            self.clear()
            play_NVDA_sound("error")
            return
        log.debug('BRLkeys: Done composition "{0}"'.format(state[0]))
        if braille.handler.buffer is braille.handler.messageBuffer:
            braille.handler._dismissMessage()
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
        if braille.handler.buffer is braille.handler.messageBuffer:
            braille.handler._dismissMessage()
    # Translators: Name of a command to clear braille buffer and/or dismiss NVDA braille message.
    script_clearBRLbuffer.__doc__ = _("Clear braille buffer and/or dismiss NVDA braille message.")
    script_clearBRLbuffer.category = SCRCAT_BrlIMEHelper

    def script_copyBRLdisplayContent(self, gesture):
        if not braille.handler.enabled:
            log.error("The braille display is not enabled.")
            play_NVDA_sound("error")
            return
        brlbuf = braille.handler.buffer
        count = scriptHandler.getLastScriptRepeatCount()
        answer = None
        if 0 <= count < 2:
            answers = ["", ""]
            for r in brlbuf.regions:
                answers[1] += r.rawText
                if not isinstance(r, braille.NVDAObjectRegion):
                    answers[0] += r.rawText
            if not answers[0] and brlbuf.cursorPos is None:
                answers[0] = brlbuf.regions[-1].rawText
            answer = answers[count]
        if answer is not None:
            if answer.endswith(" ") and any((r.cursorPos, r.brailleSelectionStart, r.brailleSelectionEnd) != (None,) * 3 for r in brlbuf.visibleRegions):
                answer = answer[:-1]
            patch.copyToClip(answer)
        else: # Too many presses.
            play_NVDA_sound("error")
    # Translators: Name of a command to copy the raw text content of the braille display to the clipboard.
    script_copyBRLdisplayContent.__doc__ = _("Copy the raw text content of the braille display to the clipboard.")
    script_copyBRLdisplayContent.category = SCRCAT_BrlIMEHelper

    def script_copyBRLdisplayContentB(self, gesture, brl_format="Unicode"):
        if not braille.handler.enabled:
            log.error("The braille display is not enabled.")
            play_NVDA_sound("error")
            return
        brlbuf = braille.handler.buffer
        count = scriptHandler.getLastScriptRepeatCount()
        data, end, answer = None, -1, None
        if count == 0:
            data, end = brlbuf.windowBrailleCells, brlbuf.windowEndPos
        elif count == 1:
            data, end = brlbuf.brailleCells, len(brlbuf.brailleCells)
        if data:
            if end >= len(brlbuf.brailleCells) and data[-1] == 0 and any((r.cursorPos, r.brailleSelectionStart, r.brailleSelectionEnd) != (None,) * 3 for r in brlbuf.visibleRegions):
                data = data[:-1]
            answer, error_log = brl_tables.encode_brl_values(data, brl_format, 'Invalid brl_format value "{0}". Please report the bug.')
            if error_log:
                play_NVDA_sound("textError")
                error_log = "\n".join("At: %d, Braille: %s" % e for e in error_log)
                log.warning("Encoding failed at the following cell(s):\n" + error_log)
        if answer is not None:
            patch.copyToClip(answer)
        else: # Too many presses or other errors.
            play_NVDA_sound("error")
    # Translators: Name of a command to copy the braille patterns on the braille display to the clipboard.
    script_copyBRLdisplayContentB.__doc__ = _("Copy the braille patterns on the braille display to the clipboard.")
    script_copyBRLdisplayContentB.category = SCRCAT_BrlIMEHelper

    script_copyBRLdisplayContentB_BRF = lambda self, gesture: self.script_copyBRLdisplayContentB(gesture, "BRF")
    # Translators: Name of a command to copy the braille patterns on the braille display to the clipboard in BRF format.
    script_copyBRLdisplayContentB_BRF.__doc__ = _("Copy the braille patterns on the braille display to the clipboard in BRF format.")
    script_copyBRLdisplayContentB_BRF.category = SCRCAT_BrlIMEHelper

    script_copyBRLdisplayContentB_NABCC = lambda self, gesture: self.script_copyBRLdisplayContentB(gesture, "NABCC")
    # Translators: Name of a command to copy the braille patterns on the braille display to the clipboard in NABCC format.
    script_copyBRLdisplayContentB_NABCC.__doc__ = _("Copy the braille patterns on the braille display to the clipboard in NABCC format.")
    script_copyBRLdisplayContentB_NABCC.category = SCRCAT_BrlIMEHelper

    def script_switchIMEmode(self, gesture):
        self.send_keys(configure.get("IME_LANGUAGE_MODE_TOGGLE_KEY"))
    # Translators: Name of a command to switch between IME alphanumeric and native input conversion modes.
    script_switchIMEmode.__doc__ = _("Switch between IME alphanumeric and native input conversion modes.")
    script_switchIMEmode.category = SCRCAT_BrlIMEHelper

    def script_viewAddonState(self, gesture):
        dots_info = self.brl_state.hint_msg(self.brl_str, "")
        if gesture is None and self.kbh:
            numpad_state = "".join(str(i) for i in range(configure.NUM_BRAILLE_KEYS) if self.kbh._uncommittedDots[0] & (1 << i))
            if numpad_state:
                dots_info = "{0} #{1}".format(dots_info, numpad_state).strip()
            if self.kbh._uncommittedDots[1] is not None:
                dots_info = "{0} =>{1}".format(dots_info, self.kbh._uncommittedDots[1]).strip()
            if dots_info:
                ui.message(dots_info)
            else:
                winsound.MessageBeep()
            return
        try:
            IME_state, guessed = keyboard.infer_IME_state(), (False, False)
        except ValueError as e:
            IME_state, guessed = e.args[0], e.args[1:3]
        mode_info, name_info = keyboard_hook.input_mode_name(IME_state, None), _("unknown input method")
        if self.kbh is not None and not self.kbh.disabled():
            mode_info = keyboard_hook.input_mode_name(IME_state, self.config_r["kbbrl_ASCII_mode"])
        if IME_state.name:
            name_info = IME_state.name_str()
            if guessed[1]:
                name_info = "(?) {0}".format(name_info)
        name_info = "{0} {{{1}}}".format(name_info, IME_state.mode_flags())
        info = "; ".join([dots_info, mode_info, name_info])
        ui.message(info)
    # Translators: Name of a command to view the state of the addon.
    script_viewAddonState.__doc__ = _("View the state of BrlIMEHelper.")
    script_viewAddonState.category = SCRCAT_BrlIMEHelper

    def script_internalCodeBRL(self, gesture):
        if self.old_louis_translate is None:
            def hack_louis_translate(old_translate, tableList, inbuf, *args, **kwargs):
                try:
                    braille, brailleToRawPos, rawToBraillePos = internal_code_brl("UTF-8", inbuf)
                except:
                    log.error("Failed to translate the internal code braille: {0}".format(inbuf), exc_info=True)
                    return old_translate(tableList, inbuf, *args, **kwargs)
                brailleCursorPos = 0
                if "cursorPos" in kwargs:
                    try:
                        brailleCursorPos = rawToBraillePos[kwargs["cursorPos"]]
                    except:
                        pass
                return braille, brailleToRawPos, rawToBraillePos, brailleCursorPos
            self.old_louis_translate = louis.translate
            louis.translate = partial(hack_louis_translate, self.old_louis_translate)
        else:
            louis.translate, self.old_louis_translate = self.old_louis_translate, None
        for region in braille.handler.buffer.regions:
            region.update()
        braille.handler.buffer.update()
        braille.handler.update()
        try: tether = braille.handler.getTether()
        except: tether = braille.handler.tether
        if tether == braille.handler.TETHER_FOCUS:
            try: braille.handler.handleGainFocus(api.getFocusObject(), shouldAutoTether=False)
            except: braille.handler.handleGainFocus(api.getFocusObject())
        else:
            try: braille.handler.handleReviewMove(shouldAutoTether=False)
            except: braille.handler.handleReviewMove()
    # Translators: Name of a command to switch the display of the internal code in braille.
    script_internalCodeBRL.__doc__ = _("Turn on/off the display of the internal code in braille.")
    script_internalCodeBRL.category = SCRCAT_BrlIMEHelper

    def script_openControlPanel(self, gesture): # os.system("control") is inefficient.
        l = windll.Kernel32.GetSystemDirectoryA(None, 0)
        b = create_string_buffer(l)
        windll.Kernel32.GetSystemDirectoryA(b, len(b))
        windll.Kernel32.WinExec(os.path.join(b.value, b"control.exe"), 1) # SW_NORMAL
    # Translators: Name of a command to open the control panel.
    script_openControlPanel.__doc__ = _("Open the control panel.")
    script_openControlPanel.category = SCRCAT_BrlIMEHelper

    def script_showMessageIndefinitely(self, gesture):
        if braille.handler._messageCallLater:
            braille.handler._messageCallLater.Stop()
            braille.handler._messageCallLater = None
    # Translators: Name of a command to force NVDA to show the current braille message indefinitely.
    script_showMessageIndefinitely.__doc__ = _("Force NVDA to show the current braille message indefinitely.")
    script_showMessageIndefinitely.category = SCRCAT_BrlIMEHelper

    def script_translateClip(self, gesture, brl_format="Unicode"):
        try:
            text = api.getClipData()
        except:
            # Translators: Reported when reading the clipboard has failed.
            ui.message(_("Failed to read the clipboard."))
            return
        brl_lines, error_logs = [], []
        for line in re.split(r"\r*\n|\r", text):
            region = braille.TextRegion(line)
            region.update()
            answer, error_log = brl_tables.encode_brl_values(region.brailleCells, brl_format, 'Invalid brl_format value "{0}". Please report the bug.')
            if answer is not None:
                brl_lines.append(answer)
            if error_log: # The condition is to prevent blank lines.
                error_logs.append("\n".join("Line: %d, At: %d, Braille: %s" % ((len(brl_lines),) + e) for e in error_log))
        answer = os.linesep.join(brl_lines)
        if error_logs:
            play_NVDA_sound("textError")
            log.warning("Encoding failed at the following cell(s):\n" + "\n".join(error_logs))
        if patch.cmpNVDAver(2020, 4) < 0: # api.copyToClip of earlier NVDA versions reports no message.
            if api.copyToClip(answer):
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            else:
                play_NVDA_sound("error")
        else:
            api.copyToClip(answer, notify=True)
    # Translators: Name of a command to translate the clipboard content into Unicode braille patterns.
    script_translateClip.__doc__ = _("Translate the clipboard content into Unicode braille patterns.")
    script_translateClip.category = SCRCAT_BrlIMEHelper

    script_translateClip_BRF = lambda self, gesture: self.script_translateClip(gesture, "BRF")
    # Translators: Name of a command to translate the clipboard content into braille in BRF format.
    script_translateClip_BRF.__doc__ = _("Translate the clipboard content into braille in BRF format.")
    script_translateClip_BRF.category = SCRCAT_BrlIMEHelper

    script_translateClip_NABCC = lambda self, gesture: self.script_translateClip(gesture, "NABCC")
    # Translators: Name of a command to translate the clipboard content into braille in NABCC format.
    script_translateClip_NABCC.__doc__ = _("Translate the clipboard content into braille in NABCC format.")
    script_translateClip_NABCC.category = SCRCAT_BrlIMEHelper

    __gestures = {
        "kb:NVDA+control+6": "toggleBRLsimulation",
        "kb:NVDA+printscreen": "copyBRLdisplayContent",
        "kb:NVDA+windows+printscreen": "copyBRLdisplayContentB",
        "kb:NVDA+windows+a": "viewAddonState",
        "kb:NVDA+windows+u": "internalCodeBRL",
        "bk:dots": "BRLdots",
        "bk:space+dot2+dot4+dot5": "clearBRLbuffer",
        "bk:space+dot1+dot2+dot3": "switchMainKBInputManner",
        "bk:space+dot4+dot5+dot6": "switchIMEmode",
        "bk:space+dot1+dot3+dot6": "toggleUnicodeBRL",
    }

    default_bk_gestures = dict(
        _make_bk_gesture_set(1, None, key="a") +
        _make_bk_gesture_set(12, None, key="b") +
        _make_bk_gesture_set(14, "kb:control", key="c") +
        _make_bk_gesture_set(145, None, key="d") +
        _make_bk_gesture_set(15, None, key="e") +
        _make_bk_gesture_set(124, None, key="f") +
        _make_bk_gesture_set(1245, None, var3=None, key="g") +
        _make_bk_gesture_set(125, None, key="h") +
        _make_bk_gesture_set(24, None, key="i") +
        _make_bk_gesture_set(245, None, key="j") +
        _make_bk_gesture_set(13, None, key="k") +
        _make_bk_gesture_set(123, None, key="l") +
        _make_bk_gesture_set(134, "kb:alt", key="m") +
        _make_bk_gesture_set(1345, "showGui", var3=None, key="n") +
        _make_bk_gesture_set(135, None, key="o") +
        _make_bk_gesture_set(1234, None, var3=None, key="p") +
        _make_bk_gesture_set(1235, None, var3=None, key="r") +
        _make_bk_gesture_set(234, "kb:shift", key="s") +
        _make_bk_gesture_set(2345, None, var3=None, key="t") +
        _make_bk_gesture_set(136, None, key="u") +
        _make_bk_gesture_set(1236, None, var3=None, key="v") +
        _make_bk_gesture_set(2456, "kb:windows", var3=None, key="w") +
        _make_bk_gesture_set(1346, "kb:alt+f4", var3=None, key="x") +
        _make_bk_gesture_set(1356, None, var3=None, key="z") +
        _make_bk_gesture_set(246, "kb:pageUp", var3=None) +
        _make_bk_gesture_set(1256, "kb:pageDown", var3=None) +
        _make_bk_gesture_set(12456, "sayAll") +
        _make_bk_gesture_set(45, "kb:home", var3=None) +
        _make_bk_gesture_set(0, None, "kb:windows+space", "kb:alt+space", "kb:windows+shift+space") +
        _make_bk_gesture_set(2346, "kb:escape", var3=None) +
        _make_bk_gesture_set(5, "leftMouseClick", "kb:f11", "moveMouseToNavigatorObject", None) +
        _make_bk_gesture_set(3456, "kb:delete", var3=None) +
        _make_bk_gesture_set(1246, "kb:end", var3=None) +
        _make_bk_gesture_set(146, "kb:downArrow") +
        _make_bk_gesture_set(12346, "kb:applications", None, None, None) +
        _make_bk_gesture_set(3, None, None, "navigatorObject_currentDimensions", "kb:windows+tab") +
        _make_bk_gesture_set(12356, "kb:NVDA+f9", None, None, None) +
        _make_bk_gesture_set(23456, "kb:NVDA+f10", None, None, None) +
        _make_bk_gesture_set(16, "kb:shift+tab", var3=None) +
        _make_bk_gesture_set(346, "kb:upArrow") +
        _make_bk_gesture_set(6, "rightMouseClick", None, "moveNavigatorObjectToMouse", "kb:windows+t") +
        _make_bk_gesture_set(36, None, None, "navigatorObject_toFocus", "GlobalPlugin.openControlPanel") +
        _make_bk_gesture_set(34, "kb:tab", var3=None) +
        _make_bk_gesture_set(356, None, "kb:f10", "review_activate", None) +
        _make_bk_gesture_set(2, "review_previousCharacter", "kb:f1", "reviewMode_previous", "kb:windows+a") +
        _make_bk_gesture_set(23, "review_currentCharacter", "kb:f2", "navigatorObject_firstChild", "kb:windows+b") +
        _make_bk_gesture_set(25, "review_nextCharacter", "kb:f3", None, "kb:windows+x") +
        _make_bk_gesture_set(256, "review_previousWord", "kb:f4", "navigatorObject_previous", "kb:windows+d") +
        _make_bk_gesture_set(26, "review_currentWord", "kb:f5", "navigatorObject_current", None) +
        _make_bk_gesture_set(235, "review_nextWord", "kb:f6", "navigatorObject_next", None) +
        _make_bk_gesture_set(2356, "review_previousLine", "kb:f7", "reviewMode_next", None) +
        _make_bk_gesture_set(236, "review_currentLine", "kb:f8", "navigatorObject_parent", None) +
        _make_bk_gesture_set(35, "review_nextLine", "kb:f9", None, "kb:windows+i") +
        _make_bk_gesture_set(56, "review_sayAll", "kb:f12", None, None) +
        _make_bk_gesture_set(126, "kb:leftArrow") +
        _make_bk_gesture_set(345, "kb:rightArrow") +
        []
    )
