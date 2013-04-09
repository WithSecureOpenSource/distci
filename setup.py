from setuptools import setup
import version

setup(
    name = 'distci',
    version = version.git_version(),
    packages = [ 'distci',
                 'distci.frontend',
                 'distci.distcilib',
                 'distci.worker',
                 'distci.worker.build_control',
                 'distci.worker.git_checkout',
                 'distci.worker.execute_shell',
                 'distci.worker.publish_artifacts',
                 'distci.worker.calculator' ],
    package_dir = { 'distci': 'src/distci' },
    entry_points = {
        'console_scripts': [
            'distci-frontend = distci.frontend.__main__:main_entry',
            'distci-build-control-worker = distci.worker.build_control.__main__:main_entry',
            'distci-git-checkout-worker = distci.worker.git_checkout.__main__:main_entry',
            'distci-execute-shell-worker = distci.worker.execute_shell.__main__:main_entry',
            'distci-publish-artifacts-worker = distci.worker.publish_artifacts.__main__:main_entry',
            'distci-calculator-worker = distci.worker.calculator.__main__:main_entry'
        ]
    },
    author = 'Heikki Nousiainen',
    author_email = 'Heikki.Nousiainen@F-Secure.com',
    url = 'http://github.com/F-Secure/distci'
)

