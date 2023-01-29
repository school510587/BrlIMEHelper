# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2023 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import print_function
from __future__ import unicode_literals
from collections import OrderedDict
from comtypes import COMError
from comtypes import CLSCTX_ALL
from comtypes import GUID
from comtypes.GUID import GUID_null
from comtypes.client import CreateObject
from ctypes import *
from ctypes.wintypes import *
from json import JSONDecoder
import codecs
import itertools
import os
import re
try:
    import winreg
except:
    import _winreg as winreg

from keyboardHandler import getInputHkl
from logHandler import log
from winUser import *
import addonHandler
import vkCodes

from . import configure
from .msctf import *

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

# The profile ID of the Microsoft Bopomofo IME.
MICROSOFT_BOPOMOFO = {
    "profile": GUID("{B2F9C502-1742-11D4-9790-0080C882687E}"),
    "processor": GUID_null,
    "keyboard-layout": HANDLE(),
    "description": "",
}

# Display names of keyboard mappings.
mapping = configure.profile["KEYBOARD_MAPPING"].allowed_values

class _Symbol2KeyDict(dict):
    def __init__(self, IME_data_dict):
        type(self).__base__.__init__(self, IME_data_dict["SYMBOLS"].items())
        self.undefined_symbol_pattern = IME_data_dict["UNDEFINED_SYMBOL"]
        self.allow_non_bmp_symbols = bool(IME_data_dict["ALLOW_NON_BMP_SYMBOLS"])
    def __getitem__(self, index):
        try:
            return type(self).__base__.__getitem__(self, index)
        except KeyError:
            if len(index) != 1:
                raise
            elif ord(index) >= 0x10000 and not self.allow_non_bmp_symbols:
                raise
            return "|".join(self.undefined_symbol_pattern % (ord(index),))

with codecs.open(os.path.join(os.path.dirname(__file__), "{0}.json".format(MICROSOFT_BOPOMOFO["profile"])), encoding="UTF-8") as json_file:
    IME_json = json_file.read()
    IME_data = dict((GUID(g), d) for g, d in JSONDecoder(object_pairs_hook=OrderedDict).decode(IME_json).items())
    IME_data_dict = IME_data[GUID_null]
    try:
        oIPP = CreateObject(CLSID_TF_InputProcessorProfiles, CLSCTX_ALL, interface=ITfInputProcessorProfiles)
        gtr = oIPP.EnumLanguageProfiles(0x0404)
        while 1:
            profile = gtr.Next()
            if profile is None:
                break
            elif profile.guidProfile != MICROSOFT_BOPOMOFO["profile"]:
                continue
            MICROSOFT_BOPOMOFO["processor"] = profile.clsid
            MICROSOFT_BOPOMOFO["description"] = oIPP.GetLanguageProfileDescription(profile.clsid, profile.langid, profile.guidProfile)
            if profile.clsid not in IME_data:
                continue
            for k, v in IME_data[profile.clsid].items():
                if k in IME_data_dict:
                    if v is None:
                        del IME_data_dict[k]
                    else:
                        try:
                            IME_data_dict[k].update(v)
                        except:
                            IME_data_dict[k] = v
                elif v is not None:
                    IME_data_dict[k] = v
            if not oIPP.IsEnabledLanguageProfile(profile.clsid, 0x0404, MICROSOFT_BOPOMOFO["profile"]):
                log.warning("Microsoft Bopomofo IME is not enabled now.")
    except COMError:
        log.error("Some COM error occurred.", exc_info=True)
try:
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Keyboard Layouts") as kls:
        log.debug("Scanning HKLM")
        for i in itertools.count():
            kl_hex = winreg.EnumKey(kls, i)
            with winreg.OpenKey(kls, kl_hex) as kl:
                log.debug("Scanning {0}".format(kl_hex))
                try:
                    _name, _type = winreg.QueryValueEx(kl, "Layout Text")
                    if _type == winreg.REG_SZ and _name == MICROSOFT_BOPOMOFO["description"]:
                        MICROSOFT_BOPOMOFO["keyboard-layout"] = type(MICROSOFT_BOPOMOFO["keyboard-layout"])(int(kl_hex, 16))
                except WindowsError as w:
                    if w.winerror != 2: raise
except WindowsError as w:
    if w.winerror != 259: raise
symb2gesture = _Symbol2KeyDict(IME_data_dict)

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
            return [symb2gesture[subject]]
        except:
            pass
        answer, skip = [], 0
        for i in range(len(subject)):
            if skip > 0:
                skip -= 1
                continue
            prefix, sub = [], self.default_map.get(subject[i], [symb2gesture[subject[i]]])
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
