"""
Workspace operations

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

class Client(object):
    """ client class for workspace upload/download """
    def __init__(self, parent):
        self.parent = parent

    def put(self, job_id, build_id, fileobj, fileobj_len):
        """ update workspace """
        try:
            response = self.parent.rest.do_build_request('PUT',
                                                         job_id,
                                                         build_id,
                                                         'workspace',
                                                         data=fileobj,
                                                         data_len=fileobj_len,
                                                         content_type="application/octet-stream")
        except:
            self.parent.log.exception('Failed to update workspace %s/%s', job_id, build_id)
            return False

        if response.status != 204:
            self.parent.log.error('Updating workspace %s/%s failed with HTTP code %d', job_id, build_id, response.status)
            return False

        return True

    def get(self, job_id, build_id, fileobj):
        """ Get workspace """
        try:
            response = self.parent.rest.do_build_request('GET',
                                                         job_id,
                                                         build_id,
                                                         'workspace')
        except:
            self.parent.log.exception('Failed to get workspace %s/%s', job_id, build_id)
            return False

        if response.status != 200:
            self.parent.log.error('Getting workspace %s/%s failed with HTTP code %d', job_id, build_id, response.status)
            return False

        while True:
            data = response.read(1024*64)
            if data == '':
                break
            fileobj.write(data)

        return True

    def delete(self, job_id, build_id):
        """ Delete workspace """
        try:
            response = self.parent.rest.do_build_request('DELETE',
                                                         job_id,
                                                         build_id,
                                                         'workspace')
        except:
            self.parent.log.exception('Failed to delete workspace %s/%s', job_id, build_id)
            return False

        if response.status != 204 and response.status != 404:
            self.parent.log.error('Delete workspace %s/%s failed with HTTP code %d', job_id, build_id, response.status)
            return False

        return True

