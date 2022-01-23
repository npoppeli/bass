#!/usr/bin/env python3

from setuptools import setup

setup(
    name='bass',
    version='1.3.0',
    author='Nico Poppelier',
    author_email='n.poppelier@xs4all.nl',
    license='MIT',
    url='http://schier7.home.xs4all.nl/bass',
    description='Static site generator',
    long_description=
        "Bass is a static website generator. It turns a collection of "
        "content pages, assets (PNG, CSS, JS etc.) into a static website. "
        "You run it on your local computer, and it generates a directory "
        "of files that you can upload to your web server, or serve directly. ",
    download_url="http://schier7.home.xs4all.nl/bass/download",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    install_requires=[
        'chameleon>=3.0',
        'markdown2>=2.3.0',
        'pyyaml>=5.1'
    ],
    packages=['bass'],
    scripts=['script/bass'],
)
