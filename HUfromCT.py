# -*- coding: utf-8 -*-

# Copyright (C) 2013 Michael Hogg

# This file is part of bonemapy - See LICENSE.txt for information on usage and redistribution

from abaqus import *
from abaqusConstants import *
from odbAccess import *
import os, dicom, copy
import numpy as np
import elementTypes as et
import helperClasses as hc

# ~~~~~~~~~~ 

def getElements(m,instORset,instORsetName):
    
    """Get element type and number of nodes per element"""
        
    # Get elements
    if instORset=='Part instance':
        elements = m.rootAssembly.instances[instORsetName].elements
    elif instORset=='Assembly set':
        elements = m.rootAssembly.allSets[instORsetName].elements
    
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
            usTypes.append(eType)
    if len(usTypes)>0:
        print 'Element types %s in %s %s are not supported' % (', '.join(usTypes),instORset,instORsetName)   
        return None
    
    return partInfo, elements
       
# ~~~~~~~~~~      

def getModelData(instORset,instORsetName):

    """Get the integration point data from the supplied node and elements"""

    # Get model - Must be displayed in current viewport
    vpn = session.currentViewportName
    displayed = session.viewports[vpn].displayedObject
    mName = displayed.modelName
    m = mdb.models[mName]
    
    # Get elements and part info
    result = getElements(m,instORset,instORsetName)
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
        
    return nodeData,elemData,ipData

# ~~~~~~~~~~

def getHUfromCT(CTsliceDir,outfilename,resetCTOrigin,ipData):

    # Get a list of all the CT files in the specified directory
    if os.path.exists(CTsliceDir) and os.path.isdir(CTsliceDir):
        fileList = os.listdir(CTsliceDir)
        fileList = [os.path.join(CTsliceDir,fileName) for fileName in fileList]
    else:
        print '\nDirectory does not exist' 
        return None
    numFiles = len(fileList)

    # Check that all files in this directory have the same file extension
    exts = dict([(os.path.splitext(fileName)[-1],1) for fileName in fileList])
    if len(exts.keys())>1:
        print '\nDirectory contains more than a single file type: It must contain only CT slice files'
        return None

    # Get the z coordinates of each slice. All slices should have the (x,y) origin coordinates
    # Put the zcoord and filename into a numpy array. Then sort by zcoord to ensure that the 
    # list of filenames is sorted correctly
    z = np.zeros(numFiles,dtype=float)
    for i in xrange(numFiles):
        fileName = fileList[i]
        ds = dicom.read_file(fileName)
        if i==0:
            rows,cols = ds.Rows, ds.Columns
            print ('\nNumber of rows, columns = %d, %d' % (rows,cols))
            psx,psy   = ds.PixelSpacing
            psx = float(psx); psy = float(psy)
            print ('Pixel size: %.3f in X, %.3f in Y' % (psx,psy))
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

    # Check that all integration points are bounded by the extent of the CT slices   
    minx,miny,minz = np.min(ipData['coord'],axis=0)
    maxx,maxy,maxz = np.max(ipData['coord'],axis=0)
    if ((minx<x[0] or maxx>x[-1]) or (miny<y[0] or maxy>y[-1]) or (minz<z[0] or maxz>z[-1])):
        print '\nModel outside bounds of CT stack. Model must have been moved from original position'
        return None

    # Load all the CT slices into a numpy array
    numSlices = z.shape[0]
    CTvals = np.zeros((numSlices,cols,rows),dtype=np.int16)
    for i in xrange(numSlices):
      fileName = fileList[i]
      ds = dicom.read_file(fileName)
      CTvals[i] = ds.PixelArray
      ds.clear()

    # Note: The array ds.PixelArray is indexed by [row,col], which is equivalent to [yi,xi]. Also,
    # because we are adding to CTvals by z slice, then the resulting index of CTvals is [zi,yi,xi].
    # Correct this to more typical index [xi,yi,zi] by swapping xi and zi e.g. zi,yi,xi -> xi,yi,zi
    CTvals = CTvals.swapaxes(0,2)

    # Create instance of triLinearInterp class
    interp = hc.triLinearInterp(x,y,z,CTvals) 

    # For each integration point, get the HU value by trilinear interpolation from
    # the nearest CT slice voxels
    numPoints = ipData.size
    for i in xrange(numPoints):
        xc,yc,zc = ipData[i]['coord'] 
        ipData[i]['HUval'] = interp(xc,yc,zc)    
    
    # Get the current working directory so we can write the results file there
    workingdir  = os.getcwd()
    outfilename = os.path.join(workingdir,outfilename+'.txt')
    file1       = open(outfilename,'w')
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
    
    return

# ~~~~~~~~~~

def writeOdb(nodeData,elemData,ipData,outfilename):

    # Creates an odb from the specified assembly set / part instance. Then
    # creates a frame and a fieldoutput corresponding to the mapped HU values

    # Create new odb file
    odbName = outfilename+'.odb'        
    odb     = Odb(name=odbName)

    # Create step and frame in odb        
    step  = odb.Step(name='Step-1',description='',domain=TIME,timePeriod=1.0)
    frame = step.Frame(incrementNumber=0,frameValue=0.0)

    # Copy all the elements and associated nodes to the odb
    for instName in elemData.keys(): 
        createPartInstanceInOdb(odb,instName,nodeData[instName],elemData[instName])

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

    return 0

# ~~~~~~~~~~

def getHU(instORset, instORsetName, CTsliceDir, outfilename, resetCTOrigin, writeOdbOutput):
    """
    For the specified assembly set or part instance, gets the integration point coordinates
    for all the elements and maps the HU values from the corresponding CT stack to these
    points. Returns a text file that can be used in a subsequent finite element analysis that
    uses ABAQUS subroutine USDFLD to apply bone properties.

    Also creates an odb file with a fieldoutput showing the mapped HU values for checking.
    """ 

    result = getModelData(instORset,instORsetName)
    if result is None:
        print 'Error in getModelData. Exiting'
        return
    else:
        nodeData,elemData,ipData = result

    result = getHUfromCT(CTsliceDir,outfilename,resetCTOrigin,ipData)
    if result is None:
        print 'Error in getHUfromCT. Exiting'
        return

    # Write odb file to check HU values have been calculated correctly
    if writeOdbOutput:
        writeOdb(nodeData,elemData,ipData,outfilename)
    
    print '\nFinished\n'
    return
