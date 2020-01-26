# -*- coding: UTF-8 -*-
# Copyright (C) 2019 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from collections import OrderedDict
import wx

import addonHandler
import gui
from gui import nvdaControls
from gui import guiHelper
from gui.settingsDialogs import SettingsDialog
from logHandler import log

from . import configure

try:
    addonHandler.initTranslation()
except:
    pass

class BrlIMEHelperSettingsDialog(SettingsDialog):
    # Translators: Title of the Braille IME Helper settings dialog.
    title = _("Braille IME Helper Settings")
    CheckBox_settings = OrderedDict()

    def makeSettings(self, settingsSizer):
        sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
        for k, v in configure.profile.items():
            self.CheckBox_settings[k] = sHelper.addItem(wx.CheckBox(self, label=v.label))
            self.CheckBox_settings[k].SetValue(configure.get(k))

    def postInit(self):
        list(self.CheckBox_settings.values())[0].SetFocus()

    def onOk(self, evt):
        for k, v in self.CheckBox_settings.items():
            try:
                configure.assign(k, v.IsChecked())
            except:
                log.error("Failed setting configuration: " + k, exc_info=True)
        return super(BrlIMEHelperSettingsDialog, self).onOk(evt)
