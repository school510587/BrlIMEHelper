# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2023 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from ctypes import *
from time import time

from keyboardHandler import KeyboardInputGesture
from NVDAHelper import localLib
from NVDAHelper import nvdaControllerInternal_inputConversionModeUpdate
from NVDAHelper import nvdaControllerInternal_inputLangChangeNotify
from NVDAHelper import _setDllFuncPointer
from logHandler import log
import queueHandler

from . import configure
from .runtime_state import thread_states

# Note: Monkeying handleInputConversionModeUpdate does not work.

@WINFUNCTYPE(c_long, c_long, c_long, c_ulong)
def hack_nvdaControllerInternal_inputConversionModeUpdate(oldFlags, newFlags, lcid):
    global thread_states
    log.debug("IME conversion mode update: oldFlags={0}, newFlags={1}, lcid={2}".format(oldFlags, newFlags, lcid))
    try:
        item = thread_states.update_foreground(mode=newFlags)
        log.debug("IME status: {0}".format(item))
    except:
        log.error("IME conversion mode update failure", exc_info=True)
    return nvdaControllerInternal_inputConversionModeUpdate(c_long(oldFlags), c_long(newFlags), c_ulong(lcid))

_IME_search_start_time = None
_target_IME_name = ""

@WINFUNCTYPE(c_long, c_long, c_ulong, c_wchar_p)
def hack_nvdaControllerInternal_inputLangChangeNotify(threadID, hkl, layoutString):
    global _IME_search_start_time
    global _target_IME_name
    global thread_states
    log.debug("IME language change: thread={0}, hkl={1}, layoutString={2}".format(threadID, hkl, layoutString))
    try:
        item = thread_states.update_foreground(layout=layoutString)
        log.debug("IME status: {0}".format(item))
    except:
        log.error("IME language change failure", exc_info=True)
    silent = False
    if _IME_search_start_time is not None:
        if layoutString == _target_IME_name:
            log.info("The IME is set to '{0}'".format(layoutString))
            _IME_search_start_time = None
            # configure.get("CBRLKB_MANUAL_TOGGLE_HINT") != "ui.message"?
        elif time() - _IME_search_start_time > 0.5:
            log.info("Failed IME search.")
            _IME_search_start_time = None
        else:
            log.info("The current IME becomes '{0}'. The IME search continues.".format(layoutString))
            queueHandler.queueFunction(queueHandler.eventQueue, KeyboardInputGesture.fromName("windows+space").send)
            silent = True
    if silent:
        return 0
    return nvdaControllerInternal_inputLangChangeNotify(threadID, hkl, layoutString)

def install():
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", hack_nvdaControllerInternal_inputConversionModeUpdate)
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", hack_nvdaControllerInternal_inputLangChangeNotify)

def start_IME_search(target_IME_name):
    global _IME_search_start_time
    global _target_IME_name
    if _IME_search_start_time is not None:
        if time() - _IME_search_start_time > 0.5:
            _IME_search_start_time = None
        else:
            return False
    _target_IME_name = target_IME_name
    _IME_search_start_time = time()
    KeyboardInputGesture.fromName("windows+shift+space").send()
    return True

def uninstall():
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", nvdaControllerInternal_inputConversionModeUpdate)
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", nvdaControllerInternal_inputLangChangeNotify)
