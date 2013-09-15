#!/usr/bin/env python
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
                 'distci.worker.copy_artifacts',
                 'distci.cli' ],
    package_dir = { 'distci': 'src/distci' },
    entry_points = {
        'console_scripts': [
            'distci = distci.cli.__main__:main_entry',
            'distci-build-control-worker = distci.worker.build_control.__main__:main_entry',
            'distci-git-checkout-worker = distci.worker.git_checkout.__main__:main_entry',
            'distci-execute-shell-worker = distci.worker.execute_shell.__main__:main_entry',
            'distci-publish-artifacts-worker = distci.worker.publish_artifacts.__main__:main_entry',
            'distci-copy-artifacts-worker = distci.worker.copy_artifacts.__main__:main_entry'
        ]
    },
    author = 'Heikki Nousiainen',
    author_email = 'Heikki.Nousiainen@F-Secure.com',
    url = 'http://github.com/F-Secure/distci',
    data_files = [('distci/frontend/ui',
                      ['src/ui/index.html']),
                  ('distci/frontend/ui/js',
                      ['src/ui/js/app.js',
                       'src/ui/js/controllers.js']),
                  ('distci/frontend/ui/html',
                      ['src/ui/html/jobbuildstate.html',
                       'src/ui/html/jobbuilds.html',
                       'src/ui/html/jobs.html']),
                  ('distci/frontend/ui/css',
                      ['src/ui/css/app.css'])]
)

