# -*- coding: utf-8 -*-

# Copyright (C) 2022 Michael Hogg

# This file is part of bonemapy - See LICENSE.txt for information on usage and redistribution

import numpy as np
from abaqusConstants import C3D4, C3D4H, C3D10, C3D10H, C3D10M, C3D10MH, C3D10HS

# ~~~~~~~~~~ 

class elementC3D4():
    
    def __init__(self):
        self.name       = 'C3D4'
        self.desc       = 'Linear tetrahedral element'
        self.numNodes   = 4
        self.setNumIntPnts()    
        self.setIpnums()
        self.setIpcs()
        self.evalNips()
        
    def setNumIntPnts(self):
        self.numIntPnts = 1        
        
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
                                                    
class elementC3D4H(elementC3D4):
    
    def __init__(self):
        elementC3D4.__init__(self)
        self.name = 'C3D4H' 
        self.desc = 'Linear tetrahedral element with hybrid formulation'                              
                            
# ~~~~~~~~~~        
        
class elementC3D10():

    def __init__(self):
        self.name       = 'C3D10'
        self.desc       = 'Quadratic tetrahedral element'
        self.numNodes   = 10
        self.setNumIntPnts()
        self.setIpnums()        
        self.setIpcs()
        self.evalNips()
        
    def setNumIntPnts(self):
        self.numIntPnts = 4
        
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
        self.desc = 'Quadratic tetrahedral element with modified formulation'     

    def setIpcs(self):
        alpha    = 0.1770833333
        beta     = 0.4687500000
        self.ipcs = np.array([[alpha,alpha,alpha],
                              [beta, alpha,alpha],
                              [alpha,beta, alpha],
                              [alpha,alpha,beta ]])
                                                  
# ~~~~~~~~~~                              
                                                    
class elementC3D10H(elementC3D10):
    
    def __init__(self):
        elementC3D10.__init__(self)
        self.name = 'C3D10H' 
        self.desc = 'Quadratic tetrahedral element with hybrid formulation'                                                       
                                                                                                                                  
# ~~~~~~~~~~                              
                                                       
class elementC3D10MH(elementC3D10M):
    
    def __init__(self):
        elementC3D10M.__init__(self)
        self.name = 'C3D10MH' 
        self.desc = 'Quadratic tetrahedral element with modified hybrid formulation'                                 

# ~~~~~~~~~~     

class elementC3D10HS(elementC3D10):
    
    def __init__(self):
        elementC3D10.__init__(self)
        self.name = 'C3D10HS' 
        self.desc = 'Quadratic tetrahedral element for improved surface stress visualization'     

    def setNumIntPnts(self):
        self.numIntPnts = 11

    def setIpcs(self):
        self.ipcs = np.array([[ 0.00, 0.00, 0.00],
                              [ 1.00, 0.00, 0.00],
                              [ 0.00, 1.00, 0.00],
                              [ 0.00, 0.00, 1.00],
                              [ 0.50, 0.00, 0.00],
                              [ 0.50, 0.50, 0.00],
                              [ 0.00, 0.50, 0.00],
                              [ 0.00, 0.00, 0.50],
                              [ 0.50, 0.00, 0.50],
                              [ 0.00, 0.50, 0.50],
                              [ 0.25, 0.25, 0.25]])

# ~~~~~~~~~~         

# Supported element types
seTypes = {}
seTypes[C3D4]    = elementC3D4
seTypes[C3D4H]   = elementC3D4H
seTypes[C3D10]   = elementC3D10
seTypes[C3D10H]  = elementC3D10H
seTypes[C3D10M]  = elementC3D10M
seTypes[C3D10MH] = elementC3D10MH
seTypes[C3D10HS] = elementC3D10HS
