
import numpy as np

class elementC3D4():
    
    def __init__(self):
        self.name       = 'C3D4'
        self.desc       = 'Linear tetrahedral element'
        self.numNodes   = 4
        self.numIntPnts = 1
        self.Nips       = None        
        self.setIpcs()
        self.evalNips()
        
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
        
class elementC3D10():

    def __init__(self):
        self.name       = 'C3D10'
        self.desc       = 'Quadratic tetrahedral element'
        self.numNodes   = 10
        self.numIntPnts = 4
        self.Nips       = None
        self.setIpcs()
        self.evalNips()
        
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
                                                         
class triLinearInterp():
    def __init__(self):
        self.N = np.zeros(8,dtype=float)
    def evalN(self,ipc):
        g,h,r=ipc
        self.N[0] = (1-g)*(1-h)*(1-r)
        self.N[1] = (1+g)*(1-h)*(1-r)
        self.N[2] = (1+g)*(1+h)*(1-r)
        self.N[3] = (1-g)*(1+h)*(1-r)
        self.N[4] = (1-g)*(1-h)*(1+r)
        self.N[5] = (1+g)*(1-h)*(1+r)
        self.N[6] = (1+g)*(1+h)*(1+r)
        self.N[7] = (1-g)*(1+h)*(1+r)
        self.N /= 8.0
    def interp(self,nv,ipc):
        self.evalN(ipc)
        return np.dot(nv,self.N)
        