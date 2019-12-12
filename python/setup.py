import sys
import platform

from setuptools import setup, Extension, Command, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop


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
        subprocess.call("./update.sh", cwd="./lib")
        # Run download.sh to download all proto files
        subprocess.call("./download.sh", cwd="./src/pylibra/grpc")


class BuildProtoCommand(Command):
    """Custom build command."""

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # TODO: change to pure python
        # Generate proto files
        from grpc_tools import command

        command.build_package_protos("./src/pylibra/grpc", strict_mode=True)
        # Run fix.sh to fix up geneated protos python bindings by adding . to import line
        import subprocess

        subprocess.call("./fix.sh", cwd="./src/pylibra/grpc")


class BuildLibraCommand(Command):
    """Custom build command."""

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess

        subprocess.call("./build.sh", cwd="lib")


class DevelopCommand(develop):
    def run(self):
        self.run_command("build_proto")
        develop.run(self)


class BuildPyCommand(build_py):
    def run(self):
        self.run_command("build_proto")
        build_py.run(self)


# This is an wrapper to lazy-load setuptools's build_ext, in order to get cython detection working.
class BuildExtCommand(object):
    _build_ext = None

    def __init__(self, *args, **kwargs):
        from setuptools.command.build_ext import build_ext

        BuildExtCommand._build_ext = build_ext(*args, **kwargs)

    def __getattr__(self, *args, **kwargs):
        if BuildExtCommand._build_ext:
            return BuildExtCommand._build_ext.__getattribute__(*args, **kwargs)

    def __setattr__(self, *args, **kwargs):
        if BuildExtCommand._build_ext:
            BuildExtCommand._build_ext.__setattr__(*args, **kwargs)

    def run(self):
        self.run_command("build_libra")
        BuildExtCommand._build_ext.__dict__.update(self.__dict__)
        BuildExtCommand._build_ext.run()


# Require pytest-runner only when running tests
pytest_runner = ["pytest-runner"] if any(arg in sys.argv for arg in ("pytest", "test")) else []

LIBRA_INCLUDE_DIR = "lib/src/include"
LIBRA_HEADER = "%s/%s" % (LIBRA_INCLUDE_DIR, "data.h")
LIBRA_LIB_DIR = "lib/target/release"
LIBRA_LIB_FILE = "%s/%s" % (LIBRA_LIB_DIR, "liblibra_dev.a")

extra_link_args = []
if platform.system() == "Darwin":
    extra_link_args.extend(["-framework", "Security"])
elif platform.system() == "Linux":
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
        name="pylibra._types",
        sources=["src/pylibra/_types.pyx"],
        include_dirs=[LIBRA_INCLUDE_DIR],
        extra_objects=[LIBRA_LIB_FILE],
        depends=["src/pylibra/capi.pxd", LIBRA_HEADER, LIBRA_LIB_FILE],
        extra_link_args=extra_link_args,
    ),
]


setup(
    name="calibra-pylibra",
    version="0.1.2019121003",
    description="Official Python binding for libra-client-dev C API",
    python_requires="~=3.7",
    packages=find_packages("src"),
    include_package_data=False,  # see MANIFEST.in
    zip_safe=True,
    install_requires=["grpcio", "protobuf", "requests"],
    tests_require=["pytest", "pytest-runner", "pylama", "black"],
    setup_requires=[
        # Setuptools 18.0 properly handles Cython extensions.
        "setuptools>=18.0",
        "cython",
        "grpcio-tools",
    ]
    + pytest_runner,
    package_dir={"": "src/"},
    ext_modules=exts,
    cmdclass={
        "vendor": VendorCommand,
        "build_proto": BuildProtoCommand,
        "build_libra": BuildLibraCommand,
        "build_ext": BuildExtCommand,
        "build_py": BuildPyCommand,
        "develop": DevelopCommand,
    },
)
