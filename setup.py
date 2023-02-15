"""Setup for subitize."""

from setuptools import setup

setup(
    name='subitize',
    version='',

    description='',
    long_description='',
    license='',

    install_requires=[
        'Flask==1.0.3',
        'Jinja2==2.11.3',
        'SQLAlchemy==1.3.4',
        'Werkzeug==2.2.3',
        'beautifulsoup4==4.7.1',
        'gunicorn==19.9.0',
        'requests==2.22.0',
        'sqlparse==0.3.0',
    ],

    author='Justin Li',
    author_email='justinnhli@oxy.edu',
    url='https://github.com/justinnhli/subitize',
)
