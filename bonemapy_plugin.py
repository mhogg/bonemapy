# -*- coding: utf-8 -*-

# Copyright (C) 2013 Michael Hogg

# This file is part of bonemapy - See LICENSE.txt for information on usage and redistribution

from abaqusGui import *
from abaqusConstants import ALL
from kernelAccess import session, mdb
import os
from bonemapy_version import __version__

class Bonemapy_plugin(AFXForm):

    def __init__(self, owner):
        
        AFXForm.__init__(self, owner)

        self.cmd = AFXGuiCommand(mode=self, method='getHU',objectName='HUfromCT', registerQuery=False)       
        self.modelNameKw      = AFXStringKeyword(self.cmd, 'modelName', True, '')
        self.regionSetNameKw  = AFXStringKeyword(self.cmd, 'regionSetName', True, '')
        self.CTsliceDirKw     = AFXStringKeyword(self.cmd, 'CTsliceDir', True, '')
        self.resetCTOriginKw  = AFXBoolKeyword(self.cmd,   'resetCTOrigin', AFXBoolKeyword.TRUE_FALSE, True,False)
        self.filenameKw       = AFXStringKeyword(self.cmd, 'outfilename', True, 'HUvalues')
        self.writeOdbOutputKw = AFXBoolKeyword(self.cmd,   'writeOdbOutput', AFXBoolKeyword.TRUE_FALSE, True, True)
            
        self.m           = None
        self.modelList   = None
        self.elementSets = None
    
    def getModelList(self):
        self.modelList = mdb.models.keys()
    
    def getFirstModel(self):
        if self.modelList==None: return
        self.m = mdb.models[self.modelList[0]]
    
    def setModel(self,modelName):
        self.m = mdb.models[modelName]
    
    def getElementSetList(self):
        self.elementSets=[]
        if self.m==None: return
        for setName,set in self.m.rootAssembly.allSets.items():
            if len(set.elements)>0:
                self.elementSets.append(setName)
        for instName,inst in self.m.rootAssembly.instances.items():
            if len(inst.elements)>0:
                self.elementSets.append('.'.join([instName,'ALL'])) 
        self.elementSets.sort()
        return
    
    def getFirstDialog(self):
        self.getModelList()
        self.getFirstModel()
        self.getElementSetList()
        import bonemapyDB
        return bonemapyDB.BonemapyDB(self)
    
    def doCustomChecks(self):
    
        """Perform quick checks here. More extensive checks are performed by the kernel"""
               
        # Check that model exists
        self.getModelList()
        if self.modelNameKw.getValue() not in self.modelList:
            showAFXErrorDialog(self.getCurrentDialog(), 'Error: Model %s does not exist' % self.modelNameKw.getValue())
            return False

        # Check that region exists in model
        self.getElementSetList() 
        if self.regionSetNameKw.getValue() not in self.elementSets:
            showAFXErrorDialog(self.getCurrentDialog(), 'Error: Region %s does not exist' % self.regionSetNameKw.getValue())
            return False    
        
        # Check that CT slice directory exists
        CTsliceDir = self.CTsliceDirKw.getValue()
        if not (os.path.exists(CTsliceDir) and os.path.isdir(CTsliceDir)):
            showAFXErrorDialog(self.getCurrentDialog(), 'Error: CT directory "%s" does not exist' % CTsliceDir)
            return False 
            
        # Check that all files in the CT slice directory have the same file extension  
        fileList = os.listdir(CTsliceDir)
        fileList = [os.path.join(CTsliceDir,fileName) for fileName in fileList]    
        exts = dict([(os.path.splitext(fileName)[-1],1) for fileName in fileList])
        if len(exts.keys())>1:
            showAFXErrorDialog(self.getCurrentDialog(), 'Error: CT directory "%s" contains more than a single file type.\nIt must contain only dicom files' % CTsliceDir)
            return False       

        # Check for Abaqus version >= 6.11 
        majorNumber, minorNumber, updateNumber = getAFXApp().getVersionNumbers()
        if majorNumber==6 and minorNumber < 11:    
            showAFXErrorDialog( self.getCurrentDialog(), 'Error: ABAQUS 6.11 and above is required')
            return False
        
        # Check for numpy
        try: import numpy
        except: 
            showAFXErrorDialog( self.getCurrentDialog(), 'Error: Required module numpy cannot be found')
            return False
            
        # Check for pydicom
        try: import dicom
        except: 
            showAFXErrorDialog( self.getCurrentDialog(), 'Error: Required module pydicom cannot be found')
            return False      
        
        return True 

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Register the plug-in
desc  = 'An ABAQUS plugin used to extract bone properties from CT scans for use in finite element analyses of bone.\n\n'
desc += 'Uses tri-linear interpolation to map the HU values from the CT scans to the integration point coordinates of the '
desc += 'mesh elements, as required for simulations that use ABAQUS subroutines such as USDFLD or UMAT to apply the bone properties.\n\n'
desc += 'Requires that an ABAQUS model be open in the current viewport. Currently only accepts bone models meshed with tetrahedral '
desc += 'elements (ABAQUS element types C3D4, C3D4H, C3D10, C3D10H, C3D10I, C3D10M and C3D10MH are all supported).\n'

toolset = getAFXApp().getAFXMainWindow().getPluginToolset()
toolset.registerGuiMenuButton(
    buttonText='bonemapy|Map HU values', 
    object=Bonemapy_plugin(toolset),
    messageId=AFXMode.ID_ACTIVATE,
    icon=None,
    kernelInitString='import HUfromCT',
    applicableModules=ALL,
    version=__version__,
    author='Michael Hogg',
    description=desc,
    helpUrl='https://github.com/mhogg/bonemapy'
)
