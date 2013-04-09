"""
Build state operations

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import json

class Client(object):
    """ client class for buid state operations """
    def __init__(self, parent):
        self.parent = parent

    def put(self, job_id, build_id, state):
        """ update state """
        try:
            response = self.parent.rest.do_build_request('PUT',
                                                         job_id,
                                                         build_id,
                                                         'state',
                                                         data=json.dumps(state))
        except:
            self.parent.log.exception('Failed to update build state %s/%s', job_id, build_id)
            return None

        if response.status != 200:
            self.parent.log.error('Updating build state %s/%s failed with HTTP code %d', job_id, build_id, response.status)
            return None

        try:
            return json.loads(response.read())
        except (TypeError, ValueError):
            self.parent.log.exception('Failed to decode reply to update build state')
            return None

    def get(self, job_id, build_id):
        """ get state """
        try:
            response = self.parent.rest.do_build_request('GET',
                                                         job_id,
                                                         build_id,
                                                         'state')
        except:
            self.parent.log.exception('Failed to get build state for %s', job_id)
            return None

        if response.status != 200:
            self.parent.log.error('Get build state %s failed with HTTP code %d', job_id, response.status)
            return None

        try:
            return json.loads(response.read())
        except (TypeError, ValueError):
            self.parent.log.exception('Failed to decode reply to get build state')
            return None

