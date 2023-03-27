"""Setup for subitize."""

from setuptools import setup

with open('requirements.txt', encoding='utf-8') as fd:
    requirements = fd.read().splitlines()


setup(
    name='subitize',
    version='',

    description='',
    long_description='',
    license='',

    install_requires=requirements,

    author='Justin Li',
    author_email='justinnhli@oxy.edu',
    url='https://github.com/justinnhli/subitize',
)
