#!/usr/bin/env python3

from distutils.core import setup

setup(
        name='Perilous Map',
        version='1.0',
        packages=['perilous_map'],
        url='https://perilous-map.herokuapp.com',
        install_requires=[
            'APScheduler',
            'Flask',
            'gunicorn',
            'python-dateutil',
            'redis',
            'requests'
        ],
        extras_require={
            'dev': [
                'flake8'
            ]
        }
)
