# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2021 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from winsound import *
import os

from logHandler import log

def play_NVDA_sound(name):
    try: from globalVars import appDir as NVDA_appDir
    except: NVDA_appDir = "" # Earlier NVDA versions do not set this variable.
    import nvwave
    nvwave.playWaveFile(os.path.join(NVDA_appDir, "waves", str(name) + ".wav"))

addon_dir = os.path.dirname(__file__)

def _play_sound_hint(wav_path, replacement_winsound):
    try:
        wav_path = os.path.join(addon_dir, str(wav_path))
        if os.access(wav_path, os.R_OK):
            PlaySound(wav_path, SND_FILENAME|SND_ASYNC|SND_NODEFAULT)
        else:
            raise IOError("Failed to access {0}".format(wav_path))
    except:
        log.error("Error playing sound file: {0}".format(wav_path), exc_info=True)
        PlaySound(replacement_winsound, SND_ALIAS|SND_ASYNC)

beep_disable = lambda: _play_sound_hint("beep_disable.wav", "DeviceDisconnect")
beep_enable = lambda: _play_sound_hint("beep_enable.wav", "DeviceConnect")
beep_typo = lambda: _play_sound_hint("beep_typo.wav", "SystemExclamation")
