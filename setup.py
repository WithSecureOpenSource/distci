from setuptools import setup
import version

setup(
    name = 'distci',
    version = version.git_version(),
    packages = [ 'distci',
                 'distci.frontend',
                 'distci.distcilib',
                 'distci.worker',
                 'distci.worker.calculator' ],
    package_dir = { 'distci': 'src' },
    entry_points = {
        'console_scripts': [
            'distci-frontend = distci.frontend.__main__:main_entry',
            'distci-calculator-worker = distci.worker.calculator.__main__:main_entry'
        ]
    },
    author = 'Heikki Nousiainen',
    author_email = 'Heikki.Nousiainen@F-Secure.com',
    url = 'http://github.com/F-Secure/distci'
)

