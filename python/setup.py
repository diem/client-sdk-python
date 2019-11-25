import sys

from setuptools import setup, Extension

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
    tests_require=["pytest", "pytest-runner"],
    setup_requires=[
        # Setuptools 18.0 properly handles Cython extensions.
        'setuptools>=18.0',
        'cython',
    ] + pytest_runner,
    package_dir={"" : "src"},
    ext_modules=exts,
)
