# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2024 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from ctypes import *
from functools import partial

from eventHandler import queueEvent
from logHandler import log
import NVDAHelper
import api
import braille
import brailleInput
import config
import keyboardHandler
import queueHandler
import ui

from . import configure
from . import patch
from .runtime_state import thread_states

try:
    from config.configFlags import ShowMessages
    class _confMessageTimeout:
        key = "showMessages"
        show_indefinitely = ShowMessages.SHOW_INDEFINITELY
        use_timeout = ShowMessages.USE_TIMEOUT
except: # The old NVDA versions.
    class _confMessageTimeout:
        key = "noMessageTimeout"
        show_indefinitely = True
        use_timeout = False

def hack_resetMessageTimer(real_resetMessageTimer, self, *args, **kwargs):
    if config.conf["braille"][_confMessageTimeout.key] == _confMessageTimeout.show_indefinitely and self._messageCallLater:
        self._messageCallLater.Stop()
        self._messageCallLater = None
    return real_resetMessageTimer(self, *args, **kwargs)
type(braille.handler)._resetMessageTimer = patch.monkey_method(partial(hack_resetMessageTimer, type(braille.handler)._resetMessageTimer), type(braille.handler))

def hack_bk_sendChars(real_bk_sendChars, self, *args, **kwargs):
    for k in args[0]:
        try:
            keyboardHandler.KeyboardInputGesture.fromName({"+": "plus"}.get(k, k)).send()
        except LookupError: # Not a key name.
            real_bk_sendChars(self, k, *args[1:], **kwargs)
        except: # Other unexpected exceptions.
            log.warning("Unexpected exception occurred. Debug is required.", exc_info=True)
            real_bk_sendChars(self, k, *args[1:], **kwargs)
type(brailleInput.handler).sendChars = patch.monkey_method(partial(hack_bk_sendChars, type(brailleInput.handler).sendChars), type(brailleInput.handler))

old_handleInputCompositionEnd = NVDAHelper.handleInputCompositionEnd
def hack_handleInputCompositionEnd(*args, **kwargs):
    log.debug("Interrupt BRL composition by hack_handleInputCompositionEnd().")
    queueEvent("interruptBRLcomposition", api.getFocusObject())
    return old_handleInputCompositionEnd(*args, **kwargs)

from NVDAHelper import handleInputConversionModeUpdate

def hack_queueHandler_queueFunction(hacked_func, focus, queue, func, *args, **kwargs):
    if func is handleInputConversionModeUpdate:
        log.debug("Replace handleInputConversionModeUpdate() with hack_handleInputConversionModeUpdate().")
        def hack_handleInputConversionModeUpdate(focus, *args, **kwargs):
            log.debug("Call handleInputConversionModeUpdate() after monkeying queueHandler.queueFunction().")
            def _hack_queueHandler_queueFunction(hacked_func, focus, queue, func, *args, **kwargs):
                if func is ui.message:
                    log.debug("Replace ui.message() by hack_ui_message().")
                    def hack_ui_message(*args, **kwargs):
                        log.debug("Call ui.message() with USE_TIMEOUT.")
                        old_value = config.conf["braille"][_confMessageTimeout.key]
                        if configure.get("NO_INDEFINITE_ICM_UPDATE_MSG") and config.conf["braille"][_confMessageTimeout.key] == _confMessageTimeout.show_indefinitely:
                            config.conf["braille"][_confMessageTimeout.key] = _confMessageTimeout.use_timeout
                        result = ui.message(*args, **kwargs)
                        config.conf["braille"][_confMessageTimeout.key] = old_value
                        return result
                    return queueEvent("showInputConversionMode", focus, ui_message=hack_ui_message, args=args, kwargs=kwargs)
                return hacked_func(queue, func, *args, **kwargs)
            old_func, queueHandler.queueFunction = queueHandler.queueFunction, partial(_hack_queueHandler_queueFunction, queueHandler.queueFunction, focus)
            result = handleInputConversionModeUpdate(*args, **kwargs)
            queueHandler.queueFunction = old_func
            return result
        func = lambda *args, **kwargs: hack_handleInputConversionModeUpdate(focus, *args, **kwargs)
    return hacked_func(queue, func, *args, **kwargs)

# Note: Monkeying handleInputConversionModeUpdate does not work.

from NVDAHelper import nvdaControllerInternal_inputConversionModeUpdate

@WINFUNCTYPE(c_long, c_long, c_long, c_ulong)
def hack_nvdaControllerInternal_inputConversionModeUpdate(oldFlags, newFlags, lcid):
    global thread_states
    log.debug("IME conversion mode update: oldFlags={0}, newFlags={1}, lcid={2}".format(oldFlags, newFlags, lcid))
    focus = api.getFocusObject()
    try:
        item = thread_states.update_foreground(source=focus, lcid=lcid, mode=newFlags)
        log.debug("IME status: {0}".format(item))
    except:
        log.error("IME conversion mode update failure", exc_info=True)
        item = None
    old_func, queueHandler.queueFunction = queueHandler.queueFunction, partial(hack_queueHandler_queueFunction, queueHandler.queueFunction, focus)
    result = nvdaControllerInternal_inputConversionModeUpdate(c_long(oldFlags), c_long(newFlags), c_ulong(lcid))
    queueHandler.queueFunction = old_func
    queueEvent("interruptBRLcomposition", focus)
    return result

from NVDAHelper import nvdaControllerInternal_inputLangChangeNotify

@WINFUNCTYPE(c_long, c_long, c_ulong, c_wchar_p)
def hack_nvdaControllerInternal_inputLangChangeNotify(threadID, hkl, layoutString):
    global thread_states
    log.debug("IME language change: thread={0}, hkl={1}, layoutString={2}".format(threadID, hkl, layoutString))
    try:
        item = thread_states.update_foreground(source=threadID, layout=layoutString)
        log.debug("IME status: {0}".format(item))
    except:
        log.error("IME language change failure", exc_info=True)
    result = nvdaControllerInternal_inputLangChangeNotify(threadID, hkl, layoutString)
    queueEvent("interruptBRLcomposition", api.getFocusObject())
    return result

from NVDAHelper import localLib
from NVDAHelper import _setDllFuncPointer

def install():
    NVDAHelper.handleInputCompositionEnd = hack_handleInputCompositionEnd
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", hack_nvdaControllerInternal_inputConversionModeUpdate)
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", hack_nvdaControllerInternal_inputLangChangeNotify)

def uninstall():
    NVDAHelper.handleInputCompositionEnd = old_handleInputCompositionEnd
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputConversionModeUpdate", nvdaControllerInternal_inputConversionModeUpdate)
    _setDllFuncPointer(localLib, "_nvdaControllerInternal_inputLangChangeNotify", nvdaControllerInternal_inputLangChangeNotify)
