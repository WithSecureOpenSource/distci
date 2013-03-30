"""
Test DistCI input validation routines

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

from distci.frontend import validators

class TestValidators:
    valid_task_ids = [
            '00000000-0000-0000-0000-000000000000',
            'be1a4893-aada-4fa1-980c-46fc30e196c6'
        ]
    invalid_task_ids = [
            '00000000-0000-0000-0000-00000000000',
            '00000000-0000-0000-0000-0000000000000',
            '000000000-000-000-000000-00000000000',
            '00000000000000000000000000000000',
            '00000000-0000-0000-0000-00000000000F',
            '00000000-0000-0000-0000-00000000000g',
            '..',
            '00000000-0000-0000-0000-000000000000/..',
            '00000000-0000-0000-0000-00\\000000000',
            '00000000-0000-/000-0000-000000000000'
        ]

    valid_job_ids = [
            'myjob',
            'my_job',
            'my-job-2',
            'abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ-0123456789'
        ]

    invalid_job_ids = [
            '/etc/passwd',
            '..',
            '/',
            'my+job',
            '(my)job',
            'my:job'
        ]

    valid_build_ids = [
            '1',
            '1234567890123456'
    ]

    invalid_build_ids = [
            '/etc/passwd',
            '..',
            '/',
            'foobar',
            '123foobar',
            '12345678901234567'
    ]

    def test_01_valid_task_ids(self):
        for task_id in self.valid_task_ids:
            assert validators.validate_task_id(task_id) == task_id, "Validator declined valid task_id %s" % task_id

    def test_02_invalid_task_ids(self):
        for task_id in self.invalid_task_ids:
            assert validators.validate_task_id(task_id) is None, "Validator accepted invalid task_id %s" % task_id

    def test_03_valid_job_ids(self):
        for job_id in self.valid_job_ids:
            assert validators.validate_job_id(job_id) == job_id, "Validator declined valid job_id %s" % job_id

    def test_04_invalid_job_ids(self):
        for job_id in self.invalid_job_ids:
            assert validators.validate_job_id(job_id) is None, "Validator accepted invalid job_id %s" % job_id

    def test_05_valid_build_ids(self):
        for build_id in self.valid_build_ids:
            assert validators.validate_build_id(build_id) == build_id, "Validator declined valid build_id %s" % build_id

    def test_06_invalid_build_ids(self):
        for build_id in self.invalid_build_ids:
            assert validators.validate_build_id(build_id) is None, "Validator accepted invalid build_id %s" % build_id

