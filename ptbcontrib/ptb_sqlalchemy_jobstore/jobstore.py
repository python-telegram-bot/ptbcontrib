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
"""This file contains PTBSQLAlchemyJobStore."""
import logging
from typing import Any

from apscheduler.job import Job as APSJob
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from telegram.ext import Application, Job

logger = logging.getLogger(__name__)


class PTBSQLAlchemyJobStore(SQLAlchemyJobStore):
    """
    Wraps apscheduler.SQLAlchemyJobStore to make :class:`telegram.ext.Job` class storable.
    """

    def __init__(self, application: Application, **kwargs: Any) -> None:
        """
        Args:
            application (:class:`telegram.ext.Application`): Application instance
                that will be passed to CallbackContext when recreating jobs.
            **kwargs (:obj:`dict`): Arbitrary keyword Arguments to be passed to
                the SQLAlchemyJobStore constructor.
        """

        if "url" in kwargs and kwargs["url"].startswith("sqlite:///"):
            logger.warning(
                "Use of SQLite db is not supported  due to "
                "multi-threading limitations of SQLite databases "
                "You can still try to use it, but it will likely "
                "behave differently from what you expect."
            )

        super().__init__(**kwargs)
        self.application = application

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

    @staticmethod
    def _prepare_job(job: APSJob) -> APSJob:
        """
        Erase all unpickable data from telegram.ext.Job
        Args:
            job (:obj:`apscheduler.job`): The job to be processed.
        """
        # make new job which is copy of actual job cause
        # modifying actual job also modifies jobs in threadpool
        # executor which are currently running/going to run, and
        # we'll get incorrect argument instead of CallbackContext.
        prepped_job = APSJob.__new__(APSJob)
        prepped_job.__setstate__(job.__getstate__())
        # Extract relevant information from the job and
        # store it in the job's args.
        tg_job = Job._from_aps_job(job)  # pylint: disable=W0212
        prepped_job.args = (
            tg_job.name,
            tg_job.data,
            tg_job.chat_id,
            tg_job.user_id,
            tg_job.callback,
        )
        return prepped_job

    def _reconstitute_job(self, job_state: bytes) -> APSJob:
        """
        Called from apscheduler's internals when loading job.
        Args:
            job_state (:obj:`str`): String containing pickled job state.
        """
        job: APSJob = super()._reconstitute_job(job_state)  # pylint: disable=W0212

        name, data, chat_id, user_id, callback = job.args
        tg_job = Job(
            callback=callback,
            chat_id=chat_id,
            user_id=user_id,
            name=name,
            data=data,
        )
        job._modify(  # pylint: disable=W0212
            args=(
                tg_job,
                self.application,
            )
        )
        return job
