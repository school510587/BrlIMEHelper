# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2020 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from ctypes import *

from NVDAHelper import localLib
from NVDAHelper import nvdaControllerInternal_inputConversionModeUpdate
from NVDAHelper import nvdaControllerInternal_inputLangChangeNotify
from NVDAHelper import _setDllFuncPointer
from logHandler import log

from .runtime_state import thread_states

# Note: Monkeying handleInputConversionModeUpdate does not work.

@WINFUNCTYPE(c_long, c_long, c_long, c_ulong)
def hack_nvdaControllerInternal_inputConversionModeUpdate(oldFlags, newFlags, lcid):
    global thread_states
    pid = thread_states.update_foreground(mode=newFlags)
    log.debug("IME mode update: oldFlags={0}, newFlags={1}, lcid={2} (IME layout: {3})".format(oldFlags, newFlags, lcid, thread_states[pid]["layout"]))
    return nvdaControllerInternal_inputConversionModeUpdate(c_long(oldFlags), c_long(newFlags), c_ulong(lcid))

@WINFUNCTYPE(c_long, c_long, c_ulong, c_wchar_p)
def hack_nvdaControllerInternal_inputLangChangeNotify(threadID, hkl, layoutString):
    global thread_states
    pid = thread_states.update_foreground(layout=layoutString)
    log.debug("IME language change: thread={0}, hkl={1}, layout={2} (IME mode: {3})".format(threadID, hkl, layoutString, thread_states[pid]["mode"]))
    return nvdaControllerInternal_inputLangChangeNotify(threadID, hkl, layoutString)

def install():
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", hack_nvdaControllerInternal_inputConversionModeUpdate)
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", hack_nvdaControllerInternal_inputLangChangeNotify)

def uninstall():
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", nvdaControllerInternal_inputConversionModeUpdate)
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", nvdaControllerInternal_inputLangChangeNotify)
