# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
from setuptools import setup


setup(
    name="pylibra-beta", # libra-client-sdk
    version="0.5.master",
    # description="The Python Client SDK for Libra",
    # url="https://github.com/libra/libra-client-sdk-python",
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
