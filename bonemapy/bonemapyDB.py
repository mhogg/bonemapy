# -*- coding: utf-8 -*-

# Copyright (C) 2022 Michael Hogg

# This file is part of bonemapy - See LICENSE.txt for information on usage and redistribution

from abaqusConstants import *
from abaqusGui import *
import os

thisPath = os.path.abspath(__file__)
thisDir  = os.path.dirname(thisPath)

class BonemapyDB(AFXDataDialog):

    def __init__(self, form):

        AFXDataDialog.__init__(self, form, 'bonemapy - Map HU values',self.OK|self.CANCEL, DIALOG_ACTIONS_SEPARATOR)
        self.form = form
        
        okBtn = self.getActionButton(self.ID_CLICKED_OK)
        okBtn.setText('OK')
        
        # Select model
        GroupBox_1 = FXGroupBox(p=self, text='Select bone region', opts=FRAME_GROOVE|LAYOUT_FILL_X)
        VAligner_1 = AFXVerticalAligner(p=GroupBox_1, opts=0, x=0, y=0, w=0, h=0, pl=0, pr=0, pt=0, pb=0)
        ComboBox_1 = AFXComboBox(p=VAligner_1, ncols=45, nvis=1, text='Region model: ', tgt=form.modelNameKw, sel=0, pt=5, pb=5)    
        for modelName in self.form.modelList:
            ComboBox_1.appendItem(modelName)
        self.form.modelNameKw.setValue(self.form.modelList[0])
        ComboBox_1.setMaxVisible(10)
        self.modelName = self.form.modelList[0]
        
        # Select region
        self.ComboBox_2 = AFXComboBox(p=VAligner_1, ncols=45, nvis=1, text='Region set:', tgt=form.regionSetNameKw, sel=0, pt=5, pb=5)    
        self.ComboBox_2.setMaxVisible(10)      
        self.populateElementListComboBox()        
        
        # CT slice directory
        GroupBox_2  = FXGroupBox(p=self, text='CT slice directory', opts=FRAME_GROOVE|LAYOUT_FILL_X)
        dirHandler  = BonemapyDBDirHandler(form, 'CTsliceDir', 'All files (*)')
        fileTextHf2 = FXHorizontalFrame(p=GroupBox_2, opts=0, x=0, y=0, w=0, h=0, pl=0, pr=0, pt=5, pb=5, hs=DEFAULT_SPACING, vs=DEFAULT_SPACING)
        
        AFXTextField(p=fileTextHf2, ncols=42, labelText='Directory path: ', tgt=form.CTsliceDirKw, sel=0,
                     opts=AFXTEXTFIELD_STRING|LAYOUT_CENTER_Y|JUSTIFY_LEFT)
        icon = afxCreatePNGIcon(os.path.join(thisDir,r'icons\fileSelectSmall.png'))
        FXButton(p=fileTextHf2, text='', ic=icon, tgt=dirHandler, sel=AFXMode.ID_ACTIVATE,
                 opts=BUTTON_NORMAL|LAYOUT_CENTER_Y, x=0, y=0, w=0, h=0, pl=1, pr=1, pt=1, pb=1)
        FXCheckButton(p=GroupBox_2, text='Reset slice origin', tgt=form.resetCTOriginKw, sel=0)
        
        # Output details
        GroupBox_3 = FXGroupBox(p=self, text='Output details', opts=FRAME_GROOVE|LAYOUT_FILL_X)
        AFXTextField(p=GroupBox_3,  ncols=30, labelText='Name of output file of HU values: ', tgt=form.filenameKw, sel=0)
        FXCheckButton(p=GroupBox_3, text='Write odb output to visualise mapped HU values', tgt=form.writeOdbOutputKw, sel=0)
        
    def populateElementListComboBox(self):
        """Populate comboBox  containing element sets"""
        if len(self.form.elementSets)==0: return
        self.ComboBox_2.clearItems()
        for elementSet in self.form.elementSets:
            self.ComboBox_2.appendItem(elementSet)
        self.form.regionSetNameKw.setValue(self.form.elementSets[0])

    def processUpdates(self):
        # If model name changes, the re-populate the region list
        if self.form.modelNameKw.getValue() != self.modelName:
            self.modelName = self.form.modelNameKw.getValue()
            self.form.setModel(self.modelName)
            self.form.getElementSetList()
            self.populateElementListComboBox()  

class BonemapyDBDirHandler(FXObject):

    def __init__(self, form, keyword, patterns='*'):
        self.form = form
        self.patterns = patterns
        self.patternTgt = AFXIntTarget(0)
        exec('self.fileNameKw = form.%sKw' % keyword)
        self.readOnlyKw = AFXBoolKeyword(None, 'readOnly', AFXBoolKeyword.TRUE_FALSE)
        FXObject.__init__(self)
        FXMAPFUNC(self, SEL_COMMAND, AFXMode.ID_ACTIVATE, BonemapyDBDirHandler.activate)

    def activate(self, sender, sel, ptr):
       fileDb = AFXFileSelectorDialog(getAFXApp().getAFXMainWindow(), 'Select the CT directory', self.fileNameKw, self.readOnlyKw,
                                      AFXSELECTFILE_DIRECTORY, self.patterns, self.patternTgt)
       fileDb.create()
       fileDb.showModal()
