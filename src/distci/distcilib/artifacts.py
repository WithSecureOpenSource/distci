"""
Build artifact operations

Copyright (c) 2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import json

class Client(object):
    """ client class for build artifact related operations """
    def __init__(self, parent):
        self.parent = parent

    def put(self, job_id, build_id, fileobj, fileobj_len):
        """ Push a build artifact """
        try:
            response = self.parent.rest.do_build_request('POST',
                                                         job_id,
                                                         build_id,
                                                         'artifacts',
                                                         data=fileobj,
                                                         data_len=fileobj_len,
                                                         content_type="application/octet-stream")
        except:
            self.parent.log.exception('Failed to send artifact %s/%s', job_id, build_id)
            return None

        if response.status != 201:
            self.parent.log.error('Posting artifact %s/%s failed with HTTP code %d', job_id, build_id, response.status)
            return None

        try:
            return json.loads(response.read())
        except (TypeError, ValueError):
            self.parent.log.exception('Failed to decode reply to post artifact, %s', job_id)
            return None

    def get(self, job_id, build_id, artifact_id, fileobj):
        """ Get an artifact """
        try:
            response = self.parent.rest.do_build_request('GET',
                                                         job_id,
                                                         build_id,
                                                         'artifacts/%s' % artifact_id)
        except:
            self.parent.log.exception('Failed to get artifact %s/%s/%s', job_id, build_id, artifact_id)
            return False

        if response.status != 200:
            self.parent.log.error('Getting artifact %s/%s/%s failed with HTTP code %d', job_id, build_id, artifact_id, response.status)
            return False

        while True:
            data = response.read(1024*64)
            if data == '':
                break
            fileobj.write(data)

        return True

    def delete(self, job_id, build_id, artifact_id):
        """ delete artifact """
        try:
            response = self.parent.rest.do_build_request('DELETE',
                                                         job_id,
                                                         build_id,
                                                         'artifacts/%s' % artifact_id)
        except:
            self.parent.log.exception('Failed to delete artifact %s/%s/%s', job_id, build_id, artifact_id)
            return False

        if response.status != 204 and response.status != 404:
            self.parent.log.error('Delete artifact %s/%s/%s failed with HTTP code %d', job_id, build_id, artifact_id, response.status)
            return False

        return True
