
from abaqusConstants import *
from abaqusGui import *
import os

thisPath = os.path.abspath(__file__)
thisDir  = os.path.dirname(thisPath)

class BonemapyDB(AFXDataDialog):

    def __init__(self, form):

        AFXDataDialog.__init__(self, form, 'Map HU values',self.OK|self.CANCEL, DIALOG_ACTIONS_SEPARATOR)
        self.form = form
        
        okBtn = self.getActionButton(self.ID_CLICKED_OK)
        okBtn.setText('OK')
            
        # Region selection
        GroupBox_1 = FXGroupBox(p=self, text='Select region', opts=FRAME_GROOVE|LAYOUT_FILL_X)
        FXRadioButton(p=GroupBox_1, text='Assembly set',  tgt=form.instORsetKw1, sel=1)
        FXRadioButton(p=GroupBox_1, text='Part instance', tgt=form.instORsetKw1, sel=2)
        fileTextHf1 = FXHorizontalFrame(p=GroupBox_1, opts=0, x=0, y=0, w=0, h=0, pl=0, pr=0, pt=0, pb=0, hs=0, vs=0)
        self.lab1   = FXLabel(p=fileTextHf1, text='', ic=None, opts=JUSTIFY_LEFT|LAYOUT_FIX_WIDTH, x=0, y=0, w=130, h=0, 
                              pl=DEFAULT_PAD, pr=DEFAULT_PAD, pt=DEFAULT_PAD, pb=DEFAULT_PAD)
        self.tf1    = AFXTextField(p=fileTextHf1, ncols=0, labelText='', tgt=form.instORsetNameKw, sel=0, opts=AFXTEXTFIELD_STRING|LAYOUT_FIX_WIDTH, w=245)
        
        # CT slice directory
        GroupBox_2  = FXGroupBox(p=self, text='CT slice directory', opts=FRAME_GROOVE|LAYOUT_FILL_X)
        dirHandler  = BonemapyDBDirHandler(form, 'CTsliceDir', 'All files (*)')
        fileTextHf2 = FXHorizontalFrame(p=GroupBox_2, opts=0, x=0, y=0, w=0, h=0, pl=0, pr=0, pt=0, pb=0, hs=DEFAULT_SPACING, vs=DEFAULT_SPACING)
        
        AFXTextField(p=fileTextHf2, ncols=42, labelText='Directory path: ', tgt=form.CTsliceDirKw, sel=0,
                     opts=AFXTEXTFIELD_STRING|LAYOUT_CENTER_Y|JUSTIFY_LEFT)
        icon = afxCreatePNGIcon(os.path.join(thisDir,'fileSelectSmall.png'))
        FXButton(p=fileTextHf2, text='', ic=icon, tgt=dirHandler, sel=AFXMode.ID_ACTIVATE,
                 opts=BUTTON_NORMAL|LAYOUT_CENTER_Y, x=0, y=0, w=0, h=0, pl=1, pr=1, pt=1, pb=1)
        FXCheckButton(p=GroupBox_2, text='Reset slice origin', tgt=form.resetCTOriginKw, sel=0)
        
        # Output details
        GroupBox_3 = FXGroupBox(p=self, text='Output details', opts=FRAME_GROOVE|LAYOUT_FILL_X)
        AFXTextField(p=GroupBox_3,  ncols=30, labelText='Name of output file of HU values: ', tgt=form.filenameKw, sel=0)
        FXCheckButton(p=GroupBox_3, text='Write odb output to visualise mapped HU values', tgt=form.writeOdbOutputKw, sel=0)
        
    def processUpdates(self):
        # When radioButton selection changes, update labels and corresponding keywords 
        value = self.form.instORsetKw1.getValue()
        if   value==1: self.lab1.setText('Name of assembly set:') 
        elif value==2: self.lab1.setText('Name of part instance:') 
        name  = self.form.radioButtonGroups.keys()[0]
        self.form.instORsetKw2.setValue(self.form.radioButtonGroups[name][2][value])  
        return          

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
       fileDb = AFXFileSelectorDialog(getAFXApp().getAFXMainWindow(), 'Select a Directory', self.fileNameKw, self.readOnlyKw,
                                      AFXSELECTFILE_DIRECTORY, self.patterns, self.patternTgt)
       fileDb.create()
       fileDb.showModal()
