# -*- coding: UTF-8 -*-
# Copyright (C) 2019 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

# from __future__ import unicode_literals
from collections import namedtuple
from collections import OrderedDict

from logHandler import log
import addonHandler
import config

try:
    addonHandler.initTranslation()
except:
    pass

ItemSpec = namedtuple("ItemSpec", ["label", "default_value"])
profile = OrderedDict()
profile["AUTO_BRL_KEY"] = ItemSpec(
    label = _("Automatically enable braille keyboard simulation when NVDA starts."),
    default_value = False,
)
profile["DEFAULT_NO_ALPHANUMERIC_BRL_KEY"] = ItemSpec(
    label = _("Disable braille keyboard simulation by default in IME alphanumeric mode."),
    default_value = False,
)
runtime_conf = None

def conf_decode(value, valid_values):
    if type(valid_values[0]) is bool:
        value = value.strip().lower()
        if value == "true":
            return True
        elif value == "false":
            return False
        return bool(int(value))
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
                runtime_conf[k] = conf_decode(user_conf[k], [t.default_value])
            except:
                log.warning("Failed reading configuration: " + k, exc_info=True)
                runtime_conf[k] = t.default_value
    else:
        runtime_conf = OrderedDict((k, t.default_value) for k, t in profile.items())

def set(key, value):
    global runtime_conf
    if runtime_conf is None:
        read()
    runtime_conf[key] = value

def write():
    if "BrlIMEHelper" not in config.conf:
        config.conf["BrlIMEHelper"] = {}
    user_conf = config.conf["BrlIMEHelper"]
    for k, t in profile.items():
        try:
            user_conf[k] = str(runtime_conf[k])
        except:
            user_conf[k] = str(t.default_value)
