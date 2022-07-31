# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2022 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import print_function
from __future__ import unicode_literals
from collections import OrderedDict
from ctypes import *
from json import JSONDecoder
import codecs
import os
import re

from keyboardHandler import getInputHkl
from winUser import *
import addonHandler
import vkCodes

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

# Display names of keyboard mappings.
# It must be ordered to keep the order of dialog options constant.
mapping = OrderedDict()
mapping["STANDARD"] = _("Standard")
mapping["E_TIAN"] = _("E Tian")
mapping["IBM"] = _("IBM")
mapping["JING_YE"] = _("Jing Ye")
mapping["HANYU_PINYIN"] = _("Hanyu Pinyin")
mapping["SECONDARY_BOPOMOFO_PINYIN"] = _("Secondary Bopomofo Pinyin")
mapping["TONGYONG_PINYIN"] = _("Tongyong Pinyin")

class _Symbol2KeyDict(dict):
    def __init__(self, *args, **kwargs):
        self.__class__.__base__.__init__(self, *args, **kwargs)
    def __getitem__(self, index):
        try:
            return self.__class__.__base__.__getitem__(self, index)
        except KeyError:
            if len(index) != 1:
                raise
            if winVersion.major >= 6: # Vista or later.
                return "|".join("`u%04x " % (ord(index),))
            elif ord(index) < 0x10000:
                return "|".join("`u%04x" % (ord(index),))
            raise # Bopomofo IME on WinXP does not support characters outside the BMP.

with codecs.open(os.path.join(os.path.dirname(__file__), str("{B2F9C502-1742-11D4-9790-0080C882687E}.json")), encoding="UTF-8") as json_file:
    IME_json = json_file.read()
    IME_data_dict = JSONDecoder(object_pairs_hook=OrderedDict).decode(IME_json)
symb2gesture = _Symbol2KeyDict(IME_data_dict.items())

class Translator:
    layout_index = "ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦ ˊˇˋ˙"
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
layout["STANDARD"] = ("1qaz2wsxedcrfv5tgbyhnujm8ik,9ol.0p;/- 6347",)
layout["E_TIAN"] = ("bpmfdtnlvkhg7c,./j;'sexuaorwiqzy890-= 2341",)
layout["IBM"] = ("1234567890-qwertyuiopasdfghjkl;zxcvbn m,./",)
layout["JING_YE"] = ("2wsx3edcrfvtgb6yhnujm8ik,9ol.0p;/-['= qaz1",)
layout["HANYU_PINYIN"] = ([
        "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h", "j", "q", "x", "zh", "ch", "sh", "r", "z", "c", "s",
        "yi", "wu", "yu", "a", "o", "e", "e", "ai", "ei", "ao", "ou", "an", "en", "ang", "eng", "er",
        "1", "2", "3", "4", "5",
    ], [
        (r"(?<=[ㄓㄔㄕㄖㄗㄘㄙ])(?![ㄨㄚㄜㄞㄟㄠㄡㄢㄣㄤㄥ])", "i"),
        (r"(?<=[ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒ])ㄧ", "i"),
        (r"ㄧ(?=[ㄚㄛㄝㄞㄠㄡㄢㄤ])", "y"),
        (r"(?<=[ㄉㄊㄋㄌㄍㄎㄏㄓㄔㄕㄖㄗㄘㄙ])ㄨ(?=ㄥ)", "o"),
        (r"(?<=[ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄓㄔㄕㄖㄗㄘㄙ])ㄨ", "u"),
        (r"ㄨ(?=[ㄚㄛㄞㄟㄢㄣㄤㄥ])", "w"),
        (r"(?<=[ㄋㄌ])ㄩ(?![ㄝㄢㄣㄥ])", "v"),
        (r"(?<=[ㄐㄑㄒ])ㄩ(?=ㄥ)", "io"),
        (r"(?<=[ㄋㄌㄐㄑㄒ])ㄩ", "u"),
        (r"ㄩ(?=ㄥ)", "yo"),
        (r"(?<=[ㄧㄩ])ㄣ", "n"),
        (r"(?<=[ㄧㄨㄩ])ㄥ", "ng"),
    ], "")
layout["SECONDARY_BOPOMOFO_PINYIN"] = ([
        "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h", "j", "ch", "sh", "j", "ch", "sh", "r", "tz", "ts", "s",
        "yi", "wu", "yu", "a", "o", "e", "e", "ai", "ei", "au", "ou", "an", "en", "ang", "eng", "er",
        "1", "2", "3", "4", "5",
    ], [
        (r"(?<=[ㄓㄔㄕ])(?![ㄨㄚㄜㄞㄟㄠㄡㄢㄣㄤㄥ])", "r"),
        (r"(?<=[ㄘㄙ])(?![ㄨㄚㄜㄞㄟㄠㄡㄢㄣㄤㄥ])", "z"),
        (r"(?<=[ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒ])ㄧ", "i"),
        (r"ㄧ(?=[ㄚㄛㄝㄞㄠㄡㄢㄤ])", "y"),
        (r"(?<![ㄉㄊㄋㄌㄍㄎㄏㄓㄔㄕㄖㄗㄘㄙ])ㄨ(?=ㄥ)", "we"),
        (r"(?<=[ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄓㄔㄕㄖㄗㄘㄙ])ㄨ", "u"),
        (r"ㄨ(?=[ㄚㄛㄞㄟㄢㄣㄤㄥ])", "w"),
        (r"(?<=[ㄋㄌㄐㄑㄒ])ㄩ", "iu"),
        (r"(?<=[ㄧㄩ])ㄣ", "n"),
        (r"(?<=[ㄧㄨㄩ])ㄥ", "ng"),
    ], "")
layout["TONGYONG_PINYIN"] = ([
        "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h", "j", "c", "s", "jh", "ch", "sh", "r", "z", "c", "s",
        "yi", "wu", "yu", "a", "o", "e", "e", "ai", "ei", "ao", "ou", "an", "en", "ang", "eng", "er",
        "1", "2", "3", "4", "5",
    ], [
        (r"(?<=[ㄓㄔㄕㄖㄗㄘㄙ])(?![ㄨㄚㄜㄞㄟㄠㄡㄢㄣㄤㄥ])", "ih"),
        (r"(?<=[ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒ])ㄧ", "i"),
        (r"ㄧ(?=[ㄚㄛㄝㄞㄠㄡㄢㄤ])", "y"),
        (r"(?<=[ㄉㄊㄋㄌㄍㄎㄏㄓㄔㄕㄖㄗㄘㄙ])ㄨ(?=ㄥ)", "o"),
        (r"(?<=[ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄓㄔㄕㄖㄗㄘㄙ])ㄨ", "u"),
        (r"ㄨ(?=[ㄚㄛㄞㄟㄢㄤ])", "w"),
        (r"ㄨ(?=ㄥ)", "wo"),
        (r"ㄩ(?=ㄥ)", "yo"),
        (r"(?<=[ㄧㄨㄩ])ㄣ", "n"),
        (r"(?<=ㄈ)ㄥ", "ong"),
        (r"(?<=[ㄧㄨㄩ])ㄥ", "ng"),
    ], "")

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
