#!/usr/bin/env python3.8

from setuptools import *

setup(
    name = 'ton',
    version = '0.1',
    packages = find_namespace_packages(where="src"),
    install_requires=[
        'fire==0.2.1',
        'pip==19.3.1',
        'pygame==2.0.0.dev6',
        'numpy==1.18.1'
    ],
    package_data={
        'ton': ['assets/**.png', 'assets/*.ttf']
    },
    package_dir = {'': 'src'},
    entry_points = {
        'console_scripts': [
            'ton = ton.main:main'
        ]
    }
)
