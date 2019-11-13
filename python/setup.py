import sys

from skbuild import setup  # This line replaces 'from setuptools import setup'

# Require pytest-runner only when running tests
pytest_runner = (['pytest-runner']
                 if any(arg in sys.argv for arg in ('pytest', 'test'))
                 else [])

setup_requires = pytest_runner

setup(name="pylibra",
      version="1.0.0",
      description="Python interface for the libra-dev library function",
      author="Yucong Sun",
      author_email="sunyucong@gmail.com",
      packages=['pylibra'],
      tests_require=['pytest', 'pytest-runner'],
      setup_requires=setup_requires
)