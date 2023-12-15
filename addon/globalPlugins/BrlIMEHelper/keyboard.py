# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2023 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import print_function
from __future__ import unicode_literals
from collections import OrderedDict
from collections import namedtuple
from comtypes import COMError
from comtypes import CLSCTX_ALL
from comtypes import GUID
from comtypes.GUID import GUID_null
from comtypes.client import CreateObject
from comtypes.hresult import E_NOINTERFACE
from copy import deepcopy
from ctypes import *
from ctypes.wintypes import *
from json import JSONDecoder
import codecs
import difflib
import itertools
import os
import re
import sys
try:
    import winreg
except:
    import _winreg as winreg

from NVDAObjects.inputComposition import InputComposition
from keyboardHandler import getInputHkl
from logHandler import log
from winUser import *
import addonHandler
import vkCodes

from . import configure
from . import patch
from .msctf import *
from .runtime_state import thread_states

try:
    addonHandler.initTranslation()
except:
    log.warning("Exception occurred when loading translation.", exc_info=True)

try: # On NVDA.
    from winVersion import winVersion
except: # NVDA-independent execution.
    import sys
    winVersion = sys.getwindowsversion()

try:
    eval("_('')")
except NameError: # NVDA-independent execution.
    import gettext
    gettext.install("") # Install _() into builtins namespace.

# The default keyboard profiles of all languages (LANGID -> (CLSID, GUID)).
DEFAULT_PROFILE = {}

# The profile ID of the Microsoft Bopomofo IME.
MICROSOFT_BOPOMOFO = {
    "language": 0x0404, # MAKELANGID(LANG_CHINESE, SUBLANG_CHINESE_TRADITIONAL), not LANG_CHINESE_TRADITIONAL.
    "profile": GUID("{B2F9C502-1742-11D4-9790-0080C882687E}"),
    "processor": GUID_null,
    "keyboard-layout": 0,
    "description": "",
}

# Display names of keyboard mappings.
mapping = configure.profile["KEYBOARD_MAPPING"].allowed_values

kl2name = {}
lookup_IME = {}
_name2clsid = OrderedDict()
def symbol2gesture(index):
    try:
        IME_data = lookup_IME[thread_states.foreground["layout"]]
    except KeyError:
        try:
            pid, tid = getWindowThreadProcessID(getForegroundWindow())
            kl = getKeyboardLayout(tid)
            IME_data = lookup_IME[kl2name[DWORD(kl).value]]
        except: # Use the default bopomofo IME.
            IME_data = lookup_IME[MICROSOFT_BOPOMOFO["description"]]
    try:
        return IME_data[index]
    except KeyError:
        if len(index) != 1:
            raise
        elif ord(index) >= 0x10000 and not bool(IME_data["ALLOW_NON_BMP_SYMBOLS"]):
            raise
        return "|".join(IME_data["UNDEFINED_SYMBOL"] % (ord(index),))

with codecs.open(os.path.join(os.path.dirname(__file__), "{0}.json".format(MICROSOFT_BOPOMOFO["profile"])), encoding="UTF-8") as json_file:
    IME_json = json_file.read()
    IME_data = dict((GUID(g), d) for g, d in JSONDecoder(object_pairs_hook=OrderedDict).decode(IME_json).items())
    default_dict = IME_data[GUID_null]
    try:
        oIPP = CreateObject(CLSID_TF_InputProcessorProfiles, CLSCTX_ALL, interface=ITfInputProcessorProfiles)
        gtr = oIPP.EnumLanguageProfiles(MICROSOFT_BOPOMOFO["language"])
        while 1:
            profile = gtr.Next()
            if profile is None:
                break
            log.debug("IME: clsid={0.clsid}, langid={0.langid}, guidProfile={0.guidProfile}".format(profile))
            if profile.guidProfile != MICROSOFT_BOPOMOFO["profile"]:
                log.debug("Skipped.")
                continue
            IME_name = oIPP.GetLanguageProfileDescription(profile.clsid, profile.langid, profile.guidProfile)
            log.debug("IME name: {0}".format(IME_name))
            lookup_IME[IME_name] = deepcopy(default_dict)
            _name2clsid[IME_name] = profile.clsid
            if profile.clsid not in IME_data:
                continue
            for k, v in IME_data[profile.clsid].items():
                if k in lookup_IME[IME_name]:
                    if v is None:
                        del lookup_IME[IME_name][k]
                    else:
                        try:
                            lookup_IME[IME_name][k].update(v)
                        except:
                            lookup_IME[IME_name][k] = v
                elif v is not None:
                    lookup_IME[IME_name][k] = v
            if not oIPP.IsEnabledLanguageProfile(profile.clsid, MICROSOFT_BOPOMOFO["language"], MICROSOFT_BOPOMOFO["profile"]):
                log.warning("Microsoft Bopomofo IME is not enabled now.")
    except COMError:
        log.error("Some COM error occurred.", exc_info=True)
for n, cls in _name2clsid.items():
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\CTF\TIP\{clsid}\LanguageProfile\0x0000{langid:04X}\{guidProfile}".format(clsid=cls, langid=MICROSOFT_BOPOMOFO["language"], guidProfile=MICROSOFT_BOPOMOFO["profile"])) as IME_i:
            hKLstr, _type = winreg.QueryValueEx(IME_i, "SubstituteLayout")
            if _type == winreg.REG_SZ:
                kl = int(hKLstr, 16)
                kl2name[kl] = n
    except WindowsError as w: # The newer Python raises FileNotFoundError, i.e. w.winerror == 2.
        if w.winerror not in (2, 259): raise
for l in oIPP.GetLanguageList():
    DEFAULT_PROFILE[l] = oIPP.GetDefaultLanguageProfile(l, GUID_TFCAT_TIP_KEYBOARD)
MICROSOFT_BOPOMOFO["processor"], profile = DEFAULT_PROFILE[MICROSOFT_BOPOMOFO["language"]]
if profile == MICROSOFT_BOPOMOFO["profile"]:
    try:
        MICROSOFT_BOPOMOFO["description"] = next(name for name, cls in _name2clsid.items() if cls == MICROSOFT_BOPOMOFO["processor"])
    except:
        log.warning("Exception occurred on searching the default bopomofo IME.", exc_info=True)
        profile = GUID_null # The value will pass the following condition.
if profile != MICROSOFT_BOPOMOFO["profile"]: # The default bopomofo IME is not supported.
    try: # Select a (new version) supported bopomofo IME as the default.
        MICROSOFT_BOPOMOFO["description"], MICROSOFT_BOPOMOFO["processor"] = next((name, cls) for name, cls in _name2clsid.items() if name not in kl2name.values())
    except StopIteration: # Each bopomofo IME has a corresponding keyboard layout.
        try:
            MICROSOFT_BOPOMOFO["keyboard-layout"] = max(kl2name.keys())
            MICROSOFT_BOPOMOFO["description"] = kl2name[MICROSOFT_BOPOMOFO["keyboard-layout"]]
            MICROSOFT_BOPOMOFO["processor"] = _name2clsid[MICROSOFT_BOPOMOFO["description"]]
        except:
            log.warning("Exception occurred on searching the default bopomofo IME by KL.", exc_info=True)
if not MICROSOFT_BOPOMOFO["description"]:
    raise RuntimeError("Failed to find a supported default bopomofo IME.")

def guess_IME_name(langid):
    if configure.get("ONE_CBRLKB_TOGGLE_STATE"):
        try:
            oIPPMgr = oIPP.QueryInterface(ITfInputProcessorProfileMgr)
            profile = oIPPMgr.GetActiveProfile(GUID_TFCAT_TIP_KEYBOARD)
            if langid == profile.langid:
                if profile.dwProfileType == TF_PROFILETYPE_INPUTPROCESSOR:
                    return oIPP.GetLanguageProfileDescription(profile.clsid, profile.langid, profile.guidProfile)
                elif profile.dwProfileType == TF_PROFILETYPE_KEYBOARDLAYOUT:
                    return "%08X" % (profile.hkl,)
                else:
                    raise ValueError("Invalid dwProfileType value: {0.dwProfileType}".format(profile))
        except COMError as e:
            if e.hresult != E_NOINTERFACE:
                log.error("guess_IME_name failed", exc_info=True)
        except Exception as e:
            log.error("guess_IME_name failed", exc_info=True)
    return MICROSOFT_BOPOMOFO["description"] if langid == MICROSOFT_BOPOMOFO["language"] else None

_IME_State = namedtuple("_IME_State", ["mode", "name"])
def infer_IME_state(hwnd=None):
    global thread_states
    if hwnd is None:
        hwnd = getForegroundWindow()
    mode = (TF_CONVERSIONMODE_ALPHANUMERIC, TF_CONVERSIONMODE_NATIVE)
    pid, tid = getWindowThreadProcessID(hwnd)
    kl = DWORD(getKeyboardLayout(tid)).value
    fg = thread_states[pid]
    IME_name = "%08X" % (kl,)
    if kl in kl2name:
        log.debug("Recognized keyboard layout.")
        IME_name = kl2name[kl]
        return _IME_State(mode=(TF_CONVERSIONMODE_NOCONVERSION | mode[_name2clsid[IME_name] != DEFAULT_PROFILE[MICROSOFT_BOPOMOFO["language"]][0]]) if fg["mode"] is None else fg["mode"], name=IME_name)
    if DEFAULT_PROFILE[MICROSOFT_BOPOMOFO["language"]][0] == GUID_null and not fg["layout"]:
        log.debug("The default language profile is not an IME.")
        return _IME_State(mode=TF_CONVERSIONMODE_NOCONVERSION, name=IME_name)
    else:
        IME_name = fg["layout"] if fg["layout"] else guess_IME_name(LOWORD(kl))
        if IME_name in lookup_IME:
            log.debug("Recognized IME description.")
            return _IME_State(mode=(TF_CONVERSIONMODE_NOCONVERSION | mode[DEFAULT_PROFILE[MICROSOFT_BOPOMOFO["language"]][0] == GUID_null]) if fg["mode"] is None else fg["mode"], name=IME_name)
    log.debug("Guess the alphanumeric input mode.")
    return _IME_State(mode=mode[0], name=IME_name) # TF_CONVERSIONMODE_ALPHANUMERIC

def hack_compositionUpdate(self, compositionString, *args, **kwargs):
    global _real_compositionUpdate
    call, result = True, None
    log.debug("compositionUpdate: selection=({0}, {1}), isReading={2}, announce={announce}".format(*args, announce=kwargs.get("announce", True)))
    if sys.version_info.major < 3:
        log.debug("compositionString '{0}' -> '{1}'".format(self.compositionString.replace("'", r"\'"), compositionString.replace("'", r"\'")))
    else:
        log.debug("compositionString {0} -> {1}".format(repr(self.compositionString), repr(compositionString)))
    selectionStart, selectionEnd, isReading = args
    if not isReading and configure.get("NO_ANNOUNCEMENT_TYPING_PROCESS") and (infer_IME_state(self.windowHandle).mode & TF_CONVERSIONMODE_NATIVE):
        str_d = {"-": "", "+": "", None: ""}
        for s in difflib.ndiff(self.compositionString, compositionString):
            try: str_d[s[0]] += s[-1]
            except KeyError: str_d[None] += s[-1]
        m = re.match("(^[\u3100-\u312F]+$)|(^[`0-9A-Za-z]+$)|", str_d["+"])
        if m.group(1):
            kwargs["announce"] = bool(str_d["-"])
        elif m.group(2):
            if str_d["-"] == "" and str_d["+"] == "`":
                kwargs["announce"] = False
            else:
                call = False
    if call:
        log.debug("Call compositionUpdate() with announce={0}.".format(kwargs.get("announce")))
        result = _real_compositionUpdate(self, compositionString, *args, **kwargs)
    else:
        log.debug("Do not call compositionUpdate().")
    return result
_real_compositionUpdate = InputComposition.compositionUpdate
InputComposition.compositionUpdate = patch.monkey_method(hack_compositionUpdate, InputComposition)

class Translator:
    layout_index = ""
    def __init__(self, default_mapping, special_rules=None, sepchar="|"):
        split = lambda s: list(s if sepchar == "" else s.split(sepchar))
        self.default_map = dict(zip(Translator.layout_index, (split(k) for k in default_mapping)))
        self.special_rules = []
        if special_rules is not None:
            for p in special_rules:
                self.special_rules.append((re.compile(p[0], re.U), split(p[1])))
    def convert(self, subject):
        try: # Single-character cases.
            return [symbol2gesture(subject)]
        except:
            pass
        answer, skip = [], 0
        for i in range(len(subject)):
            if skip > 0:
                skip -= 1
                continue
            prefix, sub = [], self.default_map.get(subject[i], [symbol2gesture(subject[i])])
            for r in self.special_rules:
                m = r[0].match(subject, i)
                if m:
                    if m.end(0) > m.start(0):
                        skip = (m.end(0) - m.start(0)) - 1
                        sub = r[1]
                        break
                    prefix += r[1]
            answer.append(prefix + sub)
        return answer

# Layouts of keyboard mappings.
# Each layout is required to be a dict with all keys listed in layout_index.
layout = OrderedDict()
with codecs.open(os.path.join(os.path.dirname(__file__), str("keyboard_mappings.json")), encoding="UTF-8-SIG") as json_file:
    kbmaps_json = json_file.read()
    Translator.layout_index, layout = JSONDecoder(object_pairs_hook=OrderedDict).decode(kbmaps_json)

assert(set(mapping.keys()) == set(layout.keys()))

def vk2str(vkCode, scanCode): # GetKeyboardState does not work as expected.
    kst = [getKeyState(i) for i in range(256)]
    kst = (c_byte * len(kst))(*kst)
    b = create_unicode_buffer(32)
    l = user32.ToUnicodeEx(vkCode, scanCode, kst, b, len(b), 0, getInputHkl())
    return b.value if l > 0 else u""

def vkdbgmsg(vkCode, extended=None, injected=False):
    answer = ""
    if (vkCode, extended) in vkCodes.byCode:
        answer = vkCodes.byCode[(vkCode, extended)]
    elif extended is None and (vkCode, False) in vkCodes.byCode:
        answer = vkCodes.byCode[(vkCode, False)]
    elif (vkCode, None) in vkCodes.byCode:
        answer = vkCodes.byCode[(vkCode, None)]
    elif 0 <= vkCode < 128: # ASCII
        answer = chr(vkCode)
    else:
        answer = "0x%02X" % (vkCode,)
    if injected:
        answer = "{0}, injected".format(answer)
    return "vk: {0}".format(answer)

if __name__ == "__main__":
    pass
