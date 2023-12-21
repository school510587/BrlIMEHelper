# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2023 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from ctypes import *

from NVDAHelper import localLib
from NVDAHelper import nvdaControllerInternal_inputConversionModeUpdate
from NVDAHelper import nvdaControllerInternal_inputLangChangeNotify
from NVDAHelper import _setDllFuncPointer
from eventHandler import queueEvent
from logHandler import log
import api

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
    result = nvdaControllerInternal_inputConversionModeUpdate(c_long(oldFlags), c_long(newFlags), c_ulong(lcid))
    queueEvent("interruptBRLcomposition", api.getFocusObject())
    return result

@WINFUNCTYPE(c_long, c_long, c_ulong, c_wchar_p)
def hack_nvdaControllerInternal_inputLangChangeNotify(threadID, hkl, layoutString):
    global thread_states
    log.debug("IME language change: thread={0}, hkl={1}, layoutString={2}".format(threadID, hkl, layoutString))
    try:
        item = thread_states.update_foreground(layout=layoutString)
        log.debug("IME status: {0}".format(item))
    except:
        log.error("IME language change failure", exc_info=True)
    result = nvdaControllerInternal_inputLangChangeNotify(threadID, hkl, layoutString)
    queueEvent("interruptBRLcomposition", api.getFocusObject())
    return result

def install():
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", hack_nvdaControllerInternal_inputConversionModeUpdate)
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", hack_nvdaControllerInternal_inputLangChangeNotify)

def uninstall():
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", nvdaControllerInternal_inputConversionModeUpdate)
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", nvdaControllerInternal_inputLangChangeNotify)
