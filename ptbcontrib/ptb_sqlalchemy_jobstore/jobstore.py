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
"""This file contains PTBSQLAlchemyJobStore."""

import logging
from typing import Any
import telegram
from apscheduler.job import Job as APSJob

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from telegram.ext import CallbackContext, Dispatcher, ConversationHandler


logger = logging.getLogger(__name__)


class PTBSQLAlchemyJobStore(SQLAlchemyJobStore):
    """
    Wraps apscheduler.SQLAlchemyJobStore to make :class:`telegram.ext.Job` class storable.
    """

    def __init__(self, dispatcher: Dispatcher, **kwargs: Any) -> None:
        """
        Args:
            dispatcher (:class:`telegram.ext.Dispatcher`): Dispatcher instance
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
        self.dispatcher = dispatcher
        self.timeout_check_passed = False

    def add_job(self, job: APSJob) -> None:
        """
        Called from apscheduler's internals after adding a new job.
        Args:
            job (:obj:`apscheduler.job`): The job to be persisted.
        """
        if not self.timeout_check_passed:
            self._check_ch_timeouts()
            self.timeout_check_passed = True

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
        # executor which are currently running/going to run and
        # we'll get incorrect argument instead of CallbackContext.
        prepped_job = APSJob.__new__(APSJob)
        prepped_job.__setstate__(job.__getstate__())
        # remove CallbackContext from job args since
        # it includes refrences to dispatcher which
        # is unpickleable. we'll recreate CallbackContext
        # in _reconstitute_job method.
        if isinstance(job.args[0], CallbackContext):
            tg_job = job.args[0].job
            # APScheduler stores args as tuple.
            prepped_job.args = (tg_job.name, tg_job.context)
        return prepped_job

    def _reconstitute_job(self, job_state: bytes) -> APSJob:
        """
        Called from apscheduler's internals when loading job.
        Args:
            job_state (:obj:`str`): String containing pickled job state.
        """
        job = super()._reconstitute_job(job_state)  # pylint: disable=W0212

        # Here we rebuild callback context for the job which
        # are going for execution.
        tg_job = telegram.ext.Job(
            callback=None,
            name=job.args[0],
            context=job.args[1],
        )
        ctx = CallbackContext.from_job(tg_job, self.dispatcher)
        job._modify(args=(ctx,))  # pylint: disable=W0212
        return job

    def _check_ch_timeouts(self) -> None:
        """
        Called on first run of add_job and checks if there are
        any ConversationHandlers with active conversation_timeout.
        """

        for group in self.dispatcher.handlers:
            for handler in self.dispatcher.handlers.get(group):
                if isinstance(handler, ConversationHandler):
                    if handler.conversation_timeout is not None:
                        raise Exception(
                            "PTBSQLAlchemyJobStore does not support ConversationHandlers with timeouts!"
                        )
