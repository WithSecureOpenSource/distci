""" Handle job related requests """

import os
import json
import logging
import shutil
import time

from . import validators, request, response, jobs_builds, jobs_tags, distlocks

ERROR_INVALID_JOB_ID      = 'Invalid job ID'
ERROR_INVALID_JOB_PAYLOAD = 'Decoding job data failed'
ERROR_JOB_NOT_FOUND       = 'No such job'
ERROR_JOB_LOCKED          = 'Job locked'
ERROR_JOB_CONFIG_WRITE_FAILED = 'Failed to write job configuration'

class Jobs(object):
    """ Class for handling job related requests """
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('jobs')
        self.zknodes = config.get('zookeeper_nodes', [])
        if len(self.zknodes) == 0:
            self.zknodes = None
        self.jobs_builds = jobs_builds.JobsBuilds(config)
        self.jobs_tags = jobs_tags.JobsTags(config)

    def _data_dir(self):
        """ Return jobs directory """
        return os.path.join(self.config.get('data_directory'), 'jobs')

    def _job_dir(self, job_id):
        """ Return directory for a specific job """
        return os.path.join(self._data_dir(), job_id)

    def _job_config_file(self, job_id):
        """ Return filename for job config """
        return os.path.join(self._job_dir(job_id), 'job.config')

    def _load_job_config(self, job_id):
        """ Load and return job config """
        return json.load(file(self._job_config_file(job_id), 'rb'))

    def get_jobs(self, start_response):
        """ Return all job ids """
        results = { 'jobs': [] }
        job_ids = os.listdir(self._data_dir())
        for job_id in job_ids:
            if not os.path.isdir(self._job_dir(job_id)):
                continue
            results['jobs'].append(job_id)
        return response.send_response(start_response, 200, json.dumps(results))

    def create_or_update_job(self, environ, start_response, job_id_param = None):
        """ Create a new job """
        try:
            job_config = json.loads(request.read_request_data(environ))
        except ValueError:
            self.log.debug('Failed to load job config')
            return response.send_error(start_response, 400, ERROR_INVALID_JOB_PAYLOAD)
        job_id = job_config.get('job_id')
        if job_id == None:
            self.log.debug('Missing job_id')
            return response.send_error(start_response, 400, ERROR_INVALID_JOB_PAYLOAD)
        if job_id_param and job_id_param != job_id:
            self.log.debug('Job ID mismatch: %r vs %r' % (job_id, job_id_param))
            return response.send_error(start_response, 400, ERROR_INVALID_JOB_ID)
        if validators.validate_job_id(job_id) == None:
            self.log.debug('Invalid job_id: %r' % job_id)
            return response.send_error(start_response, 400, ERROR_INVALID_JOB_ID)
        if self.zknodes:
            lock = distlocks.ZooKeeperLock(self.zknodes, 'job-lock-%s' % job_id)
            if lock.try_lock() != True:
                lock.close()
                self.log.debug("Job locked '%s'" % job_id)
                return response.send_error(start_response, 400, ERROR_JOB_LOCKED)
        else:
            lock = None

        if job_id_param is None:
            try:
                os.mkdir(self._job_dir(job_id))
            except OSError:
                if lock:
                    lock.unlock()
                    lock.close()
                return response.send_error(start_response, 500, ERROR_JOB_CONFIG_WRITE_FAILED)

        try:
            file(self._job_config_file(job_id), 'wb').write(json.dumps(job_config))
        except IOError:
            self.log.debug('Failed to write job config, job_id %s' % job_id)
            if lock:
                lock.unlock()
                lock.close()
            return response.send_error(start_response, 500, ERROR_JOB_CONFIG_WRITE_FAILED)

        return response.send_response(start_response, 200 if job_id_param else 201, json.dumps({'job_id':job_id, 'config':job_config}))

    def delete_job(self, start_response, job_id):
        """ Delete job """
        if validators.validate_job_id(job_id) == None:
            self.log.debug('Invalid job_id: %r' % job_id)
            return response.send_error(start_response, 400, ERROR_INVALID_JOB_ID)
        if not os.path.isdir(self._job_dir(job_id)):
            return response.send_error(start_response, 404, ERROR_JOB_NOT_FOUND)
        self.log.debug("delete job %s" % job_id)
        try:
            shutil.rmtree(self._job_dir(job_id))
        except OSError:
            return response.send_error(start_response, 404, ERROR_JOB_NOT_FOUND)
        return response.send_response(start_response, 204)

    def get_job_config(self, start_response, job_id):
        """ Get config for a specific job """
        if validators.validate_job_id(job_id) != job_id:
            return response.send_error(start_response, 400, ERROR_INVALID_JOB_ID)
        if not os.path.isdir(self._job_dir(job_id)):
            return response.send_error(start_response, 404, ERROR_JOB_NOT_FOUND)
        self.log.debug("get job config %s" % job_id)
        job_data = None
        for _ in range(10):
            try:
                job_data = json.dumps({'job_id': job_id, 'config': self._load_job_config(job_id)})
                break
            except (OSError, ValueError):
                time.sleep(0.1)
        if not job_data:
            return response.send_error(start_response, 409, ERROR_JOB_LOCKED)
        return response.send_response(start_response, 200, job_data)

    def handle_request(self, environ, start_response, method, parts):
        """ Main dispatcher """
        if len(parts) == 0:
            if method == 'GET':
                return self.get_jobs(start_response)
            elif method == 'POST':
                return self.create_or_update_job(environ, start_response)
            else:
                return response.send_error(start_response, 400)
        elif len(parts) == 1:
            if method == 'GET':
                return self.get_job_config(start_response, parts[0])
            elif method == 'PUT':
                return self.create_or_update_job(environ, start_response, parts[0])
            elif method == 'DELETE':
                return self.delete_job(start_response, parts[0])
            else:
                return response.send_error(start_response, 400)
        elif parts[1] == 'builds':
            return self.jobs_builds.handle_request(environ, start_response, method, parts[0], parts[2:])
        elif parts[1] == 'tags':
            return self.jobs_tags.handle_request(environ, start_response, method, parts[0], parts[2:])

        return response.send_error(start_response, 400)

