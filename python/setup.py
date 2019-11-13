import sys

from setuptools import setup, Extension
from Cython.Build import cythonize

# Require pytest-runner only when running tests
pytest_runner = (
    ["pytest-runner"] if any(arg in sys.argv for arg in ("pytest", "test")) else []
)

setup_requires = pytest_runner

setup(
    name="pylibra",
    version="1.0.0",
    description="Python interface for the libra-dev library function",
    author="Yucong Sun",
    author_email="sunyucong@gmail.com",
    tests_require=["pytest", "pytest-runner"],
    ext_modules=cythonize(
        [
            Extension(
                "pylibra",
                ["pylibra.pyx"],
                extra_link_args=["-L../libra-dev/target/debug"],
                libraries=["libra_dev"],
            )
        ]
    ),
    setup_requires=setup_requires,
)
