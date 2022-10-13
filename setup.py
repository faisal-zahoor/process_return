# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in process_return/__init__.py
from process_return import __version__ as version

setup(
	name='process_return',
	version=version,
	description='Process Return',
	author='AK',
	author_email='ajadhao753@gmail.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
