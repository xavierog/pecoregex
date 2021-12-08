#!/usr/bin/env python3

from setuptools import setup

with open('README.md', 'r') as readme:
	long_description = readme.read()

setup(
	name='pecoregex',
	version='1.1.0',
	description='Evaluate Perl-Compatible Regular Expressions',
	long_description=long_description,
	long_description_content_type='text/markdown',
	author='Xavier G.',
	author_email='xavier.pecoregex@kindwolf.org',
	url='https://github.com/xavierog/pecoregex',
	packages=['pecoregex'],
	classifiers=[
		'License :: OSI Approved :: BSD License',
		'Operating System :: POSIX :: Linux', # pecoregex was never tested outside Linux
		'Programming Language :: Python :: 3 :: Only', # Implemented and tested with Python 3.6; unlikely to run with Python 2.x
		'Topic :: Text Processing',
	],
	license='BSD',
	keywords=['regex', 'pcre', 'ctypes', 'cli', 'json', 'yaml'],
	package_dir={'': 'src'},
	install_requires=['pyyaml'],
	entry_points={
		'console_scripts': [
			'pecoregex = pecoregex.cli:run_cli'
		]
	},

)
