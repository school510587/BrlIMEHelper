# -*- coding: UTF-8 -*-
# Copyright (C) 2020 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from winVersion import winVersion

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
if winVersion.major < 6: # WinXP
    symb2gesture["UNICODE_SUFFIX"] = ""

def from_str(string):
    cmd_list = []
    for c in string:
        key_name_str = symb2gesture.get(c, bopomofo_to_keys.get(c))
        if key_name_str is None: # Lookup failure.
            key_name_str = "%s%04x%s" % (symb2gesture["UNICODE_PREFIX"], ord(c), symb2gesture["UNICODE_SUFFIX"])
            key_name_str = "|".join(key_name_str) # Insert "|" between characters.
        cmd_list.append(key_name_str)
    return cmd_list
