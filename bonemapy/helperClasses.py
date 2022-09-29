# -*- coding: utf-8 -*-

# Copyright (C) 2022 Michael Hogg

# This file is part of bonemapy - See LICENSE.txt for information on usage and redistribution

import numpy as np

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
        
    def interp1D(self,x,xc):
        xh = x.searchsorted(xc)
        xl = xh-1               
        xiso = (xc-x[xl])/(x[xh]-x[xl])
        return xl,xh,xiso                   
        
    def interp(self,xc,yc,zc):
        xl,xh,t = self.interp1D(self.x,xc)
        yl,yh,u = self.interp1D(self.y,yc)
        zl,zh,v = self.interp1D(self.z,zc)
        self.nv[:] = self.f[xl:xh+1,yl:yh+1,zl:zh+1].flatten()   
        self.evalN(t,u,v)
        return np.dot(self.N,self.nv)
        
    def __call__(self,xc,yc,zc):
        return self.interp(xc,yc,zc)
        
# ~~~~~~~~~~
