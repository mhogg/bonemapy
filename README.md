#bonemapy

**An ABAQUS plug-in to map bone properties from CT scans to 3D finite element bone/implant models. This is typically used for applying non homogenous material properties to the bone model**

Copyright 2013, Michael Hogg (michael.christopher.hogg@gmail.com)

MIT license - See LICENSE.txt for details on usage and distribution

## Requirements

### Software requirements

* ABAQUS  >= 6.11
* pydicom >  0.9.7

**NOTES:**

1.  ABAQUS is a commerical software package and requires a license from [Simulia](http://www.3ds.com/products-services/simulia/overview/)
2.  The authors of bonemapy are not associated with ABAQUS/Simulia 
3.  bonemapy uses both Python and numpy, which are built in to ABAQUS. All of the last few releases of ABAQUS (v6.11-v6.13) use Python 2.6 and numpy 1.4

### Model setup requirements

* The model must contain only quadrilateral tetrahedral elements (ABAQUS element C3D10). Linear tetrahedral elements (type C3D4) are currently unsupported.
* Requires that the model coordinates match the CT scan coordinates e.g. the bone model cannot be shifted from its original position