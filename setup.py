# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import platform
import sys

from setuptools import Command, Extension, find_packages, setup

setup(
    name="libra-client-sdk",
    # change to 0.1.YYYYMMDDNN on release
    version="0.1.2020101001",
    description="The Python Client SDK for Libra",
    python_requires=">=3.7",
    packages=["libra"],
    include_package_data=True,  # see MANIFEST.in
    zip_safe=True,
    install_requires=["requests>=2.19", "cryptography>=3.1", "numpy>=1.18", "protobuf==3.13.0"],
    setup_requires=[
        # Setuptools 18.0 properly handles Cython extensions.
        "setuptools>=18.0",
    ],
    package_dir={"": "src/"},
)
