import sys

from setuptools import setup, Extension, Command

class DownloadProtoCommand(Command):
    """Custom build command."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        # Run download.sh to download all proto files
        subprocess.call("./download.sh", cwd="./src/pylibra/transport/proto")


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
        from grpc.tools import command
        command.build_package_protos('src/pylibra/transport/proto')
        # Run fix.sh to fix up geneated protos python bindings by adding . to import line
        import subprocess
        subprocess.call("./fix.sh", cwd="./src/pylibra/transport/proto")


# Require pytest-runner only when running tests
pytest_runner = ["pytest-runner"] if any(arg in sys.argv for arg in ("pytest", "test")) else []

exts = [
    Extension(
        name='pylibra.api',
        sources=['src/pylibra/capi.pxd', 'src/pylibra/api.pyx'],
        include_dirs=["../libra-dev/include"],
        extra_link_args=["-L../libra-dev/target/debug"],
        libraries=["libra_dev"],
    ),
    Extension(
        name='pylibra._types',
        sources=['src/pylibra/capi.pxd', 'src/pylibra/_types.pyx'],
        include_dirs=["../libra-dev/include"],
        extra_link_args=["-L../libra-dev/target/debug"],
        libraries=["libra_dev"],
    ),
]


setup(
    name="pylibra",
    version="1.0.0",
    description="Python interface for the libra-dev library function",
    install_requires=["grpcio"],
    tests_require=["pytest", "pytest-runner"],
    setup_requires=[
        # Setuptools 18.0 properly handles Cython extensions.
        'setuptools>=18.0',
        'cython',
        "grpcio-tools",
    ] + pytest_runner,
    package_dir={
        "": "src/",
    },
    ext_modules=exts,
    cmdclass={
        'download_proto': DownloadProtoCommand,
        'build_proto': BuildProtoCommand,
    },
)
