import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'BigRig',
    version = '0.1-pre',
    license = 'BSD',
    description = 'A pure Python ECMAScript 5.1 engine.',
    long_description = read('README.rst'),
    author = 'Jeff Kistler',
    author_email = 'jeff@jeffkistler.com',
    packages = ['bigrig'],
    package_dir = {'bigrig': 'bigrig'},
    scripts = ['scripts/bigrig'],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)
