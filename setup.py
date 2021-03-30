# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import re
from setuptools import setup

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Regex the file directly as we can not import it due to
# src/diem/__init__.py importing from external repo not in requirements.txt
with open(os.path.join(this_directory, "src", "diem", "__VERSION__.py"), encoding='utf-8') as f:
    version = re.search(r'VERSION = "(.*?)"', f.read(), re.MULTILINE).group(1)

setup(
    name="diem",
    version=version,
    description="The Python Client SDK for Diem",
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="Apache-2.0",
    url="https://github.com/diem/client-sdk-python",
    author="The Diem Core Contributors",
    author_email="developers@diem.com",
    py_modules=["diem.testing.cli"],
    entry_points='''
        [console_scripts]
        dmw=diem.testing.cli:main
    ''',
    python_requires=">=3.7", # requires dataclasses
    packages=["diem"],
    # package_data={"": ["src/diem/jsonrpc/*.pyi"]},
    package_dir={"": "src"},
    include_package_data=True,  # see MANIFEST.in
    zip_safe=True,
    install_requires=["requests>=2.20.0", "cryptography>=2.8", "numpy>=1.18", "protobuf>=3.12.4"],
    extras_require={
        "all": ["falcon>=2.0.0", "waitress>=1.4.4", "pytest>=6.2.1", "click>=7.1"]
    },
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ]
)
