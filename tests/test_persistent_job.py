#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2021
# The ptbcontrib developers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
import subprocess
import sys
import datetime as dtm
import pytest

from telegram.ext import JobQueue, CallbackContext

subprocess.check_call(
    [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        "ptbcontrib/persistent_jobstore/requirements.txt",
    ]
)

from ptbcontrib.persistent_jobstore import AdaptedSQLAlchemyJobStore


@pytest.fixture(scope='function')
def jq(_dp):
    jq = JobQueue()
    jq.set_dispatcher(_dp)
    job_store = AdaptedSQLAlchemyJobStore(dispatcher=_dp, url="sqlite:///:memory:")
    jq.scheduler.add_jobstore(job_store)
    jq.start()
    yield jq
    jq.stop()


def dummy_job(ctx):
    # check if arg is instance of CallbackContext or not
    # to make sure it's properly serialized
    assert isinstance(ctx, CallbackContext)


def test_default_jobstore_instance(jq):
    assert isinstance(jq.scheduler._jobstores["default"], AdaptedSQLAlchemyJobStore)


def test_next_runtime(jq):
    jq.run_repeating(dummy_job, 10, first=0)
    assert (
        jq.scheduler._jobstores["default"].get_next_run_time().second
        == dtm.datetime.now().second + 10
    )


def test_lookup_job(jq):
    initial_job = jq.run_once(dummy_job, 1)
    jobstore = jq.scheduler._jobstores["default"]
    job = jobstore.lookup_job(initial_job.id)
    assert job == initial_job.job


def test_non_existent_job(jq):
    assert jq.scheduler._jobstores["default"].lookup_job("foo") is None


def test_get_all_jobs(jq):
    j1 = jq.run_once(dummy_job, 1)
    j2 = jq.run_once(dummy_job, 2)
    j3 = jq.run_once(dummy_job, 3)
    jobs = jq.scheduler._jobstores["default"].get_all_jobs()
    assert jobs == [j1.job, j2.job, j3.job]


def test_remove_job(jq):
    j1 = jq.run_once(dummy_job, 1)
    j2 = jq.run_once(dummy_job, 2)
    jobstore = jq.scheduler._jobstores["default"]
    jobstore.remove_job(j1.id)
    assert jobstore.get_all_jobs() == [j2.job]
    jobstore.remove_job(j2.id)
    assert jobstore.get_all_jobs() == []
