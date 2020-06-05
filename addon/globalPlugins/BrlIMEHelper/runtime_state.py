# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2020 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from collections import defaultdict
from ctypes import windll
from threading import Thread
from time import sleep
import os

from logHandler import log
from winUser import *

from . import configure

class _Runtime_States(defaultdict):
    def __init__(self):
        super(self.__class__, self).__init__(lambda: {"mode": None, "layout": "", "cbrlkb": configure.get("AUTO_BRL_KEY")})
        self.cbrlkb = configure.profile["AUTO_BRL_KEY"].default_value
        self.scanning = False
        self.scanner = None
    def __del__(self):
        self.stop_scan()
    def __missing__(self, key):
        log.debug("Create entry for pid={0}".format(key))
        return super(self.__class__, self).__missing__(key)
    def foreground_process_change_notify(self, new_pid):
        if configure.get("ONE_CBRLKB_TOGGLE_STATE"):
            return 0
        result, self.cbrlkb = (self[new_pid]["cbrlkb"] - self.cbrlkb), self[new_pid]["cbrlkb"]
        return result
    def reset_cbrlkb_state(self):
        old_cbrlkb_state = self.cbrlkb
        if configure.get("ONE_CBRLKB_TOGGLE_STATE"):
            self.cbrlkb = configure.get("AUTO_BRL_KEY")
        for pid in list(self): # Use list() to avoid runtime error by size change.
            try:
                self[pid]["cbrlkb"] = self.cbrlkb
                log.debug("Set cbrlkb state of pid={0} to {1}".format(pid, self.cbrlkb))
            except:
                log.warning("Failed to set cbrlkb state for pid={0}".format(pid), exc_info=True)
        return self.cbrlkb - old_cbrlkb_state
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
        pid = getWindowThreadProcessID(getForegroundWindow())[0]
        log.debug("Update entry {0} for pid={1}".format(kwargs, pid))
        self[pid].update(kwargs)
        return pid

thread_states = _Runtime_States()
