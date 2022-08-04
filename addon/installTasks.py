# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2022 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

import wx

from brailleTables import getTable as getBRLtable
from logHandler import log
import addonHandler
import brailleInput
import gui

addonHandler.initTranslation()

def onInstall():
    try:
        us_comp8_table = getBRLtable("en-us-comp8-ext.utb")
    except:
        log.warning("No en-us-comp8-ext.utb found")
        return
    if brailleInput.handler.table is not us_comp8_table and gui.messageBox(
        # Translators: Dialog text shown to ask whether to change the braille input translation table.
        _('The current braille input translation table is "{0}". Would you like to change it to "{1}"?').format(brailleInput.handler.table.displayName, us_comp8_table.displayName),
        # Translators: Title of the dialog shown to ask whether to change the braille input translation table.
        _("Change the braille input translation table"), 
        wx.YES | wx.NO | wx.CENTER | wx.ICON_QUESTION
    ) == wx.YES:
        brailleInput.handler.table = us_comp8_table
        log.info("The braille input translation table has been changed to en-us-comp8-ext.utb")
