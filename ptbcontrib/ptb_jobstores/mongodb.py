#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2023
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
"""This file contains PTBMongoDBJobStore."""
from typing import Any

from apscheduler.job import Job as APSJob
from apscheduler.jobstores.mongodb import MongoDBJobStore
from telegram.ext import Application, Job

from .ptb_adapter import PTBStoreAdapter


class PTBMongoDBJobStore(PTBStoreAdapter, MongoDBJobStore):
    """
    Wraps apscheduler.MongoDBJobStore to make :class:`telegram.ext.Job` class storable.
    """

    def __init__(self, application: Application, **kwargs: Any) -> None:
        """
        Args:
            application (:class:`telegram.ext.Application`): Application instance
                that will be passed to CallbackContext when recreating jobs.
            **kwargs (:obj:`dict`): Arbitrary keyword Arguments to be passed to
                the MongoDBJobStore constructor.
        """

        super().__init__(application, **kwargs)

    def add_job(self, job: APSJob) -> None:
        """
        Called from apscheduler's internals after adding a new job.
        Args:
            job (:obj:`apscheduler.job`): The job to be persisted.
        """
        job = self._prepare_job(job)
        super().add_job(job)

    def update_job(self, job: APSJob) -> None:
        """
        Called from apscheduler's internals after updating a job.
        Args:
            job (:obj:`apscheduler.job`): The job to be updated.
        """
        job = self._prepare_job(job)
        super().update_job(job)
