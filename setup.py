# -*- coding: utf-8 -*-

# Copyright (C) 2013 Michael Hogg

# This file is part of bonemapy - See LICENSE.txt for information on usage and redistribution

import bonemapy
from distutils.core import setup
   
setup(
    name = 'bonemapy',
    version = bonemapy.__version__,
    description = 'An ABAQUS plug-in to map bone properties from CT scans to 3D finite element bone/implant models',
    license = 'MIT license',
    keywords = ["ABAQUS", "plug-in","CT","finite","element","bone","properties","python"],    
    author = 'Michael Hogg',
    author_email = 'michael.christopher.hogg@gmail.com',
    url = "https://github.com/mhogg/bonemapy",
    download_url = "https://github.com/mhogg/bonemapy/releases", 
    classifiers = [
        "Programming Language :: Python",                                       
        "Programming Language :: Python :: 2",             
        "Programming Language :: Python :: 2.6",                                                    
        "Development Status :: 4 - Beta",                                  
        "Environment :: Other Environment", 
        "Environment :: Plugins", 
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",   
        "License :: OSI Approved :: MIT License", 
        "Operating System :: OS Independent",     
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Visualization",
        ],
    long_description = """

bonemapy is an ABAQUS plug-in that is used to extract bone density, or Hounsfield Unit (HU) values, from CT scans. The bone density can then be used to setup heterogeneous 
material properties for a 3D finite element bone/implant model.

The HU values are extracted at the element integration points. Tri-linear interpolation is used to calculate the HU values at the location of the integration points.

bonemapy produces a text file containing the HU values that is formatted so that it can easily be read using ABAQUS user subroutines that are required to apply the bone properties. An
ABAQUS odb file is also created containing a fieldoutput representing HU so that the user can quickly visualise the mapped HU values. 

""",
)
