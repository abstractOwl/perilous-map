#!/usr/bin/env python3

from setuptools import setup

setup(
        name='Perilous Map',
        version='1.0',
        packages=['perilous_map'],
        url='https://perilous-map.herokuapp.com',
        install_requires=[
            'APScheduler == 3.9.1',
            'Flask == 2.2.2',
            'gunicorn == 20.1.0',
            'python-dateutil == 2.8.2',
            'redis == 4.3.4',
            'requests == 2.28.1'
        ],
        extras_require={
            'dev': [
                'flake8 == 5.0.4'
            ]
        }
)
