import unittest
import os
import sys
from setuptools import setup, find_packages

from keystroke_transcriber import __version__ as version

HERE = os.path.abspath(os.path.dirname(__file__))
README = os.path.join(HERE, "README.rst")
REQFILE = 'requirements.txt'

classifiers = [
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
]

with open(README, 'r') as f:
    long_description = f.read()

with open(REQFILE, 'r') as fh:
    dependencies = fh.readlines()

setup(
    name='keystroke_transcriber',
    version=version,
    description=('Records keypress events and converts them for replay on programmable USB HID devices'),
    long_description=long_description,
    url='https://github.com/eriknyquist/keystroke_transcriber',
    author='Erik Nyquist',
    author_email='eknyquist@gmail.com',
    license='Apache 2.0',
    install_requires=dependencies,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False
)
