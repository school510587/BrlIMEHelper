# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2020 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

import os.path
import winsound

from nvwave import playWaveFile
from logHandler import log

addon_dir = os.path.dirname(__file__)

def beep_typo():
    try:
        playWaveFile(os.path.join(addon_dir, str("beep_typo.wav")))
    except:
        log.error("Error playing sound file: beep_typo.wav", exc_info=True)
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
