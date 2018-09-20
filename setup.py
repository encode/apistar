#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys

from setuptools import setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


def get_long_description(long_description_file):
    """
    Read long description from file.
    """
    with open(long_description_file, encoding='utf-8') as f:
        long_description = f.read()

    return long_description



version = get_version('apistar')


setup(
    name='apistar',
    version=version,
    url='https://docs.apistar.com/',
    license='BSD',
    description='API documentation, validation, mocking, and clients.',
    long_description=get_long_description('README.md'),
    long_description_content_type='text/markdown',
    author='Tom Christie',
    author_email='tom@tomchristie.com',
    packages=get_packages('apistar'),
    package_data=get_package_data('apistar'),
    install_requires=[
        'click',
        'jinja2',
        'requests',
        'pyyaml',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    entry_points={
        'console_scripts': [
            'apistar=apistar:cli'
        ],
    },
)
