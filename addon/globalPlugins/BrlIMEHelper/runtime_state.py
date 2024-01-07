# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2023 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from collections import defaultdict
from ctypes import windll
from functools import partial
from threading import Thread
from time import sleep
import os

from eventHandler import queueEvent
from logHandler import log
from treeInterceptorHandler import DocumentTreeInterceptor
from winUser import *
import api
import browseMode

from . import configure
from . import patch

def hack_reportPassThrough(real_func, treeInterceptor, onlyIfChanged=True, **kwargs):
    log.debug("Call hack_reportPassThrough with onlyIfChanged={0}.".format(onlyIfChanged))
    if not onlyIfChanged or treeInterceptor.passThrough != browseMode.reportPassThrough.last:
        log.debug("Interrupt BRL composition.")
        queueEvent("interruptBRLcomposition", api.getFocusObject())
    return real_func(treeInterceptor, onlyIfChanged=onlyIfChanged, **kwargs)
hack_reportPassThrough = partial(hack_reportPassThrough, browseMode.reportPassThrough)
hack_reportPassThrough.last = browseMode.reportPassThrough.last
browseMode.reportPassThrough = hack_reportPassThrough

def on_browse_mode():
    try:
        obj = api.getFocusObject()
        return (isinstance(obj.treeInterceptor, DocumentTreeInterceptor) and not obj.treeInterceptor.passThrough)
    except:
        pass
    return False

class _Runtime_States(defaultdict):
    def __init__(self):
        super(self.__class__, self).__init__(lambda: {"mode": None, "layout": "", "cbrlkb": configure.get("AUTO_BRL_KEY")})
        self._cbrlkb = configure.profile["AUTO_BRL_KEY"].default_value
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
        result, self._cbrlkb = (self[new_pid]["cbrlkb"] - self._cbrlkb), self[new_pid]["cbrlkb"]
        return result
    @property
    def cbrlkb(self):
        return self._cbrlkb
    @cbrlkb.setter
    def cbrlkb(self, value):
        self._cbrlkb = bool(value)
        if not configure.get("ONE_CBRLKB_TOGGLE_STATE"):
            self.update_foreground(cbrlkb=self._cbrlkb)
    @property
    def foreground(self):
        pid = getWindowThreadProcessID(getForegroundWindow())[0]
        log.debug("Performing some operation on pid={0}".format(pid))
        return self[pid]
    def reset_cbrlkb_state(self):
        old_cbrlkb_state = self._cbrlkb
        if configure.get("ONE_CBRLKB_TOGGLE_STATE"):
            self._cbrlkb = configure.get("AUTO_BRL_KEY")
        for pid in list(self): # Use list() to avoid runtime error by size change.
            try:
                self[pid]["cbrlkb"] = self._cbrlkb
                log.debug("Set cbrlkb state of pid={0} to {1}".format(pid, self._cbrlkb))
            except:
                log.warning("Failed to set cbrlkb state for pid={0}".format(pid), exc_info=True)
        return self._cbrlkb - old_cbrlkb_state
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
    def update_foreground(self, thread=None, **kwargs):
        if thread is None:
            fg = self.foreground
        else:
            pid = patch.getProcessIdOfThread(thread)
            if not pid: raise RunTimeError("Failed to get the process ID from thread ID {0}.".format(thread))
            log.debug("Update the state for pid={0}, tid={1}".format(pid, thread))
            fg = self[pid]
        log.debug("Update entry {0} for the pid".format(kwargs))
        fg.update(kwargs)
        return fg

thread_states = _Runtime_States()
