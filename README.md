# bonemapy

**An ABAQUS plug-in to map bone properties from CT scans to 3D finite element bone/implant models. This is typically used for applying heterogeneous material properties to the 
bone model.**

**Developed together with [pyvXRAY](https://github.com/mhogg/pyvxray) and [BMDanalyse](https://github.com/mhogg/BMDanalyse) to provide tools for preparation and post-processing 
of bone/implant computer models.**

</br>

Copyright 2022, Michael Hogg (michael.christopher.hogg@gmail.com)

MIT license - See LICENSE.txt for details on usage and redistribution

</br>

## Requirements

Please note that:

1. ABAQUS is a commerical software package and requires a license from [Simulia](http://www.3ds.com/products-services/simulia/overview/)
2. The authors of bonemapy are not associated with ABAQUS/Simulia 
3. bonemapy uses both Python and numpy, which are built in to ABAQUS
4. ABAQUS still uses Python 2.7 which is not longer supported by the Python community. When installing Python libraries, from PyPi for example, the user must be careful to install only versions of packages that still support Python 2.7

### Software requirements

* ABAQUS  >= 2021
* setuptools == 41.1.0
* pip == 19.2.3
* pydicom == 1.4.2

### Model setup requirements

* The model must contain only tetrahedral elements. All 3D stress tetrahedral elements are supported (ABAQUS element types C3D4, C3D4H, C3D10, C3D10H, C3D10M, and C3D10MH)

* Requires that the model coordinates match the CT scan coordinates e.g. the bone model cannot be shifted from its original position

### CT stack requirements ###

* All CT slices should be located in the same directory. This directory must not contain any other file types or slices belonging to other stacks

* It is assumed that all slices have the same (x,y) coordinates at the slice origin

</br>

## Installation

### a. Install setuptools and pip

  To facilitate the installation of 3rd party libraries, the first thing to do is to install `setuptools` and `pip`. Choose the versions that were released around July 2019, which corresponds to the build date of the Python in Abaqus 2021.

  1. Download `setuptools` and `pip` from [PyPi](pypi.org)

  The files to download are:

  * setuptools-41.1.0.zip
  * pip-19.2.3.tar.gz

  2. Unpack these files and browse to the directory where `setup.py` is located, first for setuptools and then for pip.

    # Browse to folder 'setuptools-41.1.0' and install via
    >>> abaqus python setup.py install

    # Browse to folder 'pip-19.2.3' and install via
    >>> abaqus python setup.py install

  3. Check that `setuptools` and `pip` have been installed into the Abaqus python installation using the command below. If installed, you should be able to see it in the list printed to the screen:

    >>> abaqus python -m pip list

### b. Install pydicom

  Now that pip is installed, you can install pydicom using the command below. Note that version 1.4.2, not the latest (2.3.0 at the time of writing) is installed to be compatible with Python 2.7.

    >>> abaqus python -m pip install pydicom==1.4.2

### c. Installation of bonemapy plug-in  

bonemapy is an ABAQUS plug-in. To install any ABAQUS plug-in, the plug-in folder must be copied to one of the ABAQUS plug-in directories, of which there are several options. 

To install bonemapy into ABAQUS:

1. Download the latest bonemapy zip file from the [releases page](https://github.com/mhogg/bonemapy/releases)

2. Unzip the folder to a convenient location. This folder will typically be called `bonemapy-x.x.x`

3. Copy the `bonemapy` sub-folder to the `abaqus_plugins` directory within your ABAQUS installation. For Abaqus 2021 two alternative locations on Windows are:

    * `C:\SIMULIA\CAE\plugins\2021`

    * `C:\Users\user_name\abaqus_plugins`, where `user_name` should be replaced with your Windows user name

</br>

## Using bonemapy in ABAQUS/CAE

* Open the model within ABAQUS/CAE (not ABAQUS/Viewer)

* Launch the bonemapy GUI by going to the Menubar at the top of the ABAQUS/CAE window and selecting:

        Plug-ins --> bonemapy --> Map HU from CT

* Complete the required inputs in the GUI, which include:

  + The model and set names of the bone region
  + The location of the directory containing the CT stack 
  + The base name of all output files

* Click OK to run bonemapy

* Look at the Message Area at the bottom of the ABAQUS/CAE window for messages. On completion 'Finished' will be shown.

</br>

## Output

bonemapy produces the following output:

1. A text file containing the HU values. This has a format similar to:

        instanceName elementNumber IntegrationPointNumber HUvalue

  This file is space delimited so it can easily be read by Fortran code such as that used by ABAQUS user subroutines USDFLD / UMAT for applying mechanical properties to models. 

2. An odb file of the selected bone region with a fieldoutput of the mapped HU values. This can be used for visually checking that bonemapy has mapped the HU values correctly.

</br>

## Help

If help is required, please open an Issue or a Pull Request on Github. 
