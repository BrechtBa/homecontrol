#!/usr/bin/env/ python
from setuptools import setup, find_packages
import os

# retrieve the version
try:
    versionfile = os.path.join('knxpy', '__version__.py')
    f = open( versionfile, 'r')
    content = f.readline()
    splitcontent = content.split('\'')
    version = splitcontent[1]
    f.close()
except:
    raise Exception('Could not determine the version from knxpy/__version__.py')


# run the setup command
setup(
    name='knxpy',
    version=version,
    license='MIT',
    description='A simple connector to a KNX bus',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    url='http://github.com/BrechtBa/knxpy',
    author='Daniel Matuschek, Brecht Baeten',
    author_email='',
    packages=find_packages(),
    install_requires=[],
    classifiers=['Programming Language :: Python :: 3.5'],
)
