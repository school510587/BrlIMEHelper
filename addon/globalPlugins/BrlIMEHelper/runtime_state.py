# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2020 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from collections import defaultdict
from copy import copy
from ctypes import windll
from serial.win32 import INVALID_HANDLE_VALUE
from threading import Thread
from time import sleep
import os

from logHandler import log
from winUser import *

from . import configure

class _Runtime_States(defaultdict):
    def __init__(self):
        super(self.__class__, self).__init__(lambda: copy({"mode": None, "layout": "", "cbrlkb": configure.get("AUTO_BRL_KEY")}))
        self._cbrlkb = configure.profile["AUTO_BRL_KEY"].default_value
        self.scanning = False
        self.scanner = None
    def __del__(self):
        self.stop_scan()
    def __getitem__(self, key):
        item = super(self.__class__, self).__getitem__(key)
        if not configure.get("IND_BRL_KEY_4EACH_PROCESS"):
            item["cbrlkb"] = self._cbrlkb
        return item
    def __missing__(self, key):
        log.debug("Create entry for pid={0}".format(key))
        return super(self.__class__, self).__missing__(key)
    @property
    def cbrlkb(self):
        return self.get_by_hwnd(getForegroundWindow())["cbrlkb"] if configure.get("IND_BRL_KEY_4EACH_PROCESS") else self._cbrlkb
    @cbrlkb.setter
    def cbrlkb(self, value):
        if configure.get("IND_BRL_KEY_4EACH_PROCESS"):
            self.get_by_hwnd(getForegroundWindow())["cbrlkb"] = bool(value)
        else:
            self._cbrlkb = bool(value)
    def get_by_hwnd(self, hwnd):
        if hwnd == INVALID_HANDLE_VALUE:
            raise KeyError("Invalid window handle")
        pid = getWindowThreadProcessID(hwnd)[0]
        log.debug("Get item by hwnd={0} => pid={1}".format(hwnd, pid))
        return self[pid]
    def reset_cbrlkb_state(self):
        auto_cbrlkb = configure.get("AUTO_BRL_KEY")
        for pid in list(self): # Use list() to avoid runtime error by size change.
            try:
                self[pid]["cbrlkb"] = auto_cbrlkb
                log.debug("Reset cbrlkb state for pid=%d" % (pid,))
            except:
                log.error("Failed to reset cbrlkb state for pid=%d" % (pid,), exc_info=True)
    def start_scan(self):
        def scan_and_clear_unused_entries(self):
            while self.scanning:
                try:
                    for pid in list(self): # Use list() to avoid runtime error by size change.
                        h = windll.Kernel32.OpenProcess(0x100000, 0, pid) # With SYNCHRONIZE access.
                        if h: # The process exists.
                            windll.Kernel32.CloseHandle(h)
                        else:
                            del self[pid]
                            log.debug("Deleted pid=%d" % (pid,))
                except:
                    log.error("scan_and_clear_unused_entries", exc_info=True)
                sleep(0.01)
        self.scanning = True
        self.scanner = Thread(target=scan_and_clear_unused_entries, args=(self,))
        self.scanner.start()
    def stop_scan(self):
        if self.scanner is not None:
            self.scanning = False
            self.scanner.join()
            self.scanner = None
    def update_foreground(self, **kwargs):
        item = self.get_by_hwnd(getForegroundWindow())
        log.debug("Update this item by {0}".format(kwargs))
        item.update(kwargs)
        if "cbrlkb" in kwargs and not configure.get("IND_BRL_KEY_4EACH_PROCESS"):
            self._cbrlkb = kwargs["cbrlkb"]
        return item
    def update_self(self, **kwargs):
        pid = os.getpid()
        log.debug("Update entry {0} for NVDA itself (pid={1})".format(kwargs, pid))
        self[pid].update(kwargs)
        return pid

thread_states = _Runtime_States()
