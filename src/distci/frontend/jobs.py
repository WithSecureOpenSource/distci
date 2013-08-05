"""
Handle job related requests

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import os
import json
import logging
import shutil
import time
import webob

from distci.frontend import validators, jobs_builds, jobs_tags, distlocks, constants

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

    def get_jobs(self):
        """ Return all job ids """
        results = { 'jobs': [] }
        job_ids = os.listdir(self._data_dir())
        for job_id in job_ids:
            if not os.path.isdir(self._job_dir(job_id)):
                continue
            results['jobs'].append(job_id)
        return webob.Response(status=200, body=json.dumps(results), content_type="application/json")

    def create_or_update_job(self, request, job_id_param):
        """ Create a new job """
        try:
            job_config = json.load(request.body_file)
        except ValueError:
            self.log.error('Failed to load job config')
            return webob.Response(status=400, body=constants.ERROR_JOB_INVALID_PAYLOAD)
        job_id = job_config.get('job_id')
        if job_id == None:
            self.log.error('Missing job_id')
            return webob.Response(status=400, body=constants.ERROR_JOB_INVALID_PAYLOAD)
        if job_id_param and job_id_param != job_id:
            self.log.error('Job ID mismatch: %r vs %r' % (job_id, job_id_param))
            return webob.Response(status=400, body=constants.ERROR_JOB_INVALID_ID)
        if self.zknodes:
            lock = distlocks.ZooKeeperLock(self.zknodes, 'job-lock-%s' % job_id)
            if lock.try_lock() != True:
                lock.close()
                self.log.warn("Job locked '%s'" % job_id)
                return webob.Response(status=400, body=constants.ERROR_JOB_LOCKED)
        else:
            lock = None

        if not os.path.isdir(self._job_dir(job_id)):
            try:
                os.mkdir(self._job_dir(job_id))
            except OSError:
                if lock:
                    lock.unlock()
                    lock.close()
                return webob.Response(status=500, body=constants.ERROR_JOB_CONFIG_WRITE_FAILED)

        try:
            file(self._job_config_file(job_id), 'wb').write(json.dumps(job_config))
        except IOError:
            self.log.error('Failed to write job config, job_id %s' % job_id)
            if lock:
                lock.unlock()
                lock.close()
            return webob.Response(status=500, body=constants.ERROR_JOB_CONFIG_WRITE_FAILED)

        if lock:
            lock.unlock()
            lock.close()

        return webob.Response(status=200 if job_id_param else 201, body=json.dumps({'job_id':job_id, 'config':job_config}), content_type="application/json")

    def delete_job(self, job_id):
        """ Delete job """
        if not os.path.isdir(self._job_dir(job_id)):
            return webob.Response(status=404, body=constants.ERROR_JOB_NOT_FOUND)
        try:
            shutil.rmtree(self._job_dir(job_id))
        except OSError:
            return webob.Response(status=404, body=constants.ERROR_JOB_NOT_FOUND)
        return webob.Response(status=204)

    def get_job_config(self, job_id):
        """ Get config for a specific job """
        if not os.path.isdir(self._job_dir(job_id)):
            return webob.Response(status=404, body=constants.ERROR_JOB_NOT_FOUND)
        job_data = None
        for _ in range(10):
            try:
                job_data = json.dumps({'job_id': job_id, 'config': self._load_job_config(job_id)})
                break
            except (OSError, ValueError):
                time.sleep(0.1)
        if not job_data:
            return webob.Response(status=409, body=constants.ERROR_JOB_LOCKED)
        return webob.Response(status=200, body=job_data, content_type="application/json")

    def handle_request(self, request, parts):
        """ Main dispatcher """
        if len(parts) == 0:
            if request.method == 'GET':
                return self.get_jobs()
        else:
            if validators.validate_job_id(parts[0]) == None:
                self.log.error('Invalid job_id: %r' % parts[0])
                return webob.Response(status=400, body=constants.ERROR_JOB_INVALID_ID)

            if len(parts) == 1:
                if request.method == 'GET':
                    return self.get_job_config(parts[0])
                elif request.method == 'PUT':
                    return self.create_or_update_job(request, parts[0])
                elif request.method == 'DELETE':
                    return self.delete_job(parts[0])
            elif parts[1] == 'builds':
                return self.jobs_builds.handle_request(request, parts[0], parts[2:])
            elif parts[1] == 'tags':
                return self.jobs_tags.handle_request(request, parts[0], parts[2:])

        return webob.Response(status=400)

