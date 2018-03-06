"""
Source build and installation script.
"""

from os import path, sep, walk
from pip.download import PipSession
from pip.req import parse_requirements
from setuptools import setup, find_packages


def extract_requirements(filename):
    return [
        str(r.req)
        for r in parse_requirements(filename, session=PipSession)
    ]


def find_package_data(source, strip=''):
    pkg_data = []
    for root, dirs, files in walk(source):
        pkg_data += map(
            lambda f: path.join(root.replace(strip, '').lstrip(sep), f),
            files
        )
    return pkg_data


base_dir = path.dirname(__file__)

with open(path.join(base_dir, 'README.rst')) as f:
    long_description = f.read()

install_requires = extract_requirements('requirements.txt')

setup(
    name='python-cafe',
    version='0.14.3',
    description='Python Cafe: A convenience package providing various '
                'building blocks enabling pythonic patterns.',
    long_description=long_description,
    license='APLv2',
    url='https://github.com/abn/python-cafe',
    author='Arun Babu Neelicattu, Josha Inglis, Betsy Alpert',
    author_email='arun.neelicattu@gmail.com, '
                 'joshainglis@gmail.com, '
                 'lizbeth.alpert@gmail.com',
    classifiers=[
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'cafe': find_package_data('cafe/resources', 'cafe'),
    },
    install_requires=install_requires,
)
