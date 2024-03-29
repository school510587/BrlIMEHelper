# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2024 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import unicode_literals
try:
    from collections.abc import Iterable
    from collections.abc import Mapping
except:
    from collections import Iterable
    from collections import Mapping
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

    def __init__(self, parent, deactivate, post_apply=lambda *args: 0):
        try:
            super(BrlIMEHelperSettingsDialog, self).__init__(parent, hasApplyButton=True)
        except:
            super(BrlIMEHelperSettingsDialog, self).__init__(parent)
        self.deactivate, self.post_apply = deactivate, post_apply
        apply_button = wx.FindWindowById(wx.ID_APPLY, self)
        if apply_button is None:
            log.debug("Try to reconstruct buttons in the bottom right corner for NVDA versions earlier than 2018.2.")
            ok_button = wx.FindWindowById(wx.ID_OK, self)
            cancel_button = wx.FindWindowById(wx.ID_CANCEL, self)
            assert(ok_button.GetParent() is cancel_button.GetParent())
            mainSizer = ok_button.GetParent().GetSizer()
            if mainSizer.Remove(2): # The sizer containing [OK] and [Cancel] buttons is removed.
                ok_button.Destroy()
                cancel_button.Destroy()
                mainSizer.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.APPLY), border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL|wx.ALIGN_RIGHT)
                mainSizer.Fit(self)
            self.postInit()
        self.Bind(wx.EVT_BUTTON, self.onApply, id=wx.ID_APPLY)

    def Destroy(self):
        self.deactivate(False)
        return super(BrlIMEHelperSettingsDialog, self).Destroy()

    def makeSettings(self, settingsSizer):
        sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
        for k, v in configure.profile.items():
            conf_value = configure.get(k)
            if isinstance(conf_value, bool):
                self.options[k] = sHelper.addItem(wx.CheckBox(self, name=k, label=v.label))
                self.options[k].SetValue(conf_value)
            elif isinstance(conf_value, unicode):
                if isinstance(v.allowed_values, Iterable):
                    if isinstance(v.allowed_values, Mapping): # Choice box with processed values.
                        self.options[k] = sHelper.addLabeledControl(v.label, wx.Choice, choices=list(v.allowed_values.values()))
                        self.options[k].SetStringSelection(v.allowed_values[conf_value])
                    else: # Choice box with raw values.
                        self.options[k] = sHelper.addLabeledControl(v.label, wx.Choice, choices=v.allowed_values)
                        self.options[k].SetStringSelection(conf_value)
                else: # General textbox.
                    self.options[k] = sHelper.addLabeledControl(v.label, wx.TextCtrl)
                    self.options[k].ChangeValue(conf_value)
                self.options[k].SetName(k)
        self.options["BRAILLE_KEYS"].SetMaxLength(configure.NUM_BRAILLE_KEYS)
        self.options["BRAILLE_KEYS"].Bind(wx.EVT_KILL_FOCUS, self.onKeysOptionKillFocus)
        self.options["BRAILLE_KEYS"].Bind(wx.EVT_SET_FOCUS, self.onKeysOptionSetFocus)
        self.options["IGNORED_KEYS"].Bind(wx.EVT_KILL_FOCUS, self.onKeysOptionKillFocus)
        self.options["IGNORED_KEYS"].Bind(wx.EVT_SET_FOCUS, self.onKeysOptionSetFocus)

    def postInit(self):
        list(self.options.values())[0].SetFocus()

    def onApply(self, evt):
        backup, dirty, error = {}, set(), None
        for k in ("BRAILLE_KEYS", "IGNORED_KEYS"):
            p = self.options[k].GetInsertionPoint()
            self.options[k].ChangeValue(self.options[k].GetValue().upper())
            self.options[k].SetInsertionPoint(p)
        for k, v in configure.profile.items():
            try:
                if isinstance(v.default_value, bool):
                    backup[k] = configure.assign(k, self.options[k].IsChecked())
                elif isinstance(v.default_value, unicode):
                    if isinstance(v.allowed_values, Iterable):
                        if isinstance(v.allowed_values, Mapping):
                            backup[k] = configure.assign(k, list(v.allowed_values.keys())[self.options[k].GetSelection()])
                        else:
                            backup[k] = configure.assign(k, self.options[k].GetStringSelection())
                    else:
                        backup[k] = configure.assign(k, self.options[k].GetValue())
                if backup[k] != configure.get(k):
                    dirty.add(k)
            except:
                error = k if error is None else error
                log.error("Failed setting configuration: " + k, exc_info=True)
        if error is None:
            try:
                self.post_apply(dirty)
            except:
                log.warning("Cannot apply the configuration", exc_info=True)
                error = list(configure.profile.keys())[0]
        if error is not None:
            winsound.MessageBeep(winsound.MB_ICONHAND)
            for k, v in backup.items():
                configure.assign(k, v)
            self.options[error].SetFocus() # Where the first error occurs.
            self.post_apply(dirty)

    def onKeysOptionKillFocus(self, evt):
        self.deactivate(False)

    def onKeysOptionSetFocus(self, evt):
        self.deactivate(True)

    def onOk(self, evt):
        try:
            self.onApply(None)
        except:
            log.error("Cannot apply the settings", exc_info=True)
        return super(BrlIMEHelperSettingsDialog, self).onOk(evt)
