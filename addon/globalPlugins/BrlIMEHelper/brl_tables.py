# -*- coding: UTF-8 -*-
# Copyright (C) 2019 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from collections import OrderedDict
from json import JSONDecoder
import codecs
import re

char_exp = "[\u2800-\u28FF]|\\\\u28[0-9A-F]{2}"
char_pattern = re.compile("({char})|\\[(({char})(-({char}))?)+\\]".format(char=char_exp), re.I | re.U)

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
        self._brl_buf = ""

    def append_brl(self, brl_char):
        self._brl_buf += brl_char
        return self._brl_buf

    def brl_check(self, brl):
        if not brl: # Empty input must be rejected.
            raise NotImplementedError
        m = None # The first found match.
        for p in self.bpmf_pattern_list:
            m = [p[0].match(brl), p[1]]
            if m[0] and m[0].start(0) == 0 and m[0].end(0) == len(brl):
                break # Full match.
            m = None
        if not m: # No match is found.
            raise NotImplementedError
        if m[0].groups() and not m[0].groups()[-1]: # An intermediate state.
            return None
        answer, id_list = "", self.bpmf_rule_dict[m[1]]
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
            answer += res
        return answer

    def hint_msg(self, brl, default_message=None):
        if not brl and default_message is not None:
            return default_message
        s = "-".join("0" if ord(c) == 0x2800 else "".join(str(i + 1) if ord(c) & (1 << i) else "" for i in range(8)) for c in brl)
        return "{0} ({1})".format(brl, s)
