"""
DistCILib module

Copyright (c) 2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import logging

from . import rest, tasks, jobs, builds

class DistCIClient(object):
    """ Client class for accessing DistCI """
    def __init__(self, client_config):
        self.log = logging.getLogger('DistCIClient')
        self.config = client_config
        self.rest = rest.RESTHelper(self)
        self.tasks = tasks.Client(self)
        self.jobs = jobs.Client(self)
        self.builds = builds.Client(self)

