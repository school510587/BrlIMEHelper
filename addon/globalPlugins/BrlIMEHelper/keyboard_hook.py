# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2024 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from collections import OrderedDict
from ctypes import *
from functools import partial
import re
import string
import wx

try: unichr
except NameError: unichr = chr

from brailleDisplayDrivers.noBraille import BrailleDisplayDriver as NoBrailleDisplayDriver
from keyboardHandler import KeyboardInputGesture, getInputHkl, isNVDAModifierKey, currentModifiers
from logHandler import log
from winUser import *
import addonHandler
import braille
import brailleInput
import globalCommands
import inputCore
import queueHandler
import winInputHook

try:
    addonHandler.initTranslation()
except:
    log.warning("Exception occurred when loading translation.", exc_info=True)

from .runtime_state import *
from .sounds import *
from . import configure
from . import keyboard
from . import patch

class DummyBrailleInputGesture(braille.BrailleDisplayGesture, brailleInput.BrailleInputGesture):
    source = NoBrailleDisplayDriver.name
    @classmethod
    def update_brl_display_gesture_map(cls, GlobalPlugin, display=braille.handler.display):
        if not isinstance(display.gestureMap, inputCore.GlobalGestureMap):
            display.gestureMap = inputCore.GlobalGestureMap()
        source = "bk:" if patch.cmpNVDAver(2018, 3) < 0 else "br({0}):".format(cls.source)
        for g, f in GlobalPlugin.default_bk_gestures.items():
            display.gestureMap.add(source + g, *f)
    def _get_id(self):
        try:
            dots_id = self._makeDotsId()
            log.debug("_makeDotsId returns " + dots_id)
            sep = dots_id.find(":")
            return dots_id[sep+1:]
        except:
            log.error("Maybe _makeDotsId does not work.")
        return ""
    def _get_identifiers(self):
        ids = super(DummyBrailleInputGesture, self)._get_identifiers()
        if isinstance(braille.handler.display, NoBrailleDisplayDriver):
            return ids
        answer = []
        for id in ids:
            if id.startswith("bk:"):
                answer.append(id)
                continue
            physical_id = id.replace(self.source, braille.handler.display.name, 1)
            if physical_id.startswith("br(freedomScientific):"): # Exception specific to this driver.
                physical_id = re.sub(r"(.*)space", r"\1brailleSpaceBar", physical_id)
            if patch.cmpNVDAver(2018, 3) < 0:
                id = "bk:" + id[id.find(":")+1:]
            if configure.get("REL_PHYSICAL_DUMMY_BRLKB") == "consistent":
                answer.append(physical_id)
            elif configure.get("REL_PHYSICAL_DUMMY_BRLKB") == "former-precedence":
                answer.append(physical_id)
                answer.append(id)
            elif configure.get("REL_PHYSICAL_DUMMY_BRLKB") == "latter-precedence":
                answer.append(id)
                answer.append(physical_id)
            elif configure.get("REL_PHYSICAL_DUMMY_BRLKB") == "independent":
                answer.append(id)
            else:
                log.error("Invalid REL_PHYSICAL_DUMMY_BRLKB value.", exc_info=True)
        if patch.cmpNVDAver(2018, 3) < 0:
            answer, old_answer, id_set = [], answer, set()
            for id in old_answer:
                n_id = inputCore.normalizeGestureIdentifier(id)
                if n_id not in id_set:
                    id_set.add(n_id)
                    answer.append(id)
        return answer

def input_mode_name(IME_state, config_item):
    try: # The computer keyboard is enabled to generate the braille input.
        input_channel = int(config_item[IME_state.is_native]) # Either 0 or 1.
    except: # Only the physical braille keyboard may be working.
        input_channel = -1
    return (
        # Translators: The input mode, NVDA braille input handler with the 9-key input manner.
        _("9-key NVDA Braille Input"),
        # Translators: The input mode, BrlIMEHelper input handler with the 9-key input manner.
        _("9-key Braille IME"),
        # Translators: The input mode, NVDA braille input handler with the full-keyboard input manner.
        _("Full-keyboard NVDA Braille Input"),
        # Translators: The input mode, BrlIMEHelper input handler with the full-keyboard input manner.
        _("Full-keyboard Braille IME"),
        # Translators: The input mode, NVDA braille input handler without braille keyboard emulation.
        _("NVDA Braille Input"),
        # Translators: The input mode, BrlIMEHelper input handler without braille keyboard emulation.
        _("Braille IME"),
    )[2 * input_channel + IME_state.is_native]

def send_str_as_brl(text):
    region = braille.TextRegion(text)
    region.update()
    for cell in region.brailleCells:
        gesture = DummyBrailleInputGesture()
        gesture.dots = cell
        gesture.space = not cell
        log.debug("Emulate: {0}".format(gesture.displayName))
        inputCore.manager.emulateGesture(gesture)

class KeyboardHook(object):

    # ACC_KEYS is the universe of all processed characters. BRL_KEYS and
    # SEL_KEYS must be its subsets. Note that they are currently replaced
    # by BRAILLE_KEYS and IGNORED_KEYS options, respectively. If the same
    # key is present in both options, the former takes precedence.
    ACC_KEYS = set(string.ascii_letters + string.digits + string.punctuation + " ")

    def __init__(self, addon):
        self.addon = addon
        self.config_r = addon.config_r
        self._current_modifiers = set()
        self._ignored_keys = None
        self._kbq = []
        self._passed_keys = {}
        self._pending_keys = OrderedDict()
        self._trapped_keys = set()
        self._trapped_modifiers = {}
        self._gesture = None
        self._uncommittedDots = [0, None]
        def hack_kb_send(addon, *args):
            addon._ignored_keys = set()
            log.debug("A key-pass session begins.")
            return addon.real_kb_send(*args)
        self.real_kb_send = KeyboardInputGesture.send
        KeyboardInputGesture.send = patch.monkey_method(partial(hack_kb_send, self), KeyboardInputGesture)
        self._oldKeyDown = winInputHook.keyDownCallback
        winInputHook.keyDownCallback = self.on_key_down
        self._oldKeyUp = winInputHook.keyUpCallback
        winInputHook.keyUpCallback = self.on_key_up

    def terminate(self): # NVDA does not call __del__() automatically.
        winInputHook.keyDownCallback = self._oldKeyDown
        winInputHook.keyUpCallback = self._oldKeyUp
        KeyboardInputGesture.send = self.real_kb_send
        self.real_kb_send = None
        log.debug("Unhooked the keyboard.")

    def clear_pending_keys(self, passed_key=()):
        log.debug("Clearing pending keys for passed_key={0}.".format(passed_key))
        if passed_key:
            self._passed_keys[passed_key] = True
        still_pending_keys = set(k for k in self._pending_keys if k[1] == "")
        action = bool(still_pending_keys)
        self._trapped_keys |= still_pending_keys
        self._pending_keys.clear()
        b = self.reset_numpad_state()
        action = action or b or self._uncommittedDots[0] or self._uncommittedDots[1] is not None or self._gesture
        self._uncommittedDots = [0, None]
        self._gesture = None
        if action:
            beep_typo()

    def disabled(self):
        return on_browse_mode() or self.config_r["kbbrl_deactivated"]

    def reset_numpad_state(self, reset_to=[0, None], timeout=None):
        original_state = False
        try: original_state = bool(self._uncommittedDots)
        except AttributeError: pass
        try:
            if self._numpad_timer: # Perhaps AttributeError.
                self._uncommittedDots = list(reset_to) # copy
            self._numpad_timer.Stop()
        except:
            pass
        self._numpad_timer = None
        if timeout:
            self._numpad_timer = wx.CallLater(timeout, self.reset_numpad_state)
        return original_state and not bool(self._uncommittedDots)

    def on_key_down(self, vkCode, scanCode, extended, injected):
        log.debug("key-down: {0}".format(keyboard.vkdbgmsg(vkCode, extended, injected)))
        if self._ignored_keys is not None:
            log.debug("In a key-pass session.")
            self.clear_pending_keys()
            self._ignored_keys.add((vkCode, scanCode, extended))
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        if (vkCode, scanCode, extended) in self._passed_keys:
            log.debug("Pass the ignored key set by the add-on.")
            self.clear_pending_keys(passed_key=(vkCode, scanCode, extended))
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        if vkCode in (0xF0, 0xF2):
            log.debug("Pass the OEM specific key unconditionally to support Shift + CapsLock.")
            self.clear_pending_keys(passed_key=(vkCode, scanCode, extended))
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        if (vkCode, scanCode, extended) in self._trapped_keys:
            log.debug("The key has been trapped.")
            return False
        if self.disabled():
            log.debug("When NVDA is in the browse mode, or the focus is on some special control of the settings panel, the keyboard hooks are disabled.")
            self.clear_pending_keys(passed_key=(vkCode, scanCode, extended))
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        try:
            IME_state = keyboard.infer_IME_state()
        except ValueError as e:
            IME_state = e.args[0]
        # Note: 2017.3 doesn't support getNVDAModifierKeys.
        if isNVDAModifierKey(vkCode, extended) or vkCode in KeyboardInputGesture.NORMAL_MODIFIER_KEYS:
            log.debug("It is a modifier key.")
            result = self._passed_keys
            if self.config_r["kbbrl_ASCII_mode"][IME_state.is_native]:
                log.debug("In the full keyboard input mode...")
                if vkCode in {VK_SHIFT, VK_LSHIFT, VK_RSHIFT}:
                    log.debug("A Shift is pressed.")
                    if currentModifiers or self._current_modifiers:
                        log.debug("Pass the modifier key.")
                    else:
                        result = self._trapped_keys
                        log.debug("Trap the modifier key. Completed the key-down callback.")
                else:
                    log.debug("Not Shift.")
                    if self._trapped_modifiers:
                        result = self._trapped_keys
                        log.debug("Trap the modifier key with Shift. Completed the key-down callback.")
                    else:
                        log.debug("Pass the modifier key.")
            else:
                log.debug("Pass the modifier key anyway in the braille input mode.")
            if result is self._passed_keys:
                self.clear_pending_keys(passed_key=(vkCode, scanCode, extended))
                self._current_modifiers.add((vkCode, extended))
                return self._oldKeyDown(vkCode, scanCode, extended, injected)
            result.add((vkCode, scanCode, extended))
            self._trapped_modifiers[(vkCode, extended)] = len(self._kbq)
            return False
        charCode = user32.MapVirtualKeyExW(vkCode, MAPVK_VK_TO_CHAR, getInputHkl())
        log.debug("MapVirtualKeyExW() returns 0x%08X (%d_10)." % (charCode, charCode))
        if HIWORD(charCode) != 0:
            log.debug("Invalid character code with nonzero high word.")
            self.clear_pending_keys(passed_key=(vkCode, scanCode, extended))
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        ch = unichr(LOWORD(charCode))
        log.debug("LOWORD({0}) => {1}".format(charCode, repr(ch)))
        if self._trapped_modifiers:
            log.debug("The key is modified by some trapped modifier.")
            gesture = None
            if ch != ' ' and ch in self.ACC_KEYS and set(k[0] for k in self._trapped_modifiers).issubset({VK_SHIFT, VK_LSHIFT, VK_RSHIFT}):
                kst = [getKeyState(i) for i in range(256)]
                for k in self._trapped_modifiers:
                    kst[k[0]] = 0x80
                kst[VK_SHIFT] |= kst[VK_LSHIFT] | kst[VK_RSHIFT]
                kst[VK_CONTROL] |= kst[VK_LCONTROL] | kst[VK_RCONTROL]
                kst[VK_MENU] |= kst[VK_LMENU] | kst[VK_RMENU]
                uch = keyboard.vk2str(vkCode, scanCode, kst)
                if uch:
                    region = braille.TextRegion(uch.swapcase() if kst[VK_CAPITAL] else uch)
                    region.update()
                    for cell in region.brailleCells:
                        gesture = DummyBrailleInputGesture()
                        gesture.dots = cell
                        gesture.space = not cell
                        self._kbq.append(gesture)
            if gesture is None: # No gesture was inserted.
                self._kbq.append(KeyboardInputGesture(currentModifiers | self._current_modifiers | set(self._trapped_modifiers), vkCode, scanCode, extended))
            self._trapped_keys.add((vkCode, scanCode, extended))
            log.debug("It is queued until there is no trapped modifier.")
            return False
        elif currentModifiers or self._current_modifiers:
            log.debug("Pass the key, because it is modified by some passed modifier.")
            self.clear_pending_keys(passed_key=(vkCode, scanCode, extended))
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        if vkCode & 0xF0 == 0x60:
            log.debug("Handling the numpad key...")
            key_id = vkCode & 0x0F
            try:
                if currentModifiers or self._current_modifiers or self._trapped_modifiers or not configure.get("ALLOW_DOT_BY_DOT_BRL_INPUT_VIA_NUMPAD"):
                    raise NotImplementedError("It is modified, or the dot-by-dot braille input feature is not enabled.")
                elif 0x00 <= key_id <= 0x08: # VK_NUMPAD0 to VK_NUMPAD8
                    self.reset_numpad_state()
                    self._uncommittedDots[0] |= (1 << key_id)
                    try:
                        self._uncommittedDots[1] = self._uncommittedDots[1] * 10 + key_id
                    except:
                        self._uncommittedDots[1] = key_id
                    if configure.get("REPORT_BRL_BUFFER_CHANGES"):
                        patch.spellWithHighestPriority(str(key_id))
                elif key_id == 0x09: # VK_NUMPAD9 = 0x69
                    self.reset_numpad_state()
                    self._uncommittedDots[0] = 0
                    try:
                        self._uncommittedDots[1] = self._uncommittedDots[1] * 10 + key_id
                    except:
                        self._uncommittedDots[1] = key_id
                    if configure.get("REPORT_BRL_BUFFER_CHANGES"):
                        patch.spellWithHighestPriority(str(key_id))
                elif key_id == 0x0A: # VK_MULTIPLY = 0x6A
                    if self._uncommittedDots[1] is None:
                        raise NotImplementedError # No uncommitted routing command.
                    self._uncommittedDots[0] = 0
                    self._gesture = braille.BrailleDisplayGesture()
                    self._gesture.routingIndex = self._uncommittedDots[1]
                    queueHandler.queueFunction(queueHandler.eventQueue, self.reset_numpad_state, reset_to=[0, self._gesture.routingIndex], timeout=500)
                    queueHandler.queueFunction(queueHandler.eventQueue, globalCommands.commands.script_braille_routeTo, self._gesture)
                    self._gesture = None
                elif key_id == 0x0B: # VK_ADD = 0x6B
                    queueHandler.queueFunction(queueHandler.eventQueue, globalCommands.commands.script_braille_scrollForward, None)
                elif key_id == 0x0D: # VK_SUBTRACT = 0x6D
                    queueHandler.queueFunction(queueHandler.eventQueue, globalCommands.commands.script_braille_scrollBack, None)
                elif key_id == 0x0E: # VK_DECIMAL = 0x6E
                    if not self._uncommittedDots[0]:
                        raise NotImplementedError("No uncommitted dots.")
                    self._uncommittedDots[1] = None
                    self._gesture = DummyBrailleInputGesture()
                    self._gesture.space = bool(self._uncommittedDots[0] & 0x01)
                    self._gesture.dots = self._uncommittedDots[0] >> 1
                    queueHandler.queueFunction(queueHandler.eventQueue, self.reset_numpad_state, reset_to=[(self._gesture.dots << 1) | self._gesture.space, None], timeout=500)
                elif key_id == 0x0F: # VK_DIVIDE = 0x6F
                    queueHandler.queueFunction(queueHandler.eventQueue, self.addon.script_viewAddonState, None)
                else:
                    raise NotImplementedError("Unused numpad keys.")
            except NotImplementedError:
                log.debug("Pass the undefined numpad key.")
                self.clear_pending_keys(passed_key=(vkCode, scanCode, extended))
                return self._oldKeyDown(vkCode, scanCode, extended, injected)
            self._trapped_keys.add((vkCode, scanCode, extended))
            log.debug("The numpad key is processed. Completed the key-down callback.")
            return False
        if (vkCode, scanCode, extended) not in self._pending_keys:
            log.debug("The key is new, i.e. not pending.")
            dot = 0
            try:
                i = configure.get("BRAILLE_KEYS").index(ch)
                log.debug("Braille key [%d]." % (i,))
                dot = 1 << i
            except:
                log.debug("The key is not a braille key, ...")
                if ch not in self.ACC_KEYS:
                    log.debug("and pass rather than pend the not accepted key.")
                    self.clear_pending_keys(passed_key=(vkCode, scanCode, extended))
                    return self._oldKeyDown(vkCode, scanCode, extended, injected)
                log.debug("but it is accepted and pending.")
            else:
                log.debug("The key is a braille key, ...")
                if self._gesture is None and not self._pending_keys and not self._trapped_keys:
                    log.debug("The first ordinary main keyboard key is pressed.")
                    self._gesture = DummyBrailleInputGesture()
                if self._gesture is not None:
                    log.debug("dots|space = {0:09b}".format(dot))
                    if dot == 1:
                        self._gesture.space = True
                    self._gesture.dots |= dot >> 1
                else:
                    log.debug("However, the braille input has been interrupted. [%d pending key(s), %d trapped key(s)]" % (len(self._pending_keys), len(self._trapped_keys)))
                    log.debug("{0}".format([k for k in self._trapped_keys]))
        else:
            log.debug("The key has been pending.")
        log.debug("Record it as a pending key.")
        self._pending_keys[(vkCode, scanCode, extended)] = [ch, ""]
        log.debug("Completed the key-down callback.")
        return False

    def send_queued_gestures(self, gq):
        log.debug("Sending the queued gestures...")
        for g in gq:
            try:
                log.debug("Emulate: {0}".format(g.displayName))
                inputCore.manager.emulateGesture(g)
            except inputCore.NoInputGestureAction:
                pass
        log.debug("Done.")

    def on_key_up(self, vkCode, scanCode, extended, injected):
        log.debug("key-up: {0}".format(keyboard.vkdbgmsg(vkCode, extended, injected)))
        if self._ignored_keys is not None and (vkCode, scanCode, extended) in self._ignored_keys:
            self._ignored_keys.remove((vkCode, scanCode, extended))
            if not self._ignored_keys:
                log.debug("A key-pass session ends.")
                self._ignored_keys = None
            return self._oldKeyUp(vkCode, scanCode, extended, injected)
        try:
            if self._passed_keys[(vkCode, scanCode, extended)]:
                log.debug("Pass the key.")
                del self._passed_keys[(vkCode, scanCode, extended)]
                self._current_modifiers.discard((vkCode, extended))
                return self._oldKeyUp(vkCode, scanCode, extended, injected)
            log.debug("It should be passed to the system, but not now.")
        except:
            log.debug("It is not passed to the system.")
        try:
            self._trapped_keys.remove((vkCode, scanCode, extended))
            log.debug("It is trapped.")
            if self._trapped_modifiers.pop((vkCode, extended), None) is len(self._kbq):
                log.debug("The modifier key (combination) is pressed without non-modifier key.")
                self._kbq.append(KeyboardInputGesture(currentModifiers | self._current_modifiers | set(self._trapped_modifiers), vkCode, scanCode, extended))
            if not self._trapped_keys and self._gesture is not None:
                log.debug("The result of the dot-by-dot input.")
                self._kbq.append(self._gesture)
                self._gesture = None
            if not self._trapped_modifiers and self._kbq:
                log.debug("Send all of the queued %d gesture(s)." % (len(self._kbq),))
                queueHandler.queueFunction(queueHandler.eventQueue, self.send_queued_gestures, list(self._kbq))
                del self._kbq[:] # Python 2 does not have list.clear().
            return False
        except KeyError:
            log.debug("It is not trapped.")
        if (vkCode, scanCode, extended) not in self._pending_keys:
            log.debug("Pass the unrecognized key.")
            return self._oldKeyUp(vkCode, scanCode, extended, injected)
        elif self._pending_keys[(vkCode, scanCode, extended)][1] != "":
            log.error("The 2nd field of a pending key must be ''. Debug is required.")
        log.debug("Process of the pending key continues below.")
        try:
            IME_state = keyboard.infer_IME_state()
        except ValueError as e:
            IME_state = e.args[0]
        if self.config_r["kbbrl_ASCII_mode"][IME_state.is_native]:
            log.debug("In the full keyboard input mode...")
            self._pending_keys[(vkCode, scanCode, extended)][1] = keyboard.vk2str(vkCode, scanCode, [0] * 256)
            if not self._pending_keys[(vkCode, scanCode, extended)][1]:
                log.error("keyboard.vk2str() returns ''. Debug is required.")
                self._pending_keys[(vkCode, scanCode, extended)][1] = self._pending_keys[(vkCode, scanCode, extended)][0]
        else:
            log.debug("In the braille input mode...")
            self._pending_keys[(vkCode, scanCode, extended)][1] = self._pending_keys[(vkCode, scanCode, extended)][0]
        if "" not in set(v[1] for v in self._pending_keys.values()):
            log.debug("A braille input session ends, i.e. all pending keys are released.")
            if self.config_r["kbbrl_ASCII_mode"][IME_state.is_native] and not(self._gesture and self._gesture.dots and self._gesture.space):
                log.debug("In the full keyboard input mode, the touched keys do not compose a braille command.")
                touched_chars = "".join(v[1] for v in self._pending_keys.values())
                log.debug("Sending {0}".format(touched_chars))
                queueHandler.queueFunction(queueHandler.eventQueue, send_str_as_brl, touched_chars)
            else:
                log.debug("In the braille input mode, or a braille command is sent in the full keyboard input mode.")
                touched_chars = dict((v[0], k) for k, v in self._pending_keys.items())
                k_brl, k_ign = set(configure.get("BRAILLE_KEYS")) & set(touched_chars), set(touched_chars)
                if IME_state.is_native or not configure.get("FREE_ALL_NON_BRL_KEYS_IN_ALPHANUMERIC_MODE"):
                    log.debug("Not all non-braille keys are free.")
                    k_ign = set(configure.get("IGNORED_KEYS")) & k_ign
                if k_brl == set(touched_chars) and self._gesture:
                    log.debug("Emulate: {0}".format(self._gesture.displayName))
                    inputCore.manager.emulateGesture(self._gesture)
                elif len(k_ign) == 1 and k_ign == set(touched_chars):
                    log.debug("Exactly one ignored key has been touched.")
                    (ch,) = k_ign
                    inputCore.manager.emulateGesture(KeyboardInputGesture([], *touched_chars[ch]))
                else:
                    log.debug("Multiple ignored keys have been touched.")
                    beep_typo()
            log.debug("Clean up...")
            self._pending_keys.clear()
            self._gesture = None
            self._uncommittedDots = [0, None]
        return False
