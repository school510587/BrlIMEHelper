# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2020 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from collections import namedtuple
from collections import Callable
from collections import OrderedDict
from ctypes import windll

from keyboardHandler import getInputHkl
from logHandler import log
from winUser import *
import addonHandler
import config

try: unicode
except NameError: unicode = str

try:
    addonHandler.initTranslation()
except:
    pass

NUM_BRAILLE_KEYS = 9

ItemSpec = namedtuple("ItemSpec", ["label", "default_value", "allowed_values"])
profile = OrderedDict()
profile["AUTO_BRL_KEY"] = ItemSpec(
    label = _("Automatically enable braille keyboard simulation when NVDA starts."),
    default_value = False,
    allowed_values = None,
)
profile["DEFAULT_NO_ALPHANUMERIC_BRL_KEY"] = ItemSpec(
    label = _("Disable braille keyboard simulation by default in IME alphanumeric mode."),
    default_value = False,
    allowed_values = None,
)
profile["BRAILLE_KEYS"] = ItemSpec(
    label = _("Braille Keys:"),
    default_value = " FDSJKLA;",
    allowed_values = lambda bk: len(bk) == len(set(bk)) == NUM_BRAILLE_KEYS and
        all(ord(k) == windll.user32.MapVirtualKeyExW(VkKeyScanEx(k, getInputHkl())[1], MAPVK_VK_TO_CHAR, getInputHkl()) for k in bk),
)
profile["IGNORED_KEYS"] = ItemSpec(
    label = _("Ignored Keys:"),
    default_value = "0123456789",
    allowed_values = lambda ik: len(ik) == len(set(ik)) and
        all(ord(k) == windll.user32.MapVirtualKeyExW(VkKeyScanEx(k, getInputHkl())[1], MAPVK_VK_TO_CHAR, getInputHkl()) for k in ik),
)
profile["FREE_ALL_NON_BRL_KEYS_IN_ALPHANUMERIC_MODE"] = ItemSpec(
    label = _("Free all non-braille keys during braille keyboard simulation in IME alphanumeric mode."),
    default_value = False,
    allowed_values = None,
)
runtime_conf = None

_allowed = lambda value, allowed_values: True if allowed_values is None \
    else allowed_values(value) if isinstance(allowed_values, Callable) \
    else (value in allowed_values)

def assign(key, value):
    global profile, runtime_conf
    if runtime_conf is None:
        read()
    assert(isinstance(value, type(profile[key].default_value)))
    if not _allowed(value, profile[key].allowed_values):
        raise ValueError("{0!r} => {1!r}".format(key, value))
    old_value = runtime_conf[key]
    runtime_conf[key] = value
    return old_value

def conf_decode(value, default_value, allowed_values):
    assert(default_value is not None)
    if isinstance(default_value, bool):
        assert(allowed_values is None)
        value = value.strip().lower()
        if value == "true":
            answer = True
        elif value == "false":
            answer = False
        else:
            answer = bool(int(value))
        return answer
    assert(allowed_values is None or isinstance(allowed_values, Callable) or
        (default_value in allowed_values and all(type(v) is type(default_value) for v in allowed_values))
    )
    try:
        if isinstance(default_value, unicode):
            if not _allowed(value, allowed_values):
                raise ValueError
            return value
    except: # Any failure, including exception thrown by _allowed().
        raise ValueError(value)
    raise NotImplementedError

def get(key):
    global runtime_conf
    try:
        return runtime_conf[key]
    except:
        log.warning("Failed reading configuration: " + k)
    return profile[key].default_value

def read():
    global runtime_conf
    if "BrlIMEHelper" in config.conf:
        user_conf = config.conf["BrlIMEHelper"]
        runtime_conf = OrderedDict()
        for k, t in profile.items():
            try:
                runtime_conf[k] = conf_decode(user_conf[k], t.default_value, t.allowed_values)
            except:
                log.warning("Failed reading configuration: " + k, exc_info=True)
                runtime_conf[k] = t.default_value
    else:
        runtime_conf = OrderedDict((k, t.default_value) for k, t in profile.items())

def write():
    if "BrlIMEHelper" not in config.conf:
        config.conf["BrlIMEHelper"] = {}
    user_conf = config.conf["BrlIMEHelper"]
    for k, t in profile.items():
        try:
            user_conf[k] = unicode(runtime_conf[k])
        except:
            user_conf[k] = unicode(t.default_value)
