# -*- coding: utf-8 -*-
"""
Created on Wed Apr 20 18:18:29 2016

@author: kaufmana
"""

import os
from setuptools import setup, find_packages

# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# get version number 
exec( open('HARK/version.py').read()) 

print(__file__)

setup(
    name = "HARK",
    version = __version__,
    author = "Consumer Financial Protection Bureau",
    author_email = "david.low@cfpb.gov",
    description = ("Heterogeneous Agent Resources and toolKit "),
    license = "Apache Software License",
    keywords = "...",
    url = "https://github.com/dclow",
    packages=find_packages(),
    install_requires = [
    'joblib',
    'allpairs'
    ],
    long_description=read('README.txt'),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
)
