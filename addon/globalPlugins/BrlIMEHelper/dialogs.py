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
            conf_value = configure.get(k)
            if isinstance(conf_value, bool):
                self.CheckBox_settings[k] = sHelper.addItem(wx.CheckBox(self, label=v.label))
                self.CheckBox_settings[k].SetValue(conf_value)
            elif isinstance(conf_value, str):
                self.CheckBox_settings[k] = sHelper.addLabeledControl(v.label, wx.TextCtrl)
                self.CheckBox_settings[k].ChangeValue(conf_value)

    def postInit(self):
        list(self.CheckBox_settings.values())[0].SetFocus()

    def onOk(self, evt):
        for k, v in configure.profile.items():
            try:
                if isinstance(v.default_value, bool):
                    configure.assign(k, self.CheckBox_settings[k].IsChecked())
                elif isinstance(v.default_value, str):
                    configure.assign(k, self.CheckBox_settings[k].GetValue())
            except:
                log.error("Failed setting configuration: " + k, exc_info=True)
        return super(BrlIMEHelperSettingsDialog, self).onOk(evt)
