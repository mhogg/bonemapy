
class elementC3D10():
    def __init__(self):
        self.name       = 'C3D10'
        self.desc       = 'Quadratic tetrahedral element'
        self.numNodes   = 10
        self.numIntPnts = 4
        self.N          = array(self.numNodes)
        self.setIpcs()
    def setIpcs(self):
        alpha     = 0.1770833333
        beta      = 0.4687500000
        self.ipcs = numpy.array([[alpha,alpha,alpha],
                                 [beta, alpha,alpha],
                                 [alpha,beta, alpha],
                                 [alpha,alpha,beta ]])
    def shapeFunctionMatrix(self,ipc):
        g,h,r=ipc
        self.N[0] = (2.0*(1.0-g-h-r)-1.0)*(1.0-g-h-r)
        self.N[1] = (2.0*g-1.0)*g
        self.N[2] = (2.0*h-1.0)*h
        self.N[3] = (2.0*r-1.0)*r
        self.N[4] = 4.0*(1.0-g-h-r)*g
        self.N[5] = 4.0*g*h
        self.N[6] = 4.0*(1.0-g-h-r)*h
        self.N[7] = 4.0*(1.0-g-h-r)*r
        self.N[8] = 4.0*g*r
        self.N[9] = 4.0*h*r
    def interpFunc(self,nv):
        return np.dot(self.N,nv)
        
class elementC3D4():
    def __init__(self):
        self.name       = 'C3D4'
        self.desc       = 'Linear tetrahedral element'
        self.numNodes   = 4
        self.numIntPnts = 1
        self.N          = np.array(self.numNodes)
        self.setIpcs()
    def setIpcs(self):
        alpha = 0.33333 # CHECK THESE VALUES
        beta  = 0.33333 # CHECK THESE VALUES
        self.ipcs = np.array([[],[],[]])
    def shapeFuncMatrix(self,ipc):
        g,h,r=ipc
        self.N[0] = (1.0-g-h-r)
        self.N[1] = g
        self.N[2] = h
        self.N[3] = r
    def interpFunc(self,nv):
        return np.dot(self.N,nv)         
    


    
    
        
    