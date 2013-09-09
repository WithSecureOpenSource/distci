"""
Handle requests related to build operations

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import os
import json
import logging
import time
import webob

from distci.frontend import validators, jobs_builds_artifacts, sync, constants, storage

from distci import distcilib

class JobsBuilds(object):
    """ Class for handling build related requests """
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('jobs_builds')
        self.zknodes = config.get('zookeeper_nodes')
        self.cephmonitors = config.get('ceph_monitors')
        self.jobs_builds_artifacts = jobs_builds_artifacts.JobsBuildsArtifacts(config)
        self.distci_client = distcilib.DistCIClient(config)

    def _job_dir(self, job_id):
        """ Return directory for a specific job """
        return os.path.join(self.config.get('data_directory'), 'jobs', job_id)

    def _build_dir(self, job_id, build_id):
        """ Return directory for a specific build """
        return os.path.join(self._job_dir(job_id), build_id)

    def _build_state_file(self, job_id, build_id):
        """ Return filename for a build state file """
        return os.path.join(self._build_dir(job_id, build_id), 'build.state')

    def _build_workspace_file(self, job_id, build_id):
        """ Return filename for workspace archive """
        return os.path.join(self._build_dir(job_id, build_id), 'workspace')

    def _console_log_file(self, job_id, build_id):
        """ Return filename for a build console log """
        return os.path.join(self._build_dir(job_id, build_id), 'console.log')

    def _get_build_numbers(self, store, job_id):
        """ Return all builds for given job """
        build_ids = []
        build_id_candidates = store.listdir(self._job_dir(job_id))
        for build_id_candidate in build_id_candidates:
            try:
                build_number = int(build_id_candidate)
                build_ids.append(build_number)
            except ValueError:
                pass
        return build_ids

    def get_builds(self, job_id):
        """ Return all builds for a specific job """
        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        with storage_backend as store:
            if not store.isdir(self._job_dir(job_id)):
                return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)
            result = { 'builds': self._get_build_numbers(store, job_id) }
        if len(result['builds']) > 0:
            result['last_build_number'] = max(result['builds'])
        return webob.Response(status=200, body=json.dumps(result), content_type="application/json")

    def trigger_build(self, job_id):
        """ Trigger a new build """
        if self.zknodes:
            lock = sync.ZooKeeperLock(self.zknodes, 'job-lock-%s' % job_id)
        else:
            lock = sync.PhonyLock('job-lock-%s' % job_id)
        if lock.try_lock() != True:
            lock.close()
            self.log.info("Job locked '%s'" % job_id)
            return webob.Response(status=400, body=constants.ERROR_JOB_LOCKED)

        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        with storage_backend as store:
            if not store.isdir(self._job_dir(job_id)):
                return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)
            build_ids = self._get_build_numbers(store, job_id)
            if len(build_ids) > 0:
                new_build_number = str(max(build_ids) + 1)
            else:
                new_build_number = "1"

            try:
                store.mkdir(self._build_dir(job_id, new_build_number))
            except:
                self.log.exception("Build directory creation failed")
                if lock:
                    lock.unlock()
                    lock.close()
                return webob.Response(status=500, body=constants.ERROR_BUILD_CREATE_FAILED)

            if lock:
                lock.unlock()
                lock.close()

            build_state = { "status": "preparing" }
            try:
                with store.open(self._build_state_file(job_id, new_build_number), 'wb') as fileo:
                    json.dump(build_state, fileo)
            except:
                self.log.exception('Failed to write build state, job_id %s, build %s', job_id, new_build_number)
                return webob.Response(status=500, body=constants.ERROR_BUILD_WRITE_FAILED)

        if self.config.get('task_frontends'):
            for _ in range(10):
                task_id = self.distci_client.tasks.create()
                if task_id is not None:
                    break
            if task_id is None:
                self.log.error('Failed to create a build task')
                return webob.Response(status=500, body=constants.ERROR_BUILD_TASK_CREATION_FAILED)

            task_description = { 'capabilities': [ 'build_control_v1' ],
                                 'job_id': job_id,
                                 'build_number': new_build_number,
                                 'status': 'pending',
                                 'id': task_id }

            for _ in range(10):
                task_details = self.distci_client.tasks.update(task_id, task_description)
                if task_details is not None:
                    break
            if task_details is None:
                self.log.error("Build task creation failed")
                return webob.Response(status=500, body=constants.ERROR_BUILD_TASK_CREATION_FAILED)
        else:
            self.log.warn('No task frontends configured, unable to trigger build control task')

        return webob.Response(status=201, body=json.dumps({'job_id': job_id, 'build_number': int(new_build_number), 'state': build_state}), content_type="application/json")

    def get_build_state(self, job_id, build_id):
        """ Get job state """
        if validators.validate_build_id(build_id) != build_id:
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        build_data = None
        with storage_backend as store:
            if not store.isdir(self._build_dir(job_id, build_id)):
                return webob.Response(status=404, body=constants.ERROR_JOB_NOT_FOUND)
            for _ in range(10):
                try:
                    with store.open(self._build_state_file(job_id, build_id), 'rb') as fileo:
                        build_state = json.load(fileo)
                    build_data = json.dumps({'job_id': job_id, 'build_number': build_id, 'state': build_state})
                    break
                except (storage.NotFound, ValueError):
                    time.sleep(0.1)
                except:
                    self.log.exception("Exception while reading build state")
                    return webob.Response(status=500, body=constants.ERROR_INTERNAL)
        if not build_data:
            return webob.Response(status=409, body=constants.ERROR_BUILD_LOCKED)
        return webob.Response(status=200, body=build_data, content_type="application/json")

    def update_build_state(self, request, job_id, build_id):
        """ Update build state """
        try:
            build_state = json.load(request.body_file)
        except ValueError:
            self.log.exception('Failed to load build state')
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_PAYLOAD)
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        with storage_backend as store:
            if not store.isdir(self._build_dir(job_id, build_id)):
                return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)

            try:
                with store.open(self._build_state_file(job_id, build_id), 'wb') as fileo:
                    json.dump(build_state, fileo)
            except:
                self.log.exception('Failed to write build state, job_id %s, build %s', job_id, build_id)
                return webob.Response(status=500, body=constants.ERROR_BUILD_WRITE_FAILED)

        return webob.Response(status=200, body=json.dumps({'job_id': job_id, 'build_number': int(build_id), 'state': build_state}), content_type="application/json")

    def get_console_log(self, job_id, build_id):
        """ Return contents of the console log """
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        console_log = ''
        with storage_backend as store:
            if not store.isdir(self._build_dir(job_id, build_id)):
                return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)
            try:
                with store.open(self._console_log_file(job_id, build_id), 'rb') as fileo:
                    console_log = fileo.read()
            except storage.NotFound:
                # can be ignored, we just return empty log
                pass
            except:
                self.log.exception("Exception while reading console log")
        return webob.Response(status=200, body=console_log, content_type="text/plain")

    def update_console_log(self, request, job_id, build_id):
        """ Append content to the console log """
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        with storage_backend as store:
            if not store.isdir(self._build_dir(job_id, build_id)):
                return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)

            try:
                log = request.body_file.read()
                with store.open(self._console_log_file(job_id, build_id), 'ab') as fileo:
                    fileo.write(log)
            except:
                self.log.exception("Exception while updating console log")
                # FIXME: ignored for now
        return webob.Response(status=204)

    def update_workspace(self, request, job_id, build_id):
        """ Store workspace archive """
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        with storage_backend as store:
            if not store.isdir(self._build_dir(job_id, build_id)):
                return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)

            data_len = request.content_length
            ifh = request.body_file

            try:
                ofh = store.open(self._build_workspace_file(job_id, build_id), 'wb')
            except:
                self.log.exception("Failed to open workspace for writing")
                return webob.Response(status=500, body=constants.ERROR_BUILD_WRITE_FAILED)

            try:
                while data_len > 0:
                    read_len = data_len
                    if read_len > 1024*128:
                        read_len = 1024*128
                    data = ifh.read(read_len)
                    ofh.write(data)
                    data_len = data_len - len(data)
            except:
                self.log.exception("Exception while updating workspace")
                ofh.close()
                return webob.Response(status=500, body=constants.ERROR_BUILD_WRITE_FAILED)

            ofh.close()

        return webob.Response(status=204)

    def get_workspace(self, job_id, build_id):
        """ Get workspace archive """
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        with storage_backend as store:
            if not store.isfile(self._build_workspace_file(job_id, build_id)):
                return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)

            try:
                ifh = store.open(self._build_workspace_file(job_id, build_id), 'rb')
            except storage.NotFound:
                return webob.Response(status=500, body=constants.ERROR_BUILD_READ_FAILED)
            except:
                self.log.exception("Exception in get workspace")
                return webob.Response(status=500, body=constants.ERROR_BUILD_READ_FAILED)

            file_len = store.getsize(self._build_workspace_file(job_id, build_id))

        return webob.Response(status=200, body_file=ifh, content_length=file_len, content_type="application/octet-stream")

    def delete_workspace(self, job_id, build_id):
        """ Delete workspace archive """
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        with storage_backend as store:
            if not store.isfile(self._build_workspace_file(job_id, build_id)):
                return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)

            try:
                store.unlink(self._build_workspace_file(job_id, build_id))
            except storage.NotFound:
                return webob.Response(status=500, body=constants.ERROR_BUILD_WRITE_FAILED)
            except:
                self.log.exception("Exception while deleting workspace")
                return webob.Response(status=500, body=constants.ERROR_BUILD_WRITE_FAILED)

        return webob.Response(status=204)

    def delete_build(self, job_id, build_id):
        """ Delete a specific build and all related data """
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if self.cephmonitors:
            storage_backend = storage.CephFSStorage(','.join(self.cephmonitors))
        else:
            storage_backend = storage.LocalFSStorage()
        with storage_backend as store:
            if not store.isdir(self._build_dir(job_id, build_id)):
                return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)
            try:
                store.rmtree(self._build_dir(job_id, build_id))
            except storage.NotFound:
                return webob.Response(status=204)
            except:
                self.log.exception("Exception on delete build")
                return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)
        return webob.Response(status=204)

    def handle_request(self, request, job_id, parts):
        """ Handle requests related to builds """
        if validators.validate_job_id(job_id) == None:
            self.log.error('Invalid job_id: %r' % job_id)
            return webob.Response(status=400, body=constants.ERROR_JOB_INVALID_ID)

        if len(parts) == 0:
            if request.method == 'GET':
                return self.get_builds(job_id)
            elif request.method == 'POST':
                return self.trigger_build(job_id)
        elif len(parts) == 1:
            if request.method == 'GET':
                return self.get_build_state(job_id, parts[0])
            elif request.method == 'DELETE':
                return self.delete_build(job_id, parts[0])
        elif parts[1] == 'artifacts':
            return self.jobs_builds_artifacts.handle_request(request, job_id, parts[0], parts[2:])
        elif len(parts) == 2:
            if parts[1] == 'state' and request.method == 'GET':
                return self.get_build_state(job_id, parts[0])
            elif parts[1] == 'state' and request.method == 'PUT':
                return self.update_build_state(request, job_id, parts[0])
            elif parts[1] == 'console' and request.method == 'GET':
                return self.get_console_log(job_id, parts[0])
            elif parts[1] == 'console' and request.method == 'POST':
                return self.update_console_log(request, job_id, parts[0])
            elif parts[1] == 'workspace' and request.method == 'GET':
                return self.get_workspace(job_id, parts[0])
            elif parts[1] == 'workspace' and request.method == 'PUT':
                return self.update_workspace(request, job_id, parts[0])
            elif parts[1] == 'workspace' and request.method == 'DELETE':
                return self.delete_workspace(job_id, parts[0])

        return webob.Response(status=400)

