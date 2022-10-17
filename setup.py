# -*- coding: utf-8 -*-

# Copyright (C) 2022 Michael Hogg

# This file is part of bonemapy - See LICENSE.txt for information on usage and redistribution

import bonemapy
from distutils.core import setup
from os import path

# Get current path
here = path.abspath(path.dirname(__file__))

# Function to open the readme file
def readme():
    with open(path.join(here, 'README.md')) as f:
        return f.read()
long_description = readme()

setup(
    name = 'bonemapy',
    version = bonemapy.__version__,
    description = 'An ABAQUS plug-in to map bone properties from CT scans to 3D finite element bone/implant models',
    long_description = long_description,
    long_description_content_type='text/markdown',
    license = 'MIT license',
    keywords = ["ABAQUS", "plug-in","CT","finite","element","bone","properties","python"],
    author = 'Michael Hogg',
    author_email = 'michael.christopher.hogg@gmail.com',
    packages=['', 'bonemapy'],
    package_data = {'': ['README.md','LICENSE.txt','examples\*'], 'bonemapy': ['icons\*']},
    include_package_data = True,
    url = "https://github.com/mhogg/bonemapy",
    download_url = "https://github.com/mhogg/bonemapy/releases",
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Environment :: Other Environment",
        "Environment :: Plugins",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Visualization",
        ],
)
