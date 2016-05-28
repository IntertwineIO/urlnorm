#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from setuptools import setup, find_packages

setup_kwds = {}

setup_kwds['classifiers'] = [
    'Programming Language :: Python',
    'Natural Language :: English',
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: Implementation :: CPython',
    'Programming Language :: Python :: Implementation :: PyPy',
    'Private :: Do Not Upload',  # This prevents accidental uploads to pypi
]


requirements = {
    # Debug probably is only necessary for development environments
    'debug': [
        'pdbpp',
        'ipython'
    ],

    # Deploy identifies upgrades to local system prior to deployment
    'deploy': [
        'ansible >= 2',
        'devpi-client',
        'devpi-common',
    ],

    # Docs should probably only be necessary in Continuous Integration
    'docs': [
        'coverage',
        'sphinx',
        'sphinx_rtd_theme',
        'sphinxcontrib-napoleon',
    ],

    # Examples probably is only necessary for development environments
    'examples': [
        'docopt'
    ],

    # Monitoring identifies upgrades to remote system mostly for nagios
    'monitoring': [
        'inotify',
        'psutil',
        'graphitesend',
    ],

    # Requirements is the basic needs for this package
    'requirements': [
    ],

    # Required for setup to run
    'setup': [
        'pip',
        'setuptools >= 25',
        'pytest-runner'
    ],

    # Tests are needed in a local and CI environments for py.test and tox
    # Note:  To run the tox environment for docs, docs must also be installed
    'tests': [
        'detox',
        'pep8',
        'pdbpp',
        'pytest',
        'pytest-cov',
        'pytest-flake8',
        'pytest-html',
        'pytest-xdist',
        'tox',
    ],
}
setup_kwds['install_requires'] = requirements.get('requirements') or []
setup_kwds['test_requires'] = requirements.get('tests') or []

# Developers should probably run:  pip install .[dev]
requirements['dev'] = [
    r for k, reqs in requirements.items() for r in reqs
    if k not in ['requirements']
]

# All is for usability:  pip install .[all]
requirements['all'] = [
    r for k, reqs in requirements.items() for r in reqs
]

# Build up a nice set of installation endpoints
setup_kwds['extras_requires'] = {
    k: v for k, v in requirements.items() if k != 'requirements'
}

# Find package files
packages = find_packages()
cwd = os.path.abspath(os.path.dirname(__file__))

# Search for __init__.py or search in top rep for python file
file_to_find = '__init__.py' if packages else None

# Capture project metadata
engine = re.compile(r"^(?P<dunder_key>__(?P<key>(.*?))__) = (?P<value>([^\n]*))")
exact_matches = [
    'build', 'deploy', 'dist', 'docs', 'examples', 'provision', 'scripts', 'tests',
]
partial_matches = [
    'venv', '.egg',
]

# Attempt to find the right __init__.py or py_module file within the project structure.
#  Should be easy to find, right?  :)
metadata = {}
for root, folders, files in os.walk(cwd):
    depth = root[len(cwd) + len(os.path.sep):].count(os.path.sep)
    if packages and depth > 2:  # Don't dig too deep
        continue
    elif not packages and depth > 1:  # Without packages, only search in root
        continue
    folders[:] = [
        f for f in folders
        if f not in exact_matches  # ignore a set of common folders
        if not f.startswith('.')  # ignore anything that is a hidden folder
        if not any(p in f for p in partial_matches)  # ignore specific matches
    ]
    for filename in files:
        if file_to_find and filename != file_to_find:
            continue
        elif not filename.endswith('.py'):
            continue
        filepath = os.path.join(root, filename)
        with open(filepath, 'r') as fd:
            print('found: {}'.format(filename))
            for line in fd:
                for data in [m.groupdict() for m in engine.finditer(line)]:
                    # Would prefer not to use eval, but cannot think of
                    #  a way to support expressions without eval
                    metadata[data['key']] = eval(data['value'], metadata)
                    # Add dunders for eval context
                    metadata[data['dunder_key']] = eval(data['value'], metadata)
        if metadata:
            break
    if metadata:
        break

# Provide support for meaningful docstrings
metadata['doc'] = metadata.pop('__doc__', metadata.get('doc', ''))

# Strip out dunders to keep things lean
metadata = {k: v for k, v in metadata.items() if not k.startswith('__') and not k.endswith('__')}

# Add metadata fields to setup
field_defaults = {
    'author': None,
    'author_email': None,
    'name': metadata.get('title'),
    'url': None,
}
for field, default in field_defaults.items():
    # Only add field if it's available to add
    if field in metadata and default is not None:
        setup_kwds[field] = metadata[field]
    # Only add fields that have actual values
    elif default:
        setup_kwds[field] = default

setup_kwds['version'] = metadata.get('version_str') or metadata.get('version') or (0, 0, 0)

# Read License for setup
lic = metadata.get('license')
lic_file = 'LICENSE.txt'
if not lic and os.path.exists(lic_file):
    with open(os.path.join(cwd, lic_file), 'rb') as fd:
        lic = fd.read()
        # Decode didn't chain with read
        lic = lic.decode('utf-8')
setup_kwds['license'] = lic

# Create a long description with history
long_history = ''
for filename in ['README.rst', 'CHANGES.rst']:
    if os.path.exists(filename):
        with open(filename, 'r') as fd:
            long_history += fd.read()
            long_history += '\n\n'
long_history = long_history.rstrip('\n') or metadata.get('shortdesc')
setup_kwds['long_description'] = metadata.get('doc', long_history)


if not packages:
    setup_kwds['py_module'] = [metadata.get('title')]
else:
    setup_kwds['packages'] = packages

setup_kwds['zip_safe'] = False

setup(**setup_kwds)
