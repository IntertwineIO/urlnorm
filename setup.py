#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from setuptools import setup, find_packages

project_name = 'urlnorm'

classifiers = [
    'Intended Audience :: Developers',
    'License :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: Implementation :: CPython',
    'Programming Language :: Python :: Implementation :: PyPy'
]


requirements = {
    'install': [
    ],
    'tests': [
        'pytest'
    ]
}


# Find package files
packages = find_packages()
cwd = os.path.abspath(os.path.dirname(__file__))


# Capture project metadata
engine = re.compile(r"^__(?P<key>(.*?))__ = '(?P<value>([^']*))'")
with open(os.path.join(cwd, '{}.py'.format(project_name)), 'r') as fd:
    metadata = {
        data['key']: data['value']
        for line in fd
        for data in [m.groupdict() for m in engine.finditer(line)]
    }


# Setup README documentation in RST format if pypandoc exists
with open('README.rst', 'r') as fd:
    long_description = fd.read()


setup(
    name=metadata.get('title'),
    version=metadata.get('version'),
    author=metadata.get('author'),
    author_email=metadata.get('email'),
    description=metadata.get('shortdesc'),
    long_description=long_description,
    license=metadata.get('license'),
    url=metadata.get('url'),
    download_url=metadata.get('download_url'),
    py_module=[project_name],
    package_data={},
    classifiers=classifiers,
    install_requires=requirements['install'],
    tests_require=requirements['tests'],
    extras_require=requirements,
    test_suite='tests',
    include_package_data=True,
    zip_safe=False,
)
