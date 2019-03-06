# -*- coding: UTF-8 -*-
# Copyright (C) 2019 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from ctypes import *
from ctypes.wintypes import *
from threading import Thread
import string
import sys
import winsound
try: unichr
except NameError: unichr = chr
from keyboardHandler import KeyboardInputGesture, getInputHkl, isNVDAModifierKey
from logHandler import log
from winUser import *
import addonHandler
import brailleInput
import globalCommands
import globalPluginHandler
import inputCore
import queueHandler
import scriptHandler
import winInputHook
import ui

# addonHandler.initTranslation()

from NVDAHelper import localLib
from NVDAHelper import nvdaControllerInternal_inputConversionModeUpdate
from NVDAHelper import nvdaControllerInternal_inputLangChangeNotify
from NVDAHelper import _setDllFuncPointer
thread_states = {}
kl, layout = None, None
# Note: Monkeying handleInputConversionModeUpdate does not work.
@WINFUNCTYPE(c_long, c_long, c_long, c_ulong)
def hack_nvdaControllerInternal_inputConversionModeUpdate(oldFlags, newFlags, lcid):
    global thread_states
    pid = getWindowThreadProcessID(getForegroundWindow())[0]
    new_record = dict(zip(("mode", "layout"), (newFlags, "")))
    if pid in thread_states: new_record["layout"] = thread_states[pid]["layout"]
    thread_states[pid] = new_record
    log.debug('Logged IME mode change: pid={pid}, layout="{layout}", mode={mode}'.format(pid=pid, **thread_states[pid]))
    return nvdaControllerInternal_inputConversionModeUpdate(c_long(oldFlags), c_long(newFlags), c_ulong(lcid))
@WINFUNCTYPE(c_long, c_long, c_ulong, c_wchar_p)
def hack_nvdaControllerInternal_inputLangChangeNotify(threadID, hkl, layoutString):
    global thread_states
    pid = getWindowThreadProcessID(getForegroundWindow())[0]
    new_record = dict(zip(("mode", "layout"), (0, layoutString)))
    if pid in thread_states: new_record["mode"] = thread_states[pid]["mode"]
    thread_states[pid] = new_record
    log.debug('Logged IME language change: pid={pid}, layout="{layout}", mode={mode}'.format(pid=pid, **thread_states[pid]))
    return nvdaControllerInternal_inputLangChangeNotify(threadID, hkl, layoutString)

def scan_thread_ids(addon_inst):
    from time import sleep
    global thread_states
    while addon_inst.running:
        try:
            for pid in list(thread_states): # Use list() to avoid runtime error by size change.
                h = windll.Kernel32.OpenProcess(0x100000, 0, pid) # With SYNCHRONIZE access.
                if h: # The process exists.
                    windll.Kernel32.CloseHandle(h)
                else:
                    del thread_states[pid]
                    log.debug("Killed pid=%d" % (pid,))
        except:
            log.error("scan_thread_ids", exc_info=True)
        sleep(0.01)

# 替代型例外：
# 如果下一個輸入 new_char 是 ex_char 就把現在的注音取代成 replacement
# 例： ㄝ 與 ㄧㄞ 都可以在無聲母時使用，需要用聲調區別 ㄝˋ 與 ㄧㄞˊ
def replace(current_state, new_char, ex_char, replacement):
    if new_char == ex_char and current_state._bop_buf[-1] != replacement:
        current_state._bop_buf[-1] = replacement
        return True # handled
    return False
replace.__category__ = "CHECK_NEXT"

# 無聲母例外：
# 針對介母、韻母，如果目前輸入是點字緩衝區的第一個輸入，就要把輸入的內容替換成 replacement
def the_first(current_state, replacement):
    if current_state._brl_buf: return False
    current_state._bop_buf[-1] = replacement
    return True
the_first.__category__ = "CHECK_PREVIOUS"

# 把 dict 與一個 tuple 榜在一起
# 其中 next_state 表示下一個可接受的內部狀態
class Braille_Bopomofo_Dict(dict):
    def __init__(self, name, mapping, next_state):
        super(Braille_Bopomofo_Dict, self).__init__(mapping)
        self.name = name
        self.next_state = next_state

    def __repr__(self):
        return self.name

# 點字與聲調對應，沒有下一個可接受狀態
TONAL_MARK_DICT = Braille_Bopomofo_Dict("TONAL_MARK", {
    "1": "˙",
    "2": "ˊ",
    "3": " ",
    "4": "ˇ",
    "5": "ˋ",
}, tuple())

# 點字與介母、韻母對應，下一個可接受聲調輸入
RHYME_DICT = Braille_Bopomofo_Dict("RHYME", {
    # 介母、韻母
    "16"    : ("ㄧ",),
    "34"    : ("ㄨ",),
    "1256"  : ("ㄩ",),
    "345"   : ("ㄚ",),
    "126"   : ("ㄛ",),
    "2346"  : ("ㄜ",),
    "26"    : ("ㄧㄞ", (replace, "5", "ㄝ")), # ㄝ 跟 ㄧㄞ 同，預設顯示 ㄧㄞ 但遇第四聲改成 ㄝ
    "2456"  : ("ㄞ",),
    "356"   : ("ㄟ", (the_first, "ㄧㄛ"), (replace, "5", "ㄟ")), # 跟 ㄧㄛ 同，預設顯示 ㄟ 但前面無聲母則顯示 ㄧㄛ
    "146"   : ("ㄠ",),
    "12356" : ("ㄡ",),
    "1236"  : ("ㄢ",),
    "136"   : ("ㄣ",),
    "1346"  : ("ㄤ",),
    "1356"  : ("ㄥ",),
    "156"   : ("", (the_first, "ㄦ")), # 預設無顯示，如果前面沒有聲母則顯示 ㄦ
    # 疊韻 ㄧ 系列
    "23456" : ("ㄧㄚ",),
    "346"   : ("ㄧㄝ",),
    "246"   : ("ㄧㄠ",),
    "234"   : ("ㄧㄡ",),
    "2345"  : ("ㄧㄢ",),
    "1456"  : ("ㄧㄣ",),
    "46"    : ("ㄧㄤ",),
    "13456" : ("ㄧㄥ",),
    # 疊韻 ㄨ 系列
    "35"    : ("ㄨㄚ",),
    "25"    : ("ㄨㄛ",),
    "2356"  : ("ㄨㄞ",),
    "1246"  : ("ㄨㄟ",),
    "12456" : ("ㄨㄢ",),
    "123456": ("ㄨㄣ",),
    "456"   : ("ㄨㄤ",),
    "12346" : ("ㄨㄥ",),
    # 疊韻 ㄩ 系列
    "236"   : ("ㄩㄝ",),
    "45"    : ("ㄩㄢ",),
    "256"   : ("ㄩㄣ",),
    "235"   : ("ㄩㄥ",),
}, (TONAL_MARK_DICT,))

# ㄧㄩ 力外：
# 針對 ㄍㄘㄙ 如果接下來 new_char 是 ㄧㄩ 或其開始的疊韻，就要變成 replacement
def yi_yu(current_state, new_char, replacement):
    try:
        if RHYME_DICT[new_char][0][0] in "ㄧㄩ":
            current_state._bop_buf[-1] = replacement
            return True
    except:
        pass
    return False
yi_yu.__category__ = "CHECK_NEXT"

# 點字與聲母對應，下一個可接受介、韻母輸入
CONSONANT_DICT = Braille_Bopomofo_Dict("CONSONANT", {
    # 聲母
    "135"  : ("ㄅ",),
    "1234" : ("ㄆ",),
    "134"  : ("ㄇ",),
    "12345": ("ㄈ",),
    "145"  : ("ㄉ",),
    "124"  : ("ㄊ",),
    "1345" : ("ㄋ",),
    "14"   : ("ㄌ",),
    "13"   : ("ㄍ", (yi_yu, "ㄐ")),
    "123"  : ("ㄎ",),
    "1235" : ("ㄏ",),
    "1"    : ("ㄓ",),
    "12"   : ("ㄔ",),
    "24"   : ("ㄕ",),
    "1245" : ("ㄖ",),
    "125"  : ("ㄗ",),
    "245"  : ("ㄘ", (yi_yu, "ㄑ")),
    "15"   : ("ㄙ", (yi_yu, "ㄒ")),
}, (RHYME_DICT,))

# 點字與服泡對應，可以在此隨意新增符號定義
# 注意︰點字序列之間不可以有 prefix 的關係
SYMBOL_DICT = Braille_Bopomofo_Dict("SYMBOL", {
    "0": " ",
    "23-0": "，",
    "6-0": "、",
    "36-0": "。",
    "56-0": "；",
    "25-25": "：",
    "1456-0": "？",
    "123-0": "！",
    "5-5-5": "…",
    "5-2": "—",
    "246-0": "（",
    "135-0": "）",
    "126-126": "《",
    "345-345": "》",
    "12346-0": "【",
    "13456-0": "】",
    "126-0": "〈",
    "345-0": "〉",
    "56-36": "「",
    "36-23": "」",
    "236-236": "『",
    "356-356": "』",
    "456-12346": "＆",
    "4-3456": "＊",
    "4-16": "×",
    "46-34": "÷",
    "346-36": "±",
    "34-46-13": "≠",
    "6-123456": "∞",
    "5-46-13-126-156-12456": "≒",
    "126-123456": "≦",
    "345-123456": "≧",
    "46-146": "∩",
    "46-346": "∪",
    "1246-1234": "⊥",
    "1246-246-0": "∠",
    "4-34": "∵",
    "6-16": "∴",
    "4-156-46-13": "≡",
    "1246-123": "∥",
    "1246-126-25-25-135": "↑",
    "1246-146-25-25-135": "↓",
    "1246-246-25-25": "←",
    "1246-25-25-135": "→",
    "1246-2345": "△",
    "12346-13456": "□",
    # 希臘字母大寫 24 個
    "46-17": "Α",
    "46-127": "Β",
    "46-12457": "Γ",
    "46-1457": "Δ",
    "46-157": "Ε",
    "46-13567": "Ζ",
    "46-1567": "Η",
    "46-14567": "Θ",
    "46-247": "Ι",
    "46-137": "Κ",
    "46-1237": "Λ",
    "46-1347": "Μ",
    "46-13457": "Ν",
    "46-13467": "Ξ",
    "46-1357": "Ο",
    "46-12347": "Π",
    "46-12357": "Ρ",
    "46-2347": "Σ",
    "46-23457": "Τ",
    "46-1367": "Υ",
    "46-1247": "Φ",
    "46-123467": "Χ",
    "46-134567": "Ψ",
    "46-24567": "Ω",
    # 希臘字母小寫 24 個
    "46-1": "α",
    "46-12": "β",
    "46-1245": "γ",
    "46-145": "δ",
    "46-15": "ε",
    "46-1356": "ζ",
    "46-156": "η",
    "46-1456": "θ",
    "46-24": "ι",
    "46-13": "κ",
    "46-123": "λ",
    "46-134": "μ",
    "46-1345": "ν",
    "46-1346": "ξ",
    "46-135": "ο",
    "46-1234": "π",
    "46-1235": "ρ",
    "46-234": "σ",
    "46-2345": "τ",
    "46-136": "υ",
    "46-124": "φ",
    "46-12346": "χ",
    "46-13456": "ψ",
    "46-2456": "ω",
}, tuple())

# 點字緩衝區的狀態
# Members:
# _brl_buf: 記錄目前點字輸入的狀態
# _bop_buf: 記錄目前應有的注音輸出字串
# _stack: 記錄每個點字輸入的類型
class brl_buf_state:

    def __init__(self):
        self.reset()

    # 取得下一個點字輸入，產生狀態變化與輸出回饋
    # 輸出 dict 包含二個 keys: VK_BACK 為 backspace 的數量；bopomofo 為注音或符號序列
    def append_brl(self, brl_char):
        if brl_char == "\b":
            if not self._brl_buf: # no previous state
                return {}
            import os
            # 刪除目前「下一個可接受狀態」資訊
            del self._stack[-1]
            # 取出目前與狀態回復後的注音序列，以求出 difference
            current_bopomofo = "".join(self._bop_buf)
            self._bop_buf = self._stack[-1]["bopomofo"]
            past_bopomofo = "".join(self._bop_buf)
            p = os.path.commonprefix([current_bopomofo, past_bopomofo])
            # 回復之前的 next_state
            self._stack[-1] = self._stack[-1]["next_state"]
            # 刪除點字緩衝區一個字元
            del self._brl_buf[-1]
            # 用鋼材的 difference 寫成指令，使 libchewing 狀態同步
            return {"VK_BACK": len(current_bopomofo) - len(p), "bopomofo": past_bopomofo[len(p):]}
        from copy import copy
        # 即將被推入堆疊的舊狀態，包含三個 keys:
        # - class_info 為點字緩衝區對應 index 地方的點字內容屬於哪個分類 (CONSONANT, RHYME, TONAL_MARK, SYMBOL)
        # - bopomofo 為目前注音緩衝區的狀態，因為是 list 所以需要 copy 備份
        # - next_state 為當時打字之前堆疊頂端的值，列出接下來可接受點字組合
        # class_info 供 CHECK_NEXT 檢查用，其他資料做為 \b 的狀態回復用
        old_state = {"class_info": SYMBOL_DICT, "bopomofo": copy(self._bop_buf), "next_state": self._stack[-1]}
        try:
            # 找找看，這個輸入是否在允許的下一個類別裡
            ph_tabs = [d for d in self._stack[-1] if brl_char in d]
            # 目前我們只處理恰好一個類別的狀況
            if len(ph_tabs) != 1:
                raise KeyError
            res = {"VK_BACK": 0, "bopomofo": ""}
            # 考慮先前的注音輸入可能被現在的輸入影響
            if self._brl_buf:
                for t in self._stack[-2]["class_info"][self._brl_buf[-1]][1:]:
                    if t[0].__category__ != "CHECK_NEXT": continue
                    res["VK_BACK"] = len(self._bop_buf[-1])
                    if t[0](*((self, brl_char) + t[1:])):
                        res["bopomofo"] = self._bop_buf[-1]
                        break
                    res["VK_BACK"] = 0
            # 把目前點字的輸入先登記為預設值
            self._bop_buf.append(ph_tabs[0][brl_char][0])
            # 然後逐一檢查是否因為例外狀況要變換
            for t in ph_tabs[0][brl_char][1:]:
                if t[0].__category__ != "CHECK_PREVIOUS": continue
                if t[0](*((self,) + t[1:])): break
            # 處理完畢，把此次點字輸入堆進 buffer
            self._brl_buf.append(brl_char)
            key = "-".join(self._brl_buf)
            # 特例︰檢查是否注音序列恰好被符號定義走
            if key in SYMBOL_DICT:
                # 是，強迫內部狀態歸位，並以符號做為回傳
                res["VK_BACK"] = -1
                res["bopomofo"] += SYMBOL_DICT[key]
                self._stack[-1] = tuple()
            else:
                # 否，內部狀態進行轉換，並以注音做為回傳
                res["bopomofo"] += self._bop_buf[-1]
                old_state["class_info"] = ph_tabs[0]
                self._stack[-1] = old_state
                self._stack.append(ph_tabs[0].next_state)
            # 如果沒有下一個可接受輸入表示輸入完成一個中文字了，立即回到初始狀態
            if not self._stack[-1]:
                self.reset()
            return res
        except KeyError:
            pass
        # 注音輸入錯誤，但可能是輸入符號
        # 先把新輸入放進 buffer, 看看現有點字序列是否為某些符號的 prefix
        self._brl_buf.append(brl_char)
        key = "-".join(self._brl_buf)
        cands = [k for k in SYMBOL_DICT.keys() if k.startswith(key + "-") or k == key]
        if cands:
            self._stack[-1] = old_state
            self._stack.append(SYMBOL_DICT.next_state)
            symbol = SYMBOL_DICT.get(key, "")
            if symbol:
                # Exact match, 符號輸入完畢
                self.reset()
            return {"VK_BACK": -1, "bopomofo": symbol}
        # 也不是 prefix, 這次輸入屬於錯誤，應被拒絕
        del self._brl_buf[-1]
        return {} # input rejected

    def brl_check(self):
        return bool(self._brl_buf)

    def display_str(self, display_ucbrl):
        return self.ucbrl_str() if display_ucbrl or not self._stack[-1] else "".join(self._bop_buf)

    def hint_msg(self):
        bpmf_hint = ""
        if self._stack[-1]:
            if len(self._brl_buf) == 1:
                t = set(r[-1] if type(r) is tuple else r for r in self._stack[0]["class_info"][self._brl_buf[0]])
                t.discard("")
                bpmf_hint = "/".join(sorted(t))
            elif len(self._brl_buf) > 1:
                bpmf_hint = "".join(self._bop_buf)
            if bpmf_hint:
                bpmf_hint = " (" + bpmf_hint + ")"
        return "-".join(self._brl_buf) + bpmf_hint

    def reset(self):
        self._brl_buf = []
        self._bop_buf = []
        # 初始狀態，下一個可接受聲母或介、韻母輸入
        self._stack = [(CONSONANT_DICT, RHYME_DICT)]

    def ucbrl_str(self):
        ucbrl = ""
        for cell in self._brl_buf:
            u = 0
            for dot in cell:
                u |= 1 << int(dot) # 位移量為 1-8
            u = 0x2800 | (u >> 1)
            ucbrl += chr(u)
        return ucbrl

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

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = globalCommands.SCRCAT_BRAILLE

    # ACC_KEYS is the universe of all processed characters. BRL_KEYS and
    # SEL_KEYS must be its two disjoint subsets. Note that BRL_KEYS must
    # be ordered.
    ACC_KEYS = set(string.ascii_letters + string.digits + string.punctuation + " ")
    BRL_KEYS = " FDSJKLA;"
    SEL_KEYS = set("0123456789")

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

    def __init__(self):
        super(GlobalPlugin, self).__init__()
        self.kbbrl_enabled = False
        self.brl_state = brl_buf_state()
        self.bpmf_cumulative_str = ""
        self.running = True
        self.scanner = Thread(target=scan_thread_ids, args=(self,))
        self.scanner.start()
        _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", hack_nvdaControllerInternal_inputConversionModeUpdate)
        _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", hack_nvdaControllerInternal_inputLangChangeNotify)
        if sys.getwindowsversion().major < 6: # WinXP
            del self.symb2gesture["UNICODE_SUFFIX"]

    def terminate(self):
        _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", nvdaControllerInternal_inputConversionModeUpdate)
        _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", nvdaControllerInternal_inputLangChangeNotify)
        self.running = False
        self.scanner.join()
        self.disable()

    def initKBBRL(self): # Members for keyboard BRL simulation.
        self.ignore_injected_keys = ([], [])
        self.touched_chars = set()
        self._modifiedKeys = set()
        self._trappedKeys = set()
        self._trappedNVDAModifiers = set()
        self._gesture = None

    def enable(self):
        if self.kbbrl_enabled:
            return
        self.initKBBRL()
        # Monkey patch keyboard handling callbacks.
        # This is pretty evil, but we need low level keyboard handling.
        self._oldKeyDown = winInputHook.keyDownCallback
        winInputHook.keyDownCallback = self._keyDown
        self._oldKeyUp = winInputHook.keyUpCallback
        winInputHook.keyUpCallback = self._keyUp
        self.kbbrl_enabled = True

    def disable(self):
        if not self.kbbrl_enabled:
            return False
        winInputHook.keyDownCallback = self._oldKeyDown
        winInputHook.keyUpCallback = self._oldKeyUp
        self._gesture = None
        self._trappedKeys = None
        self.kbbrl_enabled = False

    def _keyDown(self, vkCode, scanCode, extended, injected):
        log.debug("keydown: vk = 0x%02X%s" % (vkCode, ", injected" if injected else ""))
        # Fix: Ctrl+X followed by X.
        try: # Check for keys that must be ignored.
            if self.ignore_injected_keys[0][0] != (vkCode, scanCode, bool(extended)):
                raise ValueError
            log.debug("keydown: pass injected key 0x%02X" % (vkCode,))
            del self.ignore_injected_keys[0][0]
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        except: pass
        # Note: 2017.3 doesn't support getNVDAModifierKeys.
        if isNVDAModifierKey(vkCode, extended) or vkCode in KeyboardInputGesture.NORMAL_MODIFIER_KEYS:
            self._trappedNVDAModifiers.add((vkCode, extended))
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        # Don't process vkCode if it is previously modified.
        if (vkCode, extended) in self._modifiedKeys:
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        # Don't process any numpad key.
        if vkCode & 0xF0 == 0x60:
            self._modifiedKeys.add((vkCode, extended))
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        # If any modifier key is down and vkCode is not previously trapped,
        # vkCode is now modified, and its message is passed to NVDA.
        if self._trappedNVDAModifiers:
            if (vkCode, extended) not in self._trappedKeys:
                self._modifiedKeys.add((vkCode, extended))
                return self._oldKeyDown(vkCode, scanCode, extended, injected)
        charCode = user32.MapVirtualKeyExW(vkCode, MAPVK_VK_TO_CHAR, getInputHkl())
        if HIWORD(charCode) != 0:
            return self._oldKeyDown(vkCode, scanCode, extended, injected)
        ch = unichr(LOWORD(charCode))
        log.debug('char code: %d' % (charCode,))
        try:
            dot = 1 << self.BRL_KEYS.index(ch)
        except: # not found
            if ch not in self.ACC_KEYS:
                return self._oldKeyDown(vkCode, scanCode, extended, injected)
            dot = 0
        self._trappedKeys.add(vkCode)
        self.touched_chars.add(ch)
        if dot:
            if not self._gesture:
                self._gesture = brailleInput.BrailleInputGesture()
            log.debug("keydown: dots|space = {0:09b}".format(dot))
            if dot == 1:
                self._gesture.space = True
            self._gesture.dots |= dot >> 1
        else: log.debug("keydown: num = %s" % (ch,))
        return False

    def _keyUp(self, vkCode, scanCode, extended, injected):
        log.debug("keyup: vk = 0x%02X%s" % (vkCode, ", injected" if injected else ""))
        try:
            if self.ignore_injected_keys[1][0] != (vkCode, scanCode, bool(extended)):
                raise ValueError
            log.debug("keyup: pass injected key 0x%02X" % (vkCode,))
            del self.ignore_injected_keys[1][0]
            return self._oldKeyUp(vkCode, scanCode, extended, injected)
        except: pass
        try:
            self._trappedKeys.remove(vkCode)
        except KeyError:
            self._trappedNVDAModifiers.discard((vkCode, extended))
            self._modifiedKeys.discard((vkCode, extended))
            return self._oldKeyUp(vkCode, scanCode, extended, injected)
        if not self._trappedKeys: # A session ends.
            k_brl, k_sel = set(self.BRL_KEYS) & self.touched_chars, self.SEL_KEYS & self.touched_chars
            try: # Select an action to perform, either BRL or SEL.
                if k_brl == self.touched_chars:
                    log.debug("keyup: send dot {0:08b} {1}".format(self._gesture.dots, self._gesture.space))
                    inputCore.manager.executeGesture(self._gesture)
                elif len(k_sel) == 1 and k_sel == self.touched_chars:
                    (ch,) = k_sel
                    self.send_keys(ch)
                else: winsound.MessageBeep()
            except inputCore.NoInputGestureAction:
                pass
            self._gesture = None
            self.touched_chars.clear()
        return False

    def send_keys(self, key_name_str):
        for k in key_name_str.split("|"):
            if not k: continue
            kbd_gesture = KeyboardInputGesture.fromName(k)
            if not kbd_gesture.isModifier and not kbd_gesture.modifiers and self.kbbrl_enabled:
                self.ignore_injected_keys[0].append((kbd_gesture.vkCode, kbd_gesture.scanCode, kbd_gesture.isExtended))
                self.ignore_injected_keys[1].append(self.ignore_injected_keys[0][-1])
            kbd_gesture.send()

    def script_toggleInput(self, gesture):
        if self.kbbrl_enabled:
            self.disable()
            # Translators: Reported when braille input from the PC keyboard is disabled.
            ui.message(_("停用：一般鍵盤模擬點字鍵盤"))
        else:
            self.enable()
            # Translators: Reported when braille input from the PC keyboard is enabled.
            ui.message(_("啟用：一般鍵盤模擬點字鍵盤"))

    def inferBRLmode(self):
        global thread_states
        pid, tid = getWindowThreadProcessID(getForegroundWindow())
        kl = getKeyboardLayout(tid)
        if sys.getwindowsversion().major < 6 and kl == 0x04040404: # WinXP
            return 0
        elif pid not in thread_states or thread_states[pid]["mode"] is None:
            return 2
        elif thread_states[pid]["mode"] & 1 and LOWORD(kl) == 0x0404:
            return 1
        return 0 # ENG

    def script_viewState(self, gesture):
        mode, msgs = self.inferBRLmode(), []
        if mode & 2: msgs.append("assumed")
        msgs.append(("ENG", "CHI")[mode & 1])
        ui.message(" ".join(msgs))

    # Translators: Describes a command.
    script_toggleInput.__doc__ = _("Toggles braille input from the PC keyboard.")

    def script_BRLdots(self, gesture):
        mode, key = self.inferBRLmode(), {}
        log.debug("BRLkeys: mode = %d" % (mode,))
        if mode & 1: # CHI
            current_braille = "".join(["%d"%(i+1,) for i in range(8) if gesture.dots & (1 << i)])
            if gesture.space: current_braille = "0" + current_braille
            key = self.brl_state.append_brl(current_braille)
        if not key: # ENG mode, or input is rejected by internal brl state.
            if gesture.dots == 0b01000000:
                log.debug("BRLkeys: dot7 default")
                scriptHandler.queueScript(globalCommands.commands.script_braille_eraseLastCell, gesture)
            elif gesture.dots == 0b10000000:
                log.debug("BRLkeys: dot8 default")
                scriptHandler.queueScript(globalCommands.commands.script_braille_enter, gesture)
            elif gesture.dots == 0b11000000:
                log.debug("BRLkeys: dot7+dot8 default")
                scriptHandler.queueScript(globalCommands.commands.script_braille_translate, gesture)
            elif mode & 1:
                log.debug("BRLkeys: input rejected")
                winsound.MessageBeep()
            else:
                log.debug("BRLkeys: dots default")
                scriptHandler.queueScript(globalCommands.commands.script_braille_dots, gesture)
            return
        log.debug('"{bpmf}" <= (VK_BACK={VK_BACK}, bopomofo="{bopomofo}")'.format(bpmf=self.bpmf_cumulative_str, **key))
        if key["VK_BACK"] > 0:
            self.bpmf_cumulative_str = self.bpmf_cumulative_str[:-key["VK_BACK"]]
        if len(key["bopomofo"]) > 0:
            if key["VK_BACK"] < 0:
                self.bpmf_cumulative_str = key["bopomofo"]
            else:
                self.bpmf_cumulative_str += key["bopomofo"]
        if not self.brl_state.brl_check(): # Composition completed.
            try:
                cmd_list = []
                for c in self.bpmf_cumulative_str:
                    key_name_str = self.symb2gesture.get(c, bopomofo_to_keys.get(c))
                    if key_name_str is None: # Lookup failure.
                        key_name_str = "%s%04x%s" % (self.symb2gesture["UNICODE_PREFIX"], ord(c), self.symb2gesture.get("UNICODE_SUFFIX", ""))
                        key_name_str = "|".join(key_name_str) # Insert "|" between characters.
                    cmd_list.append(key_name_str)
                for cmd in cmd_list:
                    log.debug('Sending "%s"' % (cmd,))
                    self.send_keys(cmd)
            except:
                log.warning('Undefined input gesture of "%s"' % (self.bpmf_cumulative_str,))
                winsound.MessageBeep()
            self.bpmf_cumulative_str = ""

    def script_BRLfnkeys(self, gesture):
        if gesture.dots == 0b00000001: # bk:dot1
            hint = self.brl_state.hint_msg()
            if hint: queueHandler.queueFunction(queueHandler.eventQueue, ui.message, hint)
            else: winsound.MessageBeep()
        elif gesture.dots == 0b00011010: # bk:dot2+dot4+dot5
            self.brl_state.reset()
            self.bpmf_cumulative_str = ""
        elif gesture.dots == 0b00111000: # bk:dot4+dot5+dot6
            log.debug("456+space")
            self.send_keys("Shift")

    __gestures = {
        "kb:NVDA+x": "toggleInput",
        "kb:NVDA+w": "viewState",
        "bk:dots": "BRLdots",
        "bk:space+dots": "BRLfnkeys",
    }
