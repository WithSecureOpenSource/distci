"""
Job operations

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import json

class Client(object):
    """ client class for job related operations """
    def __init__(self, parent):
        self.parent = parent

    def list(self):
        """ list existing jobs """
        try:
            response = self.parent.rest.do_job_request('GET',
                                                       None)
        except:
            self.parent.log.exception('Failed to list jobs')
            return None

        if response.status != 200:
            self.parent.log.error('List jobs failed with HTTP code %d', response.status)
            return None

        try:
            return json.loads(response.read())
        except (TypeError, ValueError):
            self.parent.log.exception('Failed to decode reply to job create')
            return None

    def create(self, job_config):
        """ create a job """
        if not job_config.get('job_id'):
            return None
        try:
            response = self.parent.rest.do_job_request('POST',
                                                       None,
                                                       data=json.dumps(job_config))
        except:
            self.parent.log.exception('Failed to create job %s', job_config['job_id'])
            return None

        if response.status != 201:
            self.parent.log.error('Create job %s failed with HTTP code %d', job_config['job_id'], response.status)
            return None

        try:
            return json.loads(response.read())
        except (TypeError, ValueError):
            self.parent.log.exception('Failed to decode reply to job create')
            return None

    def update(self, job_id, job_config):
        """ update job config """
        try:
            response = self.parent.rest.do_job_request('PUT',
                                                       job_id,
                                                       data=json.dumps(job_config))
        except:
            self.parent.log.exception('Failed to update job %s', job_id)
            return None

        if response.status != 200:
            self.parent.log.error('Update job %s failed with HTTP code %d', job_id, response.status)
            return None

        try:
            return json.loads(response.read())
        except (TypeError, ValueError):
            self.parent.log.exception('Failed to decode reply to job update')
            return None

    def get(self, job_id):
        """ get job configuration """
        try:
            response = self.parent.rest.do_job_request('GET',
                                                       job_id)
        except:
            self.parent.log.exception('Failed to get job config for %s', job_id)
            return None

        if response.status != 200:
            self.parent.log.error('Get job %s failed with HTTP code %d', job_id, response.status)
            return None

        try:
            return json.loads(response.read())
        except (TypeError, ValueError):
            self.parent.log.exception('Failed to decode reply to get job')
            return None

    def delete(self, job_id):
        """ delete a job """
        try:
            response = self.parent.rest.do_job_request('DELETE',
                                                       job_id)
        except:
            self.parent.log.exception('Failed to delete job %s', job_id)
            return False

        if response.status != 204 and response.status != 404:
            self.parent.log.error('Delete job %s failed with HTTP code %d', job_id, response.status)
            return False

        return True
