"""
Console log operations

Copyright (c) 2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

class Client(object):
    """ client class for build console log related operations """
    def __init__(self, parent):
        self.parent = parent

    def append(self, job_id, build_id, log):
        """ append console log """
        try:
            response = self.parent.rest.do_build_request('POST',
                                                         job_id,
                                                         build_id,
                                                         'console',
                                                         data=log,
                                                         content_type="text/plain")
        except:
            self.parent.log.exception('Failed to update console log %s/%s', job_id, build_id)
            return False

        if response.status != 204:
            self.parent.log.error('Updating console log %s/%s failed with HTTP code %d', job_id, build_id, response.status)
            return False

        return True

    def get(self, job_id, build_id):
        """ get console log """
        try:
            response = self.parent.rest.do_build_request('GET',
                                                         job_id,
                                                         build_id,
                                                         'console')
        except:
            self.parent.log.exception('Failed to get console log config for %s', job_id)
            return None

        if response.status != 200:
            self.parent.log.error('Get console log %s failed with HTTP code %d', job_id, response.status)
            return None

        return response.read()

