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
    options = OrderedDict()

    def makeSettings(self, settingsSizer):
        sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
        for k, v in configure.profile.items():
            conf_value = configure.get(k)
            if isinstance(conf_value, bool):
                self.options[k] = sHelper.addItem(wx.CheckBox(self, name=k, label=v.label))
                self.options[k].SetValue(conf_value)
            elif isinstance(conf_value, unicode):
                self.options[k] = sHelper.addLabeledControl(v.label, wx.TextCtrl)
                self.options[k].SetName(k)
                self.options[k].ChangeValue(conf_value)
        self.options["BRAILLE_KEYS"].SetMaxLength(configure.NUM_BRAILLE_KEYS)

    def postInit(self):
        list(self.options.values())[0].SetFocus()

    def onOk(self, evt):
        backup, error = {}, False
        for k, v in configure.profile.items():
            try:
                if isinstance(v.default_value, bool):
                    backup[k] = configure.assign(k, self.options[k].IsChecked())
                elif isinstance(v.default_value, unicode):
                    backup[k] = configure.assign(k, self.options[k].GetValue())
            except:
                error = True
                log.error("Failed setting configuration: " + k, exc_info=True)
        if error:
            winsound.MessageBeep(winsound.MB_ICONHAND)
            for k, v in backup.items():
                configure.assign(k, v)
        return super(BrlIMEHelperSettingsDialog, self).onOk(evt)
