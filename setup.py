from setuptools import setup

setup(
    name = 'distci',
    packages = [ 'distci', 'distci.frontend' ],
    package_dir = { 'distci': 'src' },
    entry_points = {
        'console_scripts': [
            'distci-frontend = distci.frontend.__main__:main_entry'
        ]
    }
)

