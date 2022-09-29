# -*- coding: utf-8 -*-

# Copyright (C) 2022 Michael Hogg

# This file is part of bonemapy - See LICENSE.txt for information on usage and redistribution

from abaqus import *
from abaqusConstants import *
from odbAccess import *
import os, copy
import elementTypes as et
import helperClasses as hc

# Use try to prevent error importing missing modules when bonemapy plug-in is launched
try:
    import numpy as np
    import pydicom
except: pass

# ~~~~~~~~~~ 

def getElements(m,regionSetName):
    
    """Get element type and number of nodes per element"""
        
    # Get elements
    region,setName = parseRegionSetName(regionSetName)
    if setName=='ALL': elements = m.rootAssembly.instances[region].elements
    else:              elements = m.rootAssembly.allSets[regionSetName].elements
    
    # Get part information: (1) instance names, (2) element types and (3) number of each element type 
    partInfo={}
    for e in elements: 
        if not partInfo.has_key(e.instanceName): partInfo[e.instanceName]={}
        if not partInfo[e.instanceName].has_key(e.type): partInfo[e.instanceName][e.type]=0
        partInfo[e.instanceName][e.type]+=1  
        
    # Put all element types from all part instances in a list
    eTypes = []
    for k1 in partInfo.keys():
        for k2 in partInfo[k1].keys(): eTypes.append(k2)
    eTypes = dict.fromkeys(eTypes,1).keys()
        
    # Check that elements are supported
    usTypes=[]
    for eType in eTypes:
        if not any([True for seType in et.seTypes.keys() if seType==eType]):
            usTypes.append(str(eType))
    if len(usTypes)>0:
        if len(usTypes)==1: strvars = ('',usTypes[0],regionSetName,'is')
        else:               strvars = ('s',', '.join(usTypes),regionSetName,'are') 
        print '\nElement type%s %s in region %s %s not supported' % strvars
        return None
    
    return partInfo, elements
       
# ~~~~~~~~~~      

def getModelData(modelName,regionSetName):

    """Get the node, element and int pnt data from the supplied part instance/assembly set"""

    # Get model
    m = mdb.models[modelName]
    
    # Get elements and part info
    result = getElements(m,regionSetName)
    if result==None: return None
    else:
        partInfo, elements = result
        numElems = len(elements)
        ec = dict([(ename,eclass()) for ename,eclass in et.seTypes.items()])
               
    # Get total number of integration points
    numIntPts = 0
    for instName in partInfo.keys():
        for etype,ecount in partInfo[instName].items():
            numIntPts += ec[etype].numIntPnts * ecount 
    
    # Get node data
    nodeData={}
    for instName in partInfo.keys():
        instNodes = m.rootAssembly.instances[instName].nodes
        numNodes  = len(instNodes)
        nodeData[instName] = np.zeros(numNodes,dtype=[('label','|i4'),('coord','|f4',(3,))])
        for n in xrange(numNodes):
            node = instNodes[n]
            nodeData[instName][n] = (node.label,node.coordinates)

    # Create empty dictionary,array to store element data 
    elemData = copy.deepcopy(partInfo)
    for instName in elemData.keys():
        for k,v in elemData[instName].items():
            elemData[instName][k] = np.zeros(v,dtype=[('label','|i4'),('econn','|i4',(ec[k].numNodes,))])
    eCount = dict([(k1,dict([k2,0] for k2 in partInfo[k1].keys())) for k1 in partInfo.keys()]) 

    # Create empty array to store int pnt data
    ipData = np.zeros(numIntPts,dtype=[('iname','|a80'),('label','|i4'),('ipnum','|i4'),('coord','|f4',(3,)),('HUval','|f4')])   

    # Calculate integration point coordinates from nodal coordinates using element 
    # interpolation function. Also get element data
    ilow = 0    
    for e in xrange(numElems):

        # Get element data
        elem       = elements[e]
        eInstName  = elem.instanceName
        eConn      = elem.connectivity
        eType      = elem.type
        eClass     = ec[eType]

        # Get int pnt coords from nodal coords
        nodeCoords = nodeData[eInstName]['coord'][list(eConn)]
        ipCoords   = eClass.getIntPointValues(nodeCoords)
        nip        = eClass.numIntPnts
        
        # Store int pnt data
        iupp = ilow + nip
        ipData['iname'][ilow:iupp] = eInstName
        ipData['label'][ilow:iupp] = elem.label
        ipData['ipnum'][ilow:iupp] = eClass.ipnums 
        ipData['coord'][ilow:iupp] = ipCoords
        ilow = iupp 
        
        # Store element label and connectivity
        eIndex = eCount[eInstName][eType]
        elemData[eInstName][eType][eIndex] = (elem.label,eConn)
        eCount[eInstName][eType] +=1  
        
    # Get bounding box for int pnt data
    minx,miny,minz = np.min(ipData['coord'],axis=0)
    maxx,maxy,maxz = np.max(ipData['coord'],axis=0)
    bbox = [[minx,miny,minz],[maxx,maxy,maxz]]
        
    return nodeData,elemData,ipData,bbox

# ~~~~~~~~~~

def getHUfromCT(CTsliceDir,resetCTOrigin,bbox):   
    
    """Loads CT stack into numpy array and creates an interpolation function"""
    
    # Get list of CT slice files    
    fileList = os.listdir(CTsliceDir)
    fileList = [os.path.join(CTsliceDir,fileName) for fileName in fileList] 
    numFiles = len(fileList)       

    # Get the z coordinates of each slice. All slices should have the (x,y) origin coordinates
    # Put the zcoord and filename into a numpy array. Then sort by zcoord to ensure that the 
    # list of filenames is sorted correctly
    z = np.zeros(numFiles,dtype=float)
    for i in xrange(numFiles):
        fileName = fileList[i]
        try: ds = pydicom.read_file(fileName)
        except: 
            print '\nCannot open CT slice file %s. Check that this is a valid dicom file' % fileName
            return None
        if i==0:
            rows,cols = ds.Rows, ds.Columns
            psx,psy   = ds.PixelSpacing
            psx = float(psx); psy = float(psy)
            ippx,ippy = ds.ImagePositionPatient[:2]
        z[i] = ds.ImagePositionPatient[-1]
        ds.clear()
    indx = np.argsort(z)
    z = z[indx]
    fileList = np.array(fileList)[indx]
    
    # If specified set CT slice origin to zero (ie. ignore CT slice origin in CT header)
    if resetCTOrigin:
        ippx=ippy=0.0

    # Get the x, y coordinates of the slice pixels. The coordinates are taken at the pixel centre
    x = np.linspace(ippx,ippx+psx*cols,cols,False)
    y = np.linspace(ippy,ippy+psy*rows,rows,False)      
    
    # Check that the model data lies within the bounds of the CT stack
    minx,miny,minz = bbox[0]
    maxx,maxy,maxz = bbox[1]
    if ((minx<x[0] or maxx>x[-1]) or (miny<y[0] or maxy>y[-1]) or (minz<z[0] or maxz>z[-1])):
        print '\nModel outside bounds of CT stack. Model must have been moved from original position'
        return None    
    
    # Load the CT slices into a numpy array. Only load the CT slices that are required
    ziLow = z.searchsorted(minz)-1
    ziUpp = z.searchsorted(maxz)+1
    z     = z[ziLow:ziUpp]
    fileList  = fileList[ziLow:ziUpp]
    numSlices = z.shape[0]
    CTvals = np.zeros((numSlices,cols,rows),dtype=np.int16)
    for i in xrange(numSlices):
        fileName = fileList[i]
        ds = pydicom.read_file(fileName)
        CTvals[i] = ds.pixel_array
        ds.clear()

    # Note: The array ds.PixelArray is indexed by [row,col], which is equivalent to [yi,xi]. Also,
    # because we are adding to CTvals by z slice, then the resulting index of CTvals is [zi,yi,xi].
    # Correct this to more typical index [xi,yi,zi] by swapping xi and zi e.g. zi,yi,xi -> xi,yi,zi
    CTvals = CTvals.swapaxes(0,2)
    
    # Create instance of triLinearInterp class
    interp = hc.triLinearInterp(x,y,z,CTvals) 
    
    # User message on CT stack info
    um  = 'CT stack summary:\n'
    um += 'Number of slices = %d\n' % numSlices
    um += 'Bot slice z coord = %.1f\n' % z[0] 
    um += 'Top slice z coord = %.1f\n' % z[-1]
    um += 'Number of rows, columns = %d, %d\n' % (rows,cols)
    um += 'Pixel size: %.3f in X, %.3f in Y\n' % (psx,psy)
    um += 'Slice origin (x,y) = (%.1f,%.1f)\n' % (ippx,ippy)
    print um
    
    return interp

# ~~~~~~~~~~

def mapHUtoMesh(ipData,interp):

    """Interpolates the HU values from the CT stack to the int pnts of the FE model"""

    # For each integration point, get the HU value by trilinear interpolation from
    # the nearest CT slice voxels
    numPoints = ipData.size
    for i in xrange(numPoints):
        xc,yc,zc = ipData[i]['coord'] 
        ipData[i]['HUval'] = interp(xc,yc,zc) 
    return ipData

# ~~~~~~~~~~
    
def writeOutput(ipData,outfilename):

    """ Writes the text output """
    
    # Get the current working directory so we can write the results file there
    outfilename = os.path.join(os.getcwd(),outfilename+'.txt')
    file1       = open(outfilename,'w')
    numPoints   = ipData.size
    for i in xrange(numPoints):
        ip       = ipData[i]
        instName = ip['iname']
        label    = ip['label']
        ipnum    = ip['ipnum']
        huval    = ip['HUval']
        file1.write('%s %7d %2d %8.1f\n' % (instName,label,ipnum,huval))
    file1.close()
    print ('HU results written to file: %s' % (outfilename))
   
    return 0

# ~~~~~~~~~~

def createPartInstanceInOdb(odb,instName,instNodes,instElems):
    
    """Create part instance in odb from provided nodes and elements"""
    
    # Create part in odb
    part = odb.Part(name=instName,embeddedSpace=THREE_D, type=DEFORMABLE_BODY)

    # Get all the nodes connected to the elements (not all elements in the instance). 
    # Also convert the connectivity from node indices to labels   
    nodeIndices={};
    for etype in instElems.keys():
        numElems=len(instElems[etype])
        for e in xrange(numElems):
            connect = instElems[etype][e]['econn']
            for i in connect: nodeIndices[i]=1
            instElems[etype][e]['econn'][:] = instNodes[connect]['label']
             
    # Get the node labels and node coordinates
    nodeIndices = np.array(nodeIndices.keys(),dtype=int)   
    nlabels = instNodes[nodeIndices]['label']
    ncoords = instNodes[nodeIndices]['coord']
    indx    = np.argsort(nlabels)
    nlabels = nlabels[indx]
    ncoords = ncoords[indx]
    
    # Add the nodes to the part
    part.addNodes(labels=nlabels,coordinates=ncoords)
    
    # Add the elements to the part
    for etype,edata in instElems.items():
        el = np.ascontiguousarray(edata['label'])
        ec = np.ascontiguousarray(edata['econn'])
        part.addElements(labels=el,connectivity=ec,type=str(etype))
               
    # Create part instance
    odb.rootAssembly.Instance(name=instName,object=part)
    odb.save()
    
    return 0

# ~~~~~~~~~~

def writeOdb(nodeData,elemData,ipData,regionSetName,outfilename):
    """
    Creates an odb from the specified assembly set / part instance. Then
    creates a frame and a fieldoutput corresponding to the mapped HU values
    """
    # Create new odb file
    odbName = outfilename+'.odb'        
    odb     = Odb(name=odbName)

    # Create step and frame in odb        
    step  = odb.Step(name='Step-1',description='',domain=TIME,timePeriod=1.0)
    frame = step.Frame(incrementNumber=0,frameValue=0.0)

    # Copy all the elements and associated nodes to the odb
    for instName in elemData.keys(): 
        createPartInstanceInOdb(odb,instName,nodeData[instName],elemData[instName])
    
    # Create an element set for the part instance / assembly set. This is required 
    # for use with the pyvXRAY plug-in  
    region,setName = parseRegionSetName(regionSetName)
    if region=='Assembly':
        elabels=[]
        for instName in elemData.keys():
            el=np.array([],dtype=int)
            for edata in elemData[instName].values():
                el = np.concatenate((el,edata['label']))
            el.sort()
            elabels.append([instName,el])
        odb.rootAssembly.ElementSetFromElementLabels(name=setName,elementLabels=elabels)          
    else:
        el=np.array([],dtype=int)
        for edata in elemData[region].values():
            el = np.concatenate((el,edata['label']))
        el.sort()
        odb.rootAssembly.instances[region].ElementSetFromElementLabels(name=setName,elementLabels=el)    
    
    # Create fieldOutput to visualise mapped HU values
    fo = frame.FieldOutput(name='HU',description='Mapped HU values',type=SCALAR)
    for instName in elemData.keys():
        i = odb.rootAssembly.instances[instName]
        indices1 = np.where(ipData['iname']==instName)
        indices2 = np.where(ipData[indices1]['ipnum']==1)
        l = ipData[indices1][indices2]['label']
        d = ipData[indices1]['HUval']
        l = np.ascontiguousarray(l)
        d = np.ascontiguousarray(d.reshape(d.size,1))    
        fo.addData(position=INTEGRATION_POINT,instance=i,labels=l,data=d)

    # Save and close odb
    odb.save()
    odb.close()
    print ('Odb file created: %s' % (os.path.join(os.getcwd(),odbName)))

    return 0

# ~~~~~~~~~~

def parseRegionSetName(regionSetName):
    """ Get region and setName from regionSetName """ 
    if '.' in regionSetName: region,setName = regionSetName.split('.')
    else:                 region,setName = 'Assembly',regionSetName   
    return region,setName

# ~~~~~~~~~~

def getHU(modelName, regionSetName, CTsliceDir, outfilename, resetCTOrigin, writeOdbOutput):
    """
    For the specified assembly set or part instance, gets the integration point coordinates
    for all the elements and maps the HU values from the corresponding CT stack to these
    points. Returns a text file that can be used in a subsequent finite element analysis that
    uses ABAQUS subroutine USDFLD to apply bone properties.

    Also creates an odb file with a fieldoutput showing the mapped HU values for checking.
    """ 
    # User message
    print '\nbonemapy plug-in to map HU values from CT stack to integration points of FE model'
    
    # Get model data
    print '\nExtracting model data'
    result = getModelData(modelName,regionSetName)
    if result is None:
        print '\nError in getModelData. Exiting'
        return
    else:
        nodeData,elemData,ipData,bbox = result

    # Get HU values from the CT stack
    print '\nGetting HU values from CT stack'   
    result = getHUfromCT(CTsliceDir,resetCTOrigin,bbox)
    if result is None:
        print '\nError in getHUfromCT. Exiting'
        return
    else:
        interp = result
        
    # Map HU values to the int pnts of the FE model mesh
    print '\nMapping HU values to the int pnts of the FE model mesh'   
    result = mapHUtoMesh(ipData,interp)
    if result is None:
        print '\nError in mapHUtoMesh. Exiting'
        return
    else:
        ipData = result

    # Write HU values to text file
    print '\nWriting text output'   
    result = writeOutput(ipData,outfilename)
    if result is None:
        print '\nError in writeOutput. Exiting'
        return        
    
    # Write odb file to check HU values have been calculated correctly
    if writeOdbOutput:
        print '\nCreating odb file for checking of mapped HU values'
        result = writeOdb(nodeData,elemData,ipData,regionSetName,outfilename)
        if result is None:
            print '\nError in writeOdbOutput. Exiting'
            return
    
    print '\nFinished\n'
    return
