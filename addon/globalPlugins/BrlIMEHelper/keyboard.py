# -*- coding: UTF-8 -*-
# Copyright (C) 2020 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from winVersion import winVersion

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

bopomofo_to_keys = dict(zip( # 標準注音鍵盤
    "ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦ ˊˇˋ˙",
    "1qaz2wsxedcrfv5tgbyhnujm8ik,9ol.0p;/- 6347"
))

symb2gesture = _Symbol2KeyDict([
    (" ", " "),
    ("※", "Control+Alt+,|r"),
    ("←", "Control+Alt+,|b"),
    ("↑", "Control+Alt+,|h"),
    ("→", "Control+Alt+,|n"),
    ("↓", "Control+Alt+,|j"),
    ("─", "Control+Alt+,|z"),
    ("、", "Control+'"),
    ("。", "Control+."),
    ("「", "Control+Alt+,|="),
    ("」", "Control+Alt+,|\\"),
    ("『", "Control+Alt+,|0"),
    ("』", "Control+Alt+,|-"),
    ("【", "Control+["),
    ("】", "Control+]"),
    ("！", "Control+!"),
    ("，", "Control+,"),
    ("：", "Control+:"),
    ("；", "Control+;"),
    ("？", "Control+?"),
    ("｛", "Control+{"),
    ("｝", "Control+}"),
])

def from_str(string):
    try: # Single-character cases.
        return [symb2gesture[string]]
    except:
        pass
    cmd_list = []
    for c in string:
        key_name_str = bopomofo_to_keys.get(c, symb2gesture[c])
        cmd_list.append(key_name_str)
    return cmd_list
