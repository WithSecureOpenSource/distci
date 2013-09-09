"""
Handle job related requests

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import os
import json
import logging
import time
import webob

from distci.frontend import validators, jobs_builds, jobs_tags, sync, constants, storage

class Jobs(object):
    """ Class for handling job related requests """
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('jobs')
        self.zknodes = config.get('zookeeper_nodes')
        self.cephmonitors = config.get('ceph_monitors')
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

    def get_jobs(self):
        """ Return all job ids """
        results = { 'jobs': [] }
        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        with storage_backend as store:
            job_ids = store.listdir(self._data_dir())
            for job_id in job_ids:
                if not store.isdir(self._job_dir(job_id)):
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
            lock = sync.ZooKeeperLock(self.zknodes, 'job-lock-%s' % job_id)
        else:
            lock = sync.PhonyLock('job-lock-%s' % job_id)
        if lock.try_lock() != True:
            lock.close()
            self.log.warn("Job locked '%s'" % job_id)
            return webob.Response(status=400, body=constants.ERROR_JOB_LOCKED)

        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        with storage_backend as store:
            if not store.isdir(self._job_dir(job_id)):
                try:
                    store.mkdir(self._job_dir(job_id))
                except:
                    self.log.exception('Failed to to create job directory, job_id %s' % job_id)
                    lock.unlock()
                    lock.close()
                    return webob.Response(status=500, body=constants.ERROR_JOB_CONFIG_WRITE_FAILED)
            try:
                with store.open(self._job_config_file(job_id), 'wb') as fileo:
                    json.dump(job_config, fileo)
            except:
                self.log.exception('Failed to write job config, job_id %s' % job_id)
                lock.unlock()
                lock.close()
                return webob.Response(status=500, body=constants.ERROR_JOB_CONFIG_WRITE_FAILED)

        lock.unlock()
        lock.close()

        return webob.Response(status=200 if job_id_param else 201, body=json.dumps({'job_id':job_id, 'config':job_config}), content_type="application/json")

    def delete_job(self, job_id):
        """ Delete job """
        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        with storage_backend as store:
            if not store.isdir(self._job_dir(job_id)):
                return webob.Response(status=404, body=constants.ERROR_JOB_NOT_FOUND)
            try:
                store.rmtree(self._job_dir(job_id))
            except storage.NotFound:
                return webob.Response(status=404, body=constants.ERROR_JOB_NOT_FOUND)
            except:
                self.log.exception("Exception in delete job")
                return webob.Response(status=500, body=constants.ERROR_INTERNAL)

        return webob.Response(status=204)

    def get_job_config(self, job_id):
        """ Get config for a specific job """
        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        with storage_backend as store:
            if not store.isdir(self._job_dir(job_id)):
                return webob.Response(status=404, body=constants.ERROR_JOB_NOT_FOUND)
            job_data = None
            for _ in range(10):
                try:
                    with store.open(self._job_config_file(job_id), 'rb') as fileo:
                        job_data = json.dumps({'job_id': job_id, 'config': json.load(fileo)})
                    break
                except (storage.NotFound, ValueError):
                    time.sleep(0.1)
                except:
                    self.log.exception("Exception while getting job config")
                    return webob.Response(status=500, body=constants.ERROR_INTERNAL)
        if not job_data:
            return webob.Response(status=409, body=constants.ERROR_JOB_LOCKED)
        return webob.Response(status=200, body=job_data, content_type="application/json")

    def github_webhook_trigger(self, request, job_id):
        """ Trigger builds via github webhook """
        try:
            data = json.loads(request.params['payload'])
            ref = data['ref']
        except (AttributeError, ValueError, KeyError):
            return webob.Response(status=400)

        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        with storage_backend as store:
            if not store.isdir(self._job_dir(job_id)):
                return webob.Response(status=404, body=constants.ERROR_JOB_NOT_FOUND)
            job_config = None
            for _ in range(10):
                try:
                    with store.open(self._job_config_file(job_id), 'rb') as fileo:
                        job_config = json.load(fileo)
                    break
                except (storage.NotFound, ValueError):
                    time.sleep(0.1)
                except:
                    self.log.exception("Exception while getting job config")
                    return webob.Response(status=500, body=constants.ERROR_INTERNAL)
        if not job_config:
            return webob.Response(status=409, body=constants.ERROR_JOB_LOCKED)
        for task in job_config.get('tasks', []):
            if task.get('type') == 'git-checkout':
                if task.get('params', {}).get('ref') == ref:
                    return self.jobs_builds.trigger_build(job_id)
        return webob.Response(status=400)

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
            elif len(parts) == 2 and parts[1] == 'github-webhook' and request.method == 'POST':
                return self.github_webhook_trigger(request, parts[0])

        return webob.Response(status=400)

