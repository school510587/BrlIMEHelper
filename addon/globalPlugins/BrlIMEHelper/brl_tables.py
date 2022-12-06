# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2022 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from collections import OrderedDict
from json import JSONDecoder
import codecs
import re
import struct

char_exp = "[\u2800-\u28FF]|\\\\u28[0-9A-F]{2}"
char_pattern = re.compile("({char})|\\[\\^?(({char})(-({char}))?)+\\]".format(char=char_exp), re.I | re.U)

class brl_buf_state:

    def __init__(self, json_path, error_logger=lambda m: None):
        with codecs.open(json_path, encoding="UTF-8") as json_file:
            bpmf_json = json_file.read()
            self.bpmf_rule_dict = JSONDecoder(object_pairs_hook=OrderedDict).decode(bpmf_json)
            self.bpmf_pattern_list = []
            for id in self.bpmf_rule_dict: # The key is identifier of the rule.
                if type(self.bpmf_rule_dict[id]) is OrderedDict:
                    self.bpmf_rule_dict[id] = list(self.bpmf_rule_dict[id].items())
                    for i in range(len(self.bpmf_rule_dict[id])):
                        condition, action = self.bpmf_rule_dict[id][i]
                        try:
                            self.bpmf_rule_dict[id][i] = (re.compile(condition, re.U), action)
                        except: # Compilation failed.
                            error_logger('{0}: "{1}" cannot compile.'.format(json_path, id))
                l = list(char_pattern.finditer(id))
                if not l or not (l[0].start() == 0 and all(l[j-1].end() == l[j].start() for j in range(1, len(l))) and l[-1].end() == len(id)):
                    continue # It does not contain braille composition information.
                self.bpmf_pattern_list.append((re.compile("(".join(p.group(0) for p in l) + ")?" * (len(l) - 1)), id))

    def brl_check(self, brl):
        if not brl: # Empty input must be rejected.
            raise NotImplementedError
        satisfied_patterns = []
        for p in self.bpmf_pattern_list:
            m = [p[0].match(brl), p[1]]
            if m[0] and m[0].start(0) == 0 and m[0].end(0) == len(brl):
                satisfied_patterns.append(m) # Full match.
        if not satisfied_patterns: # No match is found.
            raise NotImplementedError
        state = ["", False]
        for m in satisfied_patterns:
            if m[0].groups() and not m[0].groups()[-1]:
                state[1] = True # An intermediate state.
                continue
            if state[0]:
                continue # Only the first complete match is adopted.
            id_list = self.bpmf_rule_dict[m[1]]
            if type(id_list) is not list: # A single ID without enclosing brackets.
                id_list = [id_list]
            for i in range(len(id_list)):
                res = id_list[i]
                try:
                    p2c_list = self.bpmf_rule_dict[id_list[i]] # KeyError if not found.
                    for p2c in p2c_list:
                        for x in p2c[0].finditer(brl):
                            if x.start(0) == i: # At the correct position.
                                res = p2c[1]
                                raise KeyError # Exit loops.
                except KeyError:
                    pass
                state[0] += res
        return state

    def hint_msg(self, brl, default_message=None):
        if not brl and default_message is not None:
            return default_message
        s = "-".join("0" if ord(c) == 0x2800 else "".join(str(i + 1) if ord(c) & (1 << i) else "" for i in range(8)) for c in brl)
        return "{0} ({1})".format(brl, s)

# The BRF encoding map
# 6-dot Braille [P]attern (The 6 LSBs of a Unicode Braille Pattern character) <=> Braille [A]SCII
# Reference: liblouis table en-us-brf.dis
BRF_P2A, BRF_A2P = [0] * 64, {}
for k, v in zip(range(64), map(ord, " A1B'K2L@CIF/MSP\"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:4\\0Z7(_?W]#Y)=")):
    BRF_P2A[k] = struct.pack("B", v)
    BRF_A2P[BRF_P2A[k]] = k
if len(BRF_A2P) != len(BRF_P2A): raise RuntimeError

# The extended NABCC encoding map
# 8-dot Braille [P]attern (The low byte of a Unicode Braille Pattern character) <=> Arbitrary [B]yte
# The extended NABCC has the following additional mapping rules:
# Output     | Input
#------------+----------------------------------------------
# [128, 159] | Input of [96, 126] and 95 along with dot 7
# [160, 191] | Input of [32, 63] along with dot 7
# [192, 223] | Input of [32, 63] along with dot 7 and dot 8
# [224, 255] | Input of [32, 63] along with dot 8
# Reference: liblouis table en-nabcc.utb
NABCCX_P2B, NABCCX_B2P = [0] * 256, {}
_inverse_BRF = dict((ord(k) % 64, v) for k, v in BRF_A2P.items())
for i in range(len(NABCCX_P2B)):
    NABCCX_P2B[int("30102132"[i >> 5]) << 6 | _inverse_BRF[int("01000111"[i >> 5]) << 5 | (i % 32)]] = struct.pack("B", i)
NABCCX_P2B[0b00111000], NABCCX_P2B[0b01111000] = NABCCX_P2B[0b01111000], NABCCX_P2B[0b00111000]
del _inverse_BRF 
NABCCX_B2P = dict((v, k) for k, v in enumerate(NABCCX_P2B))
if len(NABCCX_B2P) != len(NABCCX_P2B): raise RuntimeError
