from setuptools import setup

setup(
    name = 'distci',
    packages = [ 'distci',
                 'distci.frontend',
                 'distci.worker',
                 'distci.worker.calculator' ],
    package_dir = { 'distci': 'src' },
    entry_points = {
        'console_scripts': [
            'distci-frontend = distci.frontend.__main__:main_entry',
            'distci-calculator-worker = distci.worker.calculator.__main__:main_entry'
        ]
    }
)

