"""
Build operations

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import json

from . import state, workspace, console, artifacts

class Client(object):
    """ Client class for build related operations """
    def __init__(self, parent):
        self.parent = parent
        self.state = state.Client(parent)
        self.workspace = workspace.Client(parent)
        self.console = console.Client(parent)
        self.artifacts = artifacts.Client(parent)

    def list(self, job_id):
        """ list all build """
        try:
            response = self.parent.rest.do_build_request('GET',
                                                         job_id,
                                                         None,
                                                         None)
        except:
            self.parent.log.exception('Failed to list builds for %s', job_id)
            return None

        if response.status != 200:
            self.parent.log.error('List builds "%s" failed with HTTP code %d', job_id, response.status)
            return None

        try:
            return json.loads(response.read())
        except (TypeError, ValueError):
            self.parent.log.exception('Failed to decode reply to list builds, %s', job_id)
            return None

    def trigger(self, job_id):
        """ trigger a build """
        try:
            response = self.parent.rest.do_build_request('POST',
                                                         job_id,
                                                         None,
                                                         None)
        except:
            self.parent.log.exception('Failed to trigger a build for %s', job_id)
            return None

        if response.status != 201:
            self.parent.log.error('Trigger build "%s" failed with HTTP code %d', job_id, response.status)
            return None

        try:
            return json.loads(response.read())
        except (TypeError, ValueError):
            self.parent.log.exception('Failed to decode reply to trigger build %s', job_id)
            return None

    def delete(self, job_id, build_id):
        """ Delete a build """
        try:
            response = self.parent.rest.do_build_request('DELETE',
                                                         job_id,
                                                         build_id,
                                                         None)
        except:
            self.parent.log.exception('Failed to delete build %s/%s', job_id, build_id)
            return False

        if response.status != 204 or response.status != 404:
            self.parent.log.error('Delete build %s/%s failed with HTTP code %d', job_id, build_id, response.status)
            return False

        return True

