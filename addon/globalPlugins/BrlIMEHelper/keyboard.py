# -*- coding: UTF-8 -*-
# Copyright (C) 2020 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from collections import OrderedDict

# Display names of keyboard mappings.
# It must be ordered to keep the order of dialog options constant.
mapping = OrderedDict()
mapping["STANDARD"] = _("Standard")
mapping["ET"] = _("E Tian")
mapping["IBM"] = _("IBM")
mapping["GIN_YIEH"] = _("Gin Yieh")
# Hanyu Pinyin
# Secondary Bopomofo Pinyin

# Layouts of keyboard mappings.
# Each layout is required to be a dict with all keys listed in layout_index.
layout_index = "ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦ ˊˇˋ˙"
layout = OrderedDict()
layout["STANDARD"] = dict(zip(layout_index, "1qaz2wsxedcrfv5tgbyhnujm8ik,9ol.0p;/- 6347"))
layout["ET"] = dict(zip(layout_index, "bpmfdtnlvkhg7c,./j;'sexuaorwiqzy890-= 2341"))
layout["IBM"] = dict(zip(layout_index, "1234567890-qwertyuiopasdfghjkl;zxcvbn m,./"))
layout["GIN_YIEH"] = dict(zip(layout_index, "2wsx3edcrfvtgb6yhnujm8ik,9ol.0p;/-['= qaz1"))

assert(set(mapping.keys()) == set(layout.keys()))
