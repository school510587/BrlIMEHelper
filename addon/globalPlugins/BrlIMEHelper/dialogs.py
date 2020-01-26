# -*- coding: UTF-8 -*-
# Copyright (C) 2019 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
from collections import OrderedDict
import winsound
import wx

import addonHandler
import gui
from gui import nvdaControls
from gui import guiHelper
from gui.settingsDialogs import SettingsDialog
from logHandler import log

from . import configure

try: unicode
except NameError: unicode = str

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
            elif isinstance(conf_value, unicode):
                self.CheckBox_settings[k] = sHelper.addLabeledControl(v.label, wx.TextCtrl)
                self.CheckBox_settings[k].ChangeValue(conf_value)

    def postInit(self):
        list(self.CheckBox_settings.values())[0].SetFocus()

    def onOk(self, evt):
        backup, error = {}, False
        for k, v in configure.profile.items():
            try:
                if isinstance(v.default_value, bool):
                    backup[k] = configure.assign(k, self.CheckBox_settings[k].IsChecked())
                elif isinstance(v.default_value, unicode):
                    backup[k] = configure.assign(k, self.CheckBox_settings[k].GetValue())
            except:
                error = True
                log.error("Failed setting configuration: " + k, exc_info=True)
        if error:
            winsound.MessageBeep(winsound.MB_ICONHAND)
            for k, v in backup.items():
                configure.assign(k, v)
        return super(BrlIMEHelperSettingsDialog, self).onOk(evt)
