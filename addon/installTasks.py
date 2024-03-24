# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2024 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

import wx

from brailleTables import getTable as getBRLtable
from logHandler import log
import addonHandler
import brailleInput
import config
import gui

addonHandler.initTranslation()

def onInstall():
    dirty_conf = False
    try:
        import globalPlugins.BrlIMEHelper
    except: # No previous effective installation.
        try:
            us_comp8_table = getBRLtable("en-us-comp8-ext.utb")
        except:
            log.warning("No en-us-comp8-ext.utb found")
        else: # Successfully find en-us-comp8-ext.utb.
            if brailleInput.handler.table is not us_comp8_table and gui.messageBox(
                # Translators: Dialog text shown to ask whether to change the braille input translation table.
                _('The current braille input translation table is "{0}". Would you like to change it to "{1}"?').format(brailleInput.handler.table.displayName, us_comp8_table.displayName),
                # Translators: Title of the dialog shown to ask whether to change the braille input translation table.
                _("Change the braille input translation table"), 
                wx.YES | wx.NO | wx.CENTER | wx.ICON_QUESTION
            ) == wx.YES:
                brailleInput.handler.table = us_comp8_table
                dirty_conf = True
                log.info("The braille input translation table has been changed to en-us-comp8-ext.utb")
    if dirty_conf and not config.conf["general"]["saveConfigurationOnExit"] and gui.messageBox(
        # Translators: Dialog text shown to ask whether to save the user configuration.
        _("The user configuration of NVDA has been changed. If it is not the first installation, then the reason would be the change of the option names/values of BrlIMEHelper. Would you like to save the change now?"),
        # Translators: Title of the dialog shown to ask whether to save the user configuration.
        _("Save the user configuration"), 
        wx.YES | wx.NO | wx.CENTER | wx.ICON_QUESTION
    ) == wx.YES:
        config.conf.save()
