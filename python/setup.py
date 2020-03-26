import sys
import platform

from setuptools import setup, Extension, Command, find_packages


class VendorCommand(Command):
    """Custom build command."""

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess

        # Run update.sh to update vendored libra-dev files.
        subprocess.run(["./update.sh"], cwd="./lib", shell=True, check=True)


# Require pytest-runner only when running tests
pytest_runner = ["pytest-runner"] if any(arg in sys.argv for arg in ("pytest", "test")) else []
grpcio_tools = ["grpcio-tools"] if any(arg in sys.argv for arg in ["vendor"]) else []

LIBRA_INCLUDE_DIR = "lib"
LIBRA_HEADER = "%s/%s" % (LIBRA_INCLUDE_DIR, "data.h")
LIBRA_LIB_DIR = "lib"

extra_link_args = []
if platform.system() == "Darwin":
    LIBRA_LIB_FILE = "%s/%s-%s.a" % (LIBRA_LIB_DIR, "liblibra_dev", "darwin-%s" % platform.machine())
    extra_link_args.extend(["-framework", "Security"])
elif platform.system() == "Linux":
    LIBRA_LIB_FILE = "%s/%s-%s.a" % (LIBRA_LIB_DIR, "liblibra_dev", "linux-%s" % platform.machine())
    extra_link_args.append("-ldl")
    extra_link_args.append("-lm")
    extra_link_args.append("-pthread")


exts = [
    Extension(
        name="pylibra.api",
        sources=["src/pylibra/api.pyx"],
        include_dirs=[LIBRA_INCLUDE_DIR],
        extra_objects=[LIBRA_LIB_FILE],
        depends=["src/pylibra/capi.pxd", LIBRA_HEADER, LIBRA_LIB_FILE],
        extra_link_args=extra_link_args,
    ),
    Extension(
        name="pylibra._native",
        sources=["src/pylibra/_native.pyx"],
        include_dirs=[LIBRA_INCLUDE_DIR],
        extra_objects=[LIBRA_LIB_FILE],
        depends=["src/pylibra/capi.pxd", LIBRA_HEADER, LIBRA_LIB_FILE],
        extra_link_args=extra_link_args,
    ),
]


setup(
    name="ivtjfchcukjgtekjrnbllkfrdkvdhdkh",
    # change to 0.1.YYYYMMDDNN on release
    version="0.2.2020032502",
    description="",
    python_requires=">=3.7",
    packages=find_packages("src"),
    include_package_data=True,  # see MANIFEST.in
    zip_safe=True,
    install_requires=["requests>=2.19"],
    tests_require=["pytest", "pytest-timeout", "pytest-runner", "pylama", "black"],
    setup_requires=[
        # Setuptools 18.0 properly handles Cython extensions.
        "setuptools>=18.0",
        "cython>=0.29",
    ]
    + grpcio_tools
    + pytest_runner,
    package_dir={"": "src/"},
    ext_modules=exts,
    cmdclass={"vendor": VendorCommand},
)
