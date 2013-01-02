from setuptools import setup

setup(
    name = 'distci',
    packages = [ 'distci', 'distci.frontend' ],
    package_dir = { 'distci': 'src' }
)

