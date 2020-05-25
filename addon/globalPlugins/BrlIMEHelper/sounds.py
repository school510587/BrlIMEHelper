# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2020 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

import os.path
import winsound

from nvwave import playWaveFile
from logHandler import log

addon_dir = os.path.dirname(__file__)

def _play_sound_hint(wav_path, replacement_winsound):
    try:
        playWaveFile(os.path.join(addon_dir, str(wav_path)))
    except:
        log.error("Error playing sound file: {0}".format(wav_path), exc_info=True)
        winsound.MessageBeep(replacement_winsound)

beep_typo = lambda: _play_sound_hint("beep_typo.wav", winsound.MB_ICONEXCLAMATION)
