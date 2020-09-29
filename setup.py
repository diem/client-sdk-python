# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
from setuptools import setup

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="pylibra-beta", # libra-client-sdk
    version="0.5.2020092801", # bump up version for release, format 0.X.YYYYMMDDNN
    description="The Python Client SDK for Libra",
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="Apache-2.0",
    url="https://github.com/libra/libra-client-sdk-python",
    # author="Libra Open Source",
    python_requires=">=3.7", # requires dataclasses
    packages=["libra"],
    include_package_data=True,  # see MANIFEST.in
    zip_safe=True,
    install_requires=["requests>=2.19", "cryptography>=3.1", "numpy>=1.18", "protobuf>=3.12.4"],
    setup_requires=[
        # Setuptools 18.0 properly handles Cython extensions.
        "setuptools>=18.0",
    ],
    package_dir={"": "src/"},
)
