# -*- coding: utf-8 -*-

# Copyright (C) 2013 Michael Hogg

# This file is part of bonemapy - See LICENSE.txt for information on usage and redistribution

from abaqusConstants import *
from abaqusGui import *
from kernelAccess import mdb, session
import os

thisPath = os.path.abspath(__file__)
thisDir = os.path.dirname(thisPath)


###########################################################################
# Class definition
###########################################################################

class hUfromCTDB(AFXDataDialog):

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, form):

        # Construct the base class.

        AFXDataDialog.__init__(self, form, 'Map HU values',
            self.OK|self.CANCEL, DIALOG_ACTIONS_SEPARATOR)
        
        okBtn = self.getActionButton(self.ID_CLICKED_OK)
        okBtn.setText('OK')
            
        #GroupBox_8 = FXGroupBox(p=self, text='Description', opts=FRAME_GROOVE|LAYOUT_FILL_X)
        #desc  = 'This function is used to calculate HU values at the integration points\n'
        #desc += 'of all elements in a given part instance or assembly set. The model that\n'
        #desc += 'is used is that which is shown in the current viewport. The output is a\n' 
        #desc += 'file containing the HU values at each integration point.'
        #l = FXLabel(p=GroupBox_8, text=desc, opts=JUSTIFY_LEFT|TEXT_WORDWRAP)
        GroupBox_3 = FXGroupBox(p=self, text='Select region', opts=FRAME_GROOVE|LAYOUT_FILL_X)
        FXRadioButton(p=GroupBox_3, text='Assembly set',  tgt=form.instORsetKw1, sel=79)
        FXRadioButton(p=GroupBox_3, text='Part instance', tgt=form.instORsetKw1, sel=80)
        AFXTextField(p=GroupBox_3, ncols=28, labelText='Name of assembly set/part instance: ', tgt=form.instORsetNameKw, sel=0)
        GroupBox_1 = FXGroupBox(p=self, text='CT slice directory', opts=FRAME_GROOVE|LAYOUT_FILL_X)
        dirHandler = hUfromCTDBDirHandler(form, 'CTsliceDir', 'All files (*)')
        fileTextHf = FXHorizontalFrame(p=GroupBox_1, opts=0, x=0, y=0, w=0, h=0,
            pl=0, pr=0, pt=0, pb=0, hs=DEFAULT_SPACING, vs=DEFAULT_SPACING)
        fileTextHf.setSelector(99)
        AFXTextField(p=fileTextHf, ncols=42, labelText='Directory path: ', tgt=form.CTsliceDirKw, sel=0,
            opts=AFXTEXTFIELD_STRING|LAYOUT_CENTER_Y|JUSTIFY_LEFT)
        icon = afxCreatePNGIcon(os.path.join(thisDir,'fileSelectSmall.png'))
        FXButton(p=fileTextHf, text='	Select File\nFrom Dialog', ic=icon, tgt=dirHandler, sel=AFXMode.ID_ACTIVATE,
            opts=BUTTON_NORMAL|LAYOUT_CENTER_Y, x=0, y=0, w=0, h=0, pl=1, pr=1, pt=1, pb=1)
        FXCheckButton(p=GroupBox_1, text='Reset slice origin', tgt=form.resetCTOriginKw, sel=0)
        GroupBox_7 = FXGroupBox(p=self, text='Output details', opts=FRAME_GROOVE|LAYOUT_FILL_X)
        AFXTextField(p=GroupBox_7, ncols=20, labelText='Name of file that HU values will be written to: ', tgt=form.filenameKw, sel=0)
        FXCheckButton(p=GroupBox_7, text='Write odb output to visualise mapped HU values', tgt=form.writeOdbOutputKw, sel=0)


###########################################################################
# Class definition
###########################################################################

class hUfromCTDBDirHandler(FXObject):

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, form, keyword, patterns='*'):

        self.form = form
        self.patterns = patterns
        self.patternTgt = AFXIntTarget(0)
        exec('self.fileNameKw = form.%sKw' % keyword)
        self.readOnlyKw = AFXBoolKeyword(None, 'readOnly', AFXBoolKeyword.TRUE_FALSE)
        FXObject.__init__(self)
        FXMAPFUNC(self, SEL_COMMAND, AFXMode.ID_ACTIVATE, hUfromCTDBDirHandler.activate)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def activate(self, sender, sel, ptr):

       fileDb = AFXFileSelectorDialog(getAFXApp().getAFXMainWindow(), 'Select a Directory',
           self.fileNameKw, self.readOnlyKw,
           AFXSELECTFILE_DIRECTORY, self.patterns, self.patternTgt)
       fileDb.create()
       fileDb.showModal()
