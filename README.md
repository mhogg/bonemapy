#bonemapy

**An ABAQUS plug-in to map bone properties from CT scans to 3D finite element bone/implant models. This is typically used for applying heterogeneous material properties to the 
bone model.**

**Developed together with [pyvXRAY](https://github.com/mhogg/pyvxray) and [BMDanalyse](https://github.com/mhogg/BMDanalyse) to provide tools for preparation and post-processing 
of bone/implant computer models.**

Copyright 2013, Michael Hogg (michael.christopher.hogg@gmail.com)

MIT license - See LICENSE.txt for details on usage and redistribution

## Requirements

### Software requirements

* ABAQUS  >= 6.11
* pydicom >= 0.9.7

**NOTES:**

1.  ABAQUS is a commerical software package and requires a license from [Simulia](http://www.3ds.com/products-services/simulia/overview/)
2.  The authors of bonemapy are not associated with ABAQUS/Simulia 
3.  bonemapy uses both Python and numpy, which are built in to ABAQUS. All of the last few releases of ABAQUS (v6.11 - v6.13) use Python 2.6.x and numpy 1.4.x

### Model setup requirements

* The model must contain only tetrahedral elements. All 3D stress tetrahedral elements are supported (ABAQUS element types C3D4, C3D4H, C3D10, C3D10H, C3D10I, C3D10M, and C3D10MH).
* Requires that the model coordinates match the CT scan coordinates e.g. the bone model cannot be shifted from its original position

### CT stack requirements ###

* All CT slices should be located in the same directory. This directory must not contain any other file types or slices belonging to other stacks.  
* It is assumed that all slices have the same (x,y) coordinates at the slice origin

## Installation

####1. Installation of bonemapy plug-in  

bonemapy is an ABAQUS plug-in. ABAQUS plug-ins may be installed in several ways. Only one of the ways is discussed here. For other options the user is referred to the ABAQUS 
user manuals. 

The recommended method is:

* Download the zip file of the latest bonemapy release
* Unzip the folder to a convenient location. This folder will typically be called `bonemapy-x.x.x`
* Copy this folder to the `abaqus_plugins` directory within your ABAQUS installation. This is in a different location depending on the ABAQUS version. 
  For the default ABAQUS installation location, possible locations are:

    v6.11-x: `C:\SIMULIA\Abaqus\6.11-x\abaqus_plugins`

    v6.12-x: `C:\SIMULIA\Abaqus\6.12-x\code\python\lib\abaqus_plugins`

    v6.13-x: `C:\SIMULIA\Abaqus\6.13-x\code\python\lib\abaqus_plugins`

####2. Installation of bonemapy requirements

The ABAQUS GUI is built on Python, and has its own Python installation. This Python installation is not the typically Python setup, so some guidance is provided here on how 
to install bonemapy's dependencies.

Currently bonemapy has only one requirement that is not built into ABAQUS, which is pydicom. The easiest way of installating this is to:

* Download the zip file of the latest pydicom source release from the [pydicom project site](https://code.google.com/p/pydicom/) or [PyPi](https://pypi.python.org/pypi/pydicom/)
* Unzip this to a convenient location
* Open a command prompt and browse to folder `pydicom-x.x.x` (containing file setup.py)
* At the command prompt enter:

        abaqus python setup.py install

## Usage

* Open the model within ABAQUS/CAE (not ABAQUS/Viewer)
* Launch the bonemapy GUI by going to the Menubar at the top of the ABAQUS/CAE window and selecting:

        Plug-ins --> bonemapy --> Map HU from CT

* Complete the required inputs in the GUI, which include:

  + The model and set names of the bone region
  + The location of the directory containing the CT stack 
  + The base name of all output files

* Click OK to run bonemapy
* Look at the Message Area at the bottom of the ABAQUS/CAE window for messages. On completion 'Finished' will be shown.

## Output

bonemapy produces the following output:

1. A text file containing the HU values. This has a format similar to:

        instanceName elementNumber IntegrationPointNumber HUvalue

  This file is space delimited so it can easily be read by Fortran code such as that used by ABAQUS user subroutines USDFLD / UMAT for applying mechanical properties to models. 

2. An odb file of the selected bone region with a fieldoutput of the mapped HU values. This can be used for visually checking that bonemapy has mapped the HU values correctly.

## Help

If help is required, please open an Issue or a Pull Request on Github. 
