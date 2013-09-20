# -*- coding: utf-8 -*-

# Copyright (C) 2013 Michael Hogg

# This file is part of bonemapy - See LICENSE.txt for information on usage and redistribution

import numpy as np
from abaqusConstants import C3D4, C3D10, C3D10M 

# ~~~~~~~~~~ 

class elementC3D4():
    
    def __init__(self):
        self.name       = 'C3D4'
        self.desc       = 'Linear tetrahedral element'
        self.numNodes   = 4
        self.numIntPnts = 1     
        self.setIpnums()
        self.setIpcs()
        self.evalNips()
        
    def setIpnums(self):
        self.ipnums = np.array([i+1 for i in range(self.numIntPnts)]) 
    
    def setIpcs(self):
        g = h = r = 0.25
        self.ipcs = np.array([[g,h,r]])
        
    def getN(self,ipc):
        g,h,r = ipc
        N1 = (1.0-g-h-r)
        N2 = g
        N3 = h
        N4 = r
        return np.array([N1,N2,N3,N4])
        
    def evalNips(self):       
        self.Nips = np.array([self.getN(ip) for ip in self.ipcs])
    
    def interp(self,N,nv):
        return np.dot(N,nv) 
      
    def getIntPointValues(self,nv):
        ipv = [self.interp(N,nv) for N in self.Nips] 
        return ipv[0]
        
    def setNodeCoords(self):
        self.nc = np.array([[ 0.0, 0.0, 0.0],
                            [ 1.0, 0.0, 0.0],
                            [ 0.0, 1.0, 0.0],
                            [ 0.0, 0.0, 1.0]]) 
                            
# ~~~~~~~~~~        
        
class elementC3D10():

    def __init__(self):
        self.name       = 'C3D10'
        self.desc       = 'Quadratic tetrahedral element'
        self.numNodes   = 10
        self.numIntPnts = 4
        self.setIpnums()        
        self.setIpcs()
        self.evalNips()
        
    def setIpnums(self):
        self.ipnums = np.array([i+1 for i in range(self.numIntPnts)])         
        
    def setIpcs(self):
        alpha     = 0.1381966
        beta      = 0.5854102
        self.ipcs = np.array([[alpha,alpha,alpha],
                              [beta, alpha,alpha],
                              [alpha,beta, alpha],
                              [alpha,alpha,beta ]])
                              
    def getN(self,ipc):
        g,h,r = ipc
        N1  = (2.0*(1.0-g-h-r)-1.0)*(1.0-g-h-r)
        N2  = (2.0*g-1.0)*g
        N3  = (2.0*h-1.0)*h
        N4  = (2.0*r-1.0)*r
        N5  = 4.0*(1.0-g-h-r)*g
        N6  = 4.0*g*h
        N7  = 4.0*(1.0-g-h-r)*h
        N8  = 4.0*(1.0-g-h-r)*r
        N9  = 4.0*g*r
        N10 = 4.0*h*r
        return np.array([N1,N2,N3,N4,N5,N6,N7,N8,N9,N10])
        
    def evalNips(self):        
        self.Nips = np.array([self.getN(ip) for ip in self.ipcs])
    
    def interp(self,N,nv):
        return np.dot(N,nv) 
      
    def getIntPointValues(self,nv):   
        ipv = [self.interp(N,nv) for N in self.Nips] 
        return np.array(ipv)
        
    def setNodeCoords(self):
        self.nc = np.array([[ 0.0, 0.0, 0.0],
                            [ 1.0, 0.0, 0.0],
                            [ 0.0, 1.0, 0.0],
                            [ 0.0, 0.0, 1.0],
                            [ 0.5, 0.0, 0.0],
                            [ 0.5, 0.5, 0.0],
                            [ 0.0, 0.5, 0.0],
                            [ 0.0, 0.0, 0.5],
                            [ 0.5, 0.0, 0.5],
                            [ 0.0, 0.5, 0.5]])
                            
# ~~~~~~~~~~                             

class elementC3D10M(elementC3D10):
    
    def __init__(self):
        elementC3D10.__init__(self)
        self.name = 'C3D10M' 
        self.desc = 'Modified quadratic tetrahedral element'

    def setIpcs(self):
        alpha    = 0.1770833333
        beta     = 0.4687500000
        self.ipcs = np.array([[alpha,alpha,alpha],
                              [beta, alpha,alpha],
                              [alpha,beta, alpha],
                              [alpha,alpha,beta ]])
       
# ~~~~~~~~~~         
        
class triLinearInterp():
    
    """ Class for trilinear interpolation"""
    
    def __init__(self,x,y,z,f):
        self.x  = x
        self.y  = y
        self.z  = z
        self.f  = f
        self.N  = np.zeros(8,dtype=float)
        self.nv = np.zeros(8,dtype=float)
        
    def evalN(self,t,u,v):
        self.N[0] = (1.0-t)*(1.0-u)*(1.0-v)
        self.N[1] = t*(1.0-u)*(1.0-v)
        self.N[2] = (1.0-t)*u*(1.0-v)
        self.N[3] = t*u*(1.0-v)
        self.N[4] = (1.0-t)*(1.0-u)*v
        self.N[5] = t*(1.0-u)*v
        self.N[6] = (1.0-t)*u*v
        self.N[7] = t*u*v 
        
    def findPointData(self,x,xc):
        xh = x.searchsorted(xc)
        xl = xh-1               
        xiso = (xc-x[xl])/(x[xh]-x[xl])
        return xl,xh,xiso                   
        
    def interp(self,xc,yc,zc):
        xl,xh,t = self.findPointData(self.x,xc)
        yl,yh,u = self.findPointData(self.y,yc)
        zl,zh,v = self.findPointData(self.z,zc)
        self.nv[:] = self.f[xl:xh+1,yl:yh+1,zl:zh+1].flatten()   
        self.evalN(t,u,v)
        return np.dot(self.N,self.nv)
        
    def __call__(self,xc,yc,zc):
        return self.interp(xc,yc,zc)
        
# ~~~~~~~~~~         

# Supported element types
seTypes = {C3D4:elementC3D4, C3D10:elementC3D10, C3D10M:elementC3D10M}     

