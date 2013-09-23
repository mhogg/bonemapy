# -*- coding: utf-8 -*-

# Copyright (C) 2013 Michael Hogg

# This file is part of bonemapy - See LICENSE.txt for information on usage and redistribution

# Import modules required to run script

from abaqus import *
from abaqusConstants import *
from odbAccess import *
import os, shutil

def shapeFunctionC3D8(nv,ipc):

    """Interpolates from nodes to integration point (specified by isoparametric coordinates g,h,r) 
       using ABAQUS element C3D8 shape function (linear hexahedron)"""

    g,h,r=ipc
    U = (1-g)*(1-h)*(1-r)*nv[0] + (1+g)*(1-h)*(1-r)*nv[1] + \
        (1+g)*(1+h)*(1-r)*nv[2] + (1-g)*(1+h)*(1-r)*nv[3] + \
        (1-g)*(1-h)*(1+r)*nv[4] + (1+g)*(1-h)*(1+r)*nv[5] + \
        (1+g)*(1+h)*(1+r)*nv[6] + (1-g)*(1+h)*(1+r)*nv[7]
    U = U/8.0
    return U

def shapeFunctionC3D10(nv,ipc):

    """Interpolates from nodes to integration point (specified by isoparametric coordinates g,h,r) 
       using ABAQUS element C3D10 shape function (quadratic tetrahedron)"""

    g,h,r=ipc
    U = (2.0*(1.0-g-h-r)-1.0)*(1.0-g-h-r)*nv[0] + (2.0*g-1.0)*g*nv[1] + (2.0*h-1.0)*h*nv[2] + \
        (2.0*r-1.0)*r*nv[3] + 4.0*(1.0-g-h-r)*g*nv[4] + 4.0*g*h*nv[5] + 4.0*(1.0-g-h-r)*h*nv[6] + \
         4.0*(1.0-g-h-r)*r*nv[7] + 4.0*g*r*nv[8] + 4.0*h*r*nv[9]
    return U

def findNearestPixel(x,xc):

    """ For a given value, finds the nearest values in an array and interpolates between the 
        values to find the fraction of the given values between these values. The indices of
        the nearest values in the array and the fraction are returned
        NOTE: The isoparametric value is within the range For -1<=iso<=1, as required for use
              with shapeFunctionC3D8
    """
    xupp = x.searchsorted(xc); xlow = xupp-1
    if not (xupp==0 or xupp==x.size): 
        dx   = 0.5*(x[xupp] - x[xlow])
        xmid = x[xlow] + dx
        xiso = (xc-xmid)/dx
        return (xlow,xupp,xiso)
    else:
        print 'Value not found in array'
        return None

def checkInputs(instORset, instORsetName, CTsliceDir):

    """Checks the input parameters. If successful returns model and elements"""

    # Check that dependencies can be loaded
    import abaqus 
    abqversion = abaqus.version
    abqMajor,abqMinor = abqversion.split('.')[-1].split('-')
    if int(abqMajor) < 11: 
        print 'ABAQUS 6.11 and above is required'
        return None 
    
    try:    import numpy
    except: print 'Requirement numpy cannot be loaded'; return None 
    
    try:    import dicom
    except: print 'Requirement pydicom cannot be loaded'; return None

    # Check that CT slice directory exists
    if not os.path.isdir(CTsliceDir):
        print 'CT directory path does not exist'
        return None

    # Check that the model is open in the active viewport
    vpn = session.currentViewportName
    displayed = session.viewports[vpn].displayedObject
    try: 
        mName = displayed.modelName
    except:
        print '\nModel is not open in the current viewport'
        return None
    else:
        print '\nCurrent model is ' + mName
        print 'HU values will be calculated for this model\n'
        m = mdb.models[mName]

    # Get elements
    if instORset=='Part instance':
        if instORsetName in m.rootAssembly.instances.keys():
            elements = m.rootAssembly.instances[instORsetName].elements
        else:
            print '\n' + instORsetName + ' is not a part instance in the current model'
            return None
    elif instORset=='Assembly set':
        if instORsetName in m.rootAssembly.allSets.keys():
            elements = m.rootAssembly.allSets[instORsetName].elements
        else:
            print '\n' + instORsetName + ' is not an assembly set in the current model'
            return None

    # Check that all elements are type C3D10/C3D10M (only element currently supported)
    eTypes={}
    for e in elements: eTypes[e.type]=1
    if ['C3D10' in str(i) for i in eTypes.keys()].count(False) != 0:
        print '\nSpecified element must only contain C3D10 or C3D10M elements'
        print 'The current element types are present: ' + ', '.join(eTypes.keys())
        return None
    
    return (m,elements)

def getModelData(m,elements):

    """Get the integration point data from the supplied node and elements"""

    import numpy

    # Get all relevant instance names, the number of elements belonging to each instance, and all the
    # node coordinates for each instances. Note that we use the node index of the instance, not the label
    instNames={}
    for e in elements: 
        if not instNames.has_key(e.instanceName): instNames[e.instanceName]=0
        instNames[e.instanceName]+=1 

    nodeData={}
    for instName in instNames.keys():
        instNodes = m.rootAssembly.instances[instName].nodes
        numNodes  = len(instNodes)
        nodeData[instName] = numpy.zeros(numNodes,dtype=[('label','|i4'),('coords','|f4',(3,))])
        for n in xrange(numNodes):
            node = instNodes[n]
            nodeData[instName][n] = (node.label,node.coordinates)

    # Define isoparametric positions of the four integration points within an ABAQUS C3D10 element
    alpha=0.1770833333; beta=0.4687500000
    iso = numpy.array([[alpha,alpha,alpha],[beta,alpha,alpha],[alpha,beta,alpha],[alpha,alpha,beta]])

    # Calculate integration point coordinates from nodal coordinates using element shape function and put into array
    intPtsPerElem = 4
    nodesPerElem  = 10
    numElems  = len(elements)
    numIntPts = numElems*intPtsPerElem
    elemData  = {}
    for instName,elemsPerInst in instNames.items():
        elemData[instName] = numpy.zeros(elemsPerInst,dtype=[('label','|i4'),('connect','|i4',(nodesPerElem,))])
    connect = numpy.zeros(nodesPerElem,dtype=numpy.int16)
    ipData  = numpy.zeros(numIntPts,dtype=[('instName','|a80'),('label','|i4'),('ipnum','|i4'),('coords','|f4',(3,)),('HU','|f4')])
    xc = numpy.zeros(nodesPerElem,dtype=float); yc=xc.copy(); zc=xc.copy()
    intPntCnt = 0
    eCount=dict([(instName,0) for instName in instNames.keys()])
    for e in xrange(numElems):

        elem     = elements[e]
        eLabel   = elem.label
        instName = elem.instanceName
        nodes    = elem.connectivity

        eIndex   = eCount[instName]
        elemData[instName][eIndex] = (eLabel,nodes)

        nNodes = len(nodes)
        for n in xrange(nNodes):
            nIndex = nodes[n]
            xc[n],yc[n],zc[n] = nodeData[instName]['coords'][nIndex]

        for i in xrange(4):
            ipnum = i+1
            ipxc  = shapeFunctionC3D10(xc,iso[i])
            ipyc  = shapeFunctionC3D10(yc,iso[i])
            ipzc  = shapeFunctionC3D10(zc,iso[i]) 
            ipData[intPntCnt] = (instName,eLabel,ipnum,(ipxc,ipyc,ipzc),0.0)
            intPntCnt +=1

        eCount[instName]+=1

    return (nodeData,elemData,ipData)

def getHUfromCT(CTsliceDir,outfilename,resetCTOrigin,ipData):

    import dicom, numpy

    # Use shutil to get a list of all the CT files in the specified directory
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
    sliceInfo = numpy.zeros(numFiles,dtype=[('zcoord','|f4'),('filename','|a256')])
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
        ippz = ds.ImagePositionPatient[-1]
        sliceInfo[i] = (ippz,fileName)
        ds.clear()
    sliceInfo.sort()
    z = sliceInfo['zcoord']
    fileList = sliceInfo['filename']

    # If specified set CT slice origin to zero (ie. ignore CT slice origin in CT header)
    if resetCTOrigin:
        ippx=0.0; ippy=0.0

    # Get the x, y coordinates of the slice pixels. The coordinates are taken at the pixel centre
    x = numpy.zeros(cols,dtype=float)    
    x[0] = ippx
    for i in xrange(1,cols): x[i] = x[i-1] + psx

    y = numpy.zeros(rows,dtype=float)
    y[0] = ippy
    for i in xrange(1,rows): y[i] = y[i-1] + psy

    # Check that all integration points are bounded by the extent of the CT slices
    minx = ipData['coords'][:,0].min()
    maxx = ipData['coords'][:,0].max()
    miny = ipData['coords'][:,1].min()
    maxy = ipData['coords'][:,1].max()
    minz = ipData['coords'][:,2].min()
    maxz = ipData['coords'][:,2].max()
    if ((minx<x[0] or maxx>x[-1]) or (miny<y[0] or maxy>y[-1]) or (minz<z[0] or maxz>z[-1])):
        print '\nModel outside bounds of CT stack. Model must have been moved from original position'
        return None

    # Load all theCTvals CT slices into a numpy array
    numSlices = z.size
    CTvals = numpy.zeros((numSlices,cols,rows),dtype=numpy.int16)
    for i in xrange(numSlices):
      fileName = fileList[i]
      ds = dicom.read_file(fileName)
      CTvals[i] = ds.PixelArray
      ds.clear()

    # Note: The array ds.PixelArray is indexed by [row,col], which is equivalent to [yi,xi]. Also,
    # because we are adding to CTvals by z slice, then the resulting index of CTvals is [zi,yi,xi].
    # Correct this to more typical index [xi,yi,zi] by swapping xi and zi
    CTvals = CTvals.swapaxes(0,2)  # zi,yi,xi -> xi,yi,zi

    # For each integration point, get the HU value by trilinear interpolation from
    # the nearest CT slice voxels
    numPoints = ipData.size
    for i in xrange(numPoints):

        xc,yc,zc = ipData[i]['coords']

        #xlow = int((xc-ippx)/psx); xupp=xlow+1
        #if xlow<=0 or xupp>=cols-1: return None
        #xmid = psx*(xlow+0.5)
        #xiso = (xc-xmid)/(0.5*psx)

        #ylow = int((yc-ippy)/psy); yupp=ylow+1
        #if ylow<=0 or yupp>=rows-1: return None
        #ymid = psy*(ylow+0.5)
        #yiso = (yc-ymid)/(0.5*psy)
               
        result = findNearestPixel(x,xc)
        if result is None: return result
        else: xlow,xupp,xiso = result

        result = findNearestPixel(y,yc)
        if result is None: return result
        else: ylow,yupp,yiso = result

        result = findNearestPixel(z,zc)
        if result is None: return result
        else: zlow,zupp,ziso = result

        nvHU = numpy.array([CTvals[xlow,ylow,zlow], CTvals[xupp,ylow,zlow], 
                            CTvals[xupp,yupp,zlow], CTvals[xlow,yupp,zlow],
                            CTvals[xlow,ylow,zupp], CTvals[xupp,ylow,zupp], 
                            CTvals[xupp,yupp,zupp], CTvals[xlow,yupp,zupp]])
        ipc = numpy.array([xiso,yiso,ziso])
        ipData[i]['HU'] = shapeFunctionC3D8(nvHU,ipc)
    
    # Get the current working directory so we can write the results file there
    workingdir  = os.getcwd()
    outfilename = os.path.join(workingdir,outfilename+'.txt')
    file1       = open(outfilename,'w')
    print ('\nWriting HU results to file: %s' % (outfilename))
    for i in xrange(numPoints):
        ip       = ipData[i]
        instName = ip['instName']
        label    = ip['label']
        ipnum    = ip['ipnum']
        huval    = ip['HU']
        file1.write('%s %6d %1d %8.1f\n' % (instName,label,ipnum,huval))
    file1.close()

    return 0

def createPartInstanceInOdb(odb,instName,instNodes,instElems):

    import numpy

    # Create part in odb
    part = odb.Part(name=instName,embeddedSpace=THREE_D, type=DEFORMABLE_BODY)

    # Get all the nodes connected to the elements. Also convert the connectivity from node indices to labels
    nodesPerElem = 10
    nodeIndices={}; numElems=len(instElems)
    for e in xrange(numElems):
        connect = instElems[e]['connect'] 
        for i in xrange(len(connect)):
            nIndex = connect[i]
            nodeIndices[nIndex] = 1
            instElems[e]['connect'][i] = instNodes[nIndex]['label']
    
    # Get the node labels and node coordinates
    nodeIndices = numpy.array(nodeIndices.keys(),dtype=int)
    numNodes = nodeIndices.size
    nodeData = numpy.zeros(numNodes,dtype=[('label','|i4'),('coords','|f4',(3,))])
    for i in xrange(numNodes):
        nIndex = nodeIndices[i]
        nodeData[i] = instNodes[nIndex]
    nodeData.sort()

    # Add the nodes and elements to the part
    nl = numpy.ascontiguousarray(nodeData['label'])
    nc = numpy.ascontiguousarray(nodeData['coords'])
    el = numpy.ascontiguousarray(instElems['label'])
    ec = numpy.ascontiguousarray(instElems['connect'])
    part.addNodes(labels=nl,coordinates=nc)
    part.addElements(labels=el,connectivity=ec,type='C3D10M')

    # Create part instance
    odb.rootAssembly.Instance(name=instName,object=part)
    odb.save()
    
    return 0

def writeOdb(nodeData,elemData,ipData,outfilename):

    # Creates an odb from the specified assembly set / part instance. Then
    # creates a frame and a fieldoutput corresponding to the mapped HU values
    
    import numpy

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
        indices1 = numpy.where(ipData['instName']==instName)
        indices2 = numpy.where(ipData[indices1]['ipnum']==1)
        l = ipData[indices1][indices2]['label']
        d = ipData[indices1]['HU']
        l = numpy.ascontiguousarray(l)
        d = numpy.ascontiguousarray(d.reshape(d.size,1))    
        fo.addData(position=INTEGRATION_POINT,instance=i,labels=l,data=d)

    # Save and close odb
    odb.save()
    odb.close()

    return 0

def getHU(instORset, instORsetName, CTsliceDir, outfilename, resetCTOrigin, writeOdbOutput):

    """For the specified assembly set or part instance, gets the integration point
       coordinates for all the elements and maps the HU values from the corresponding
       CT stack to these points. Returns a text file that can be used in a subsequent
       finite element analysis that uses ABAQUS subroutine USDFLD to apply bone properties""" 

    result = checkInputs(instORset, instORsetName, CTsliceDir)  
    if result is None:
        print 'Error in checkInputs. Exiting'
        return
    else: 
        m,elements = result

    result = getModelData(m,elements)
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
