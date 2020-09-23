# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import platform
import sys

from setuptools import Command, Extension, find_packages, setup


class VendorCommand(Command):
    """Custom build command."""

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess

        # Run codegen.sh to update python lcs files.
        subprocess.run(["./codegen.sh"], shell=True, check=True)


# Require pytest-runner only when running tests
pytest_runner = ["pytest-runner"] if any(arg in sys.argv for arg in ("pytest", "test")) else []

setup(
    name="pylibra2",
    # change to 0.1.YYYYMMDDNN on release
    version="0.1.master",
    description="",
    python_requires=">=3.7",
    packages=["pylibra2"],
    include_package_data=True,  # see MANIFEST.in
    zip_safe=True,
    install_requires=["requests>=2.19", "cryptography>=3.1", "numpy>=1.18", "dacite>=1.5.0"],
    tests_require=["pytest", "pytest-timeout", "pytest-runner", "pylama", "black"],
    setup_requires=[
        # Setuptools 18.0 properly handles Cython extensions.
        "setuptools>=18.0",
    ]
    + pytest_runner,
    package_dir={"": "src/"},
    cmdclass={"vendor": VendorCommand},
)
