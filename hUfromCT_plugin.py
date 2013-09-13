from abaqusGui import *
from abaqusConstants import ALL
import osutils, os


###########################################################################
# Class definition
###########################################################################

class hUfromCT_plugin(AFXForm):

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, owner):
        
        # Construct the base class.
        #
        AFXForm.__init__(self, owner)
        self.radioButtonGroups = {}

        self.cmd = AFXGuiCommand(mode=self, method='getHU',
            objectName='HUfromCT', registerQuery=False)
        pickedDefault = ''
        if not self.radioButtonGroups.has_key('instORset'):
            self.instORsetKw1 = AFXIntKeyword(None, 'instORsetDummy', True)
            self.instORsetKw2 = AFXStringKeyword(self.cmd, 'instORset', True)
            self.radioButtonGroups['instORset'] = (self.instORsetKw1, self.instORsetKw2, {})
        self.radioButtonGroups['instORset'][2][79] = 'Assembly set'
        self.instORsetKw1.setValue(79)
        if not self.radioButtonGroups.has_key('instORset'):
            self.instORsetKw1 = AFXIntKeyword(None, 'instORsetDummy', True)
            self.instORsetKw2 = AFXStringKeyword(self.cmd, 'instORset', True)
            self.radioButtonGroups['instORset'] = (self.instORsetKw1, self.instORsetKw2, {})
        self.radioButtonGroups['instORset'][2][80] = 'Part instance'
        self.instORsetNameKw = AFXStringKeyword(self.cmd, 'instORsetName', True, 'BONE')
        self.CTsliceDirKw = AFXStringKeyword(self.cmd, 'CTsliceDir', True, '')
        self.resetCTOriginKw = AFXBoolKeyword(self.cmd, 'resetCTOrigin', AFXBoolKeyword.TRUE_FALSE, True,False)
        self.filenameKw = AFXStringKeyword(self.cmd, 'outfilename', True, 'HUvalues')
        self.writeOdbOutputKw = AFXBoolKeyword(self.cmd, 'writeOdbOutput', AFXBoolKeyword.TRUE_FALSE, True, True)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getFirstDialog(self):

        import hUfromCTDB
        return hUfromCTDB.hUfromCTDB(self)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def doCustomChecks(self):

        # Try to set the appropriate radio button on. If the user did
        # not specify any buttons to be on, do nothing.
        #
        for kw1,kw2,d in self.radioButtonGroups.values():
            try:
                value = d[ kw1.getValue() ]
                kw2.setValue(value)
            except:
                pass
        return True

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def okToCancel(self):

        # No need to close the dialog when a file operation (such
        # as New or Open) or model change is executed.
        #
        return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Register the plug-in
#
thisPath = os.path.abspath(__file__)
thisDir = os.path.dirname(thisPath)

toolset = getAFXApp().getAFXMainWindow().getPluginToolset()
toolset.registerGuiMenuButton(
    buttonText='pyXRAY tools|Map HU values', 
    object=hUfromCT_plugin(toolset),
    messageId=AFXMode.ID_ACTIVATE,
    icon=None,
    kernelInitString='import HUfromCT',
    applicableModules=ALL,
    version='0.1.0',
    author='Michael Hogg',
    description='An ABAQUS plugin used to extract bone properties from CT scans for use in finite element analyses of bone.\n\nUses tri-linear interpolation to map the HU values from the CT scans to the integration point coordinates of the mesh elements, as required for simulations that use ABAQUS subroutines such as USDFLD or UMAT to apply the bone properties.\n\nRequires that an ABAQUS model be open in the current viewport. Currently only accepts bone models meshed with C3D10 / C3D10M elements.',
    helpUrl='https://github.com/mhogg/bonemapy'
)
