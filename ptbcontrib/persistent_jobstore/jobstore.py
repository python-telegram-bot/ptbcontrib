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
"""This fine contains AdaptedSQLAlchemyJobStore."""


import pickle  # skipcq: BAN-B403
import telegram

import apscheduler.job
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from telegram.ext import CallbackContext, Dispatcher


class AdaptedSQLAlchemyJobStore(SQLAlchemyJobStore):
    """
    Wraps apscheduler.SQLAlchemyJobStore to make telegram Job class storable.
    """

    def __init__(self, dispatcher: Dispatcher, *args, **kwargs) -> None:
        """
        :param dispatcher (:class:`telegram.ext.Dispatcher`): Dispatcher instance
            that will be passed to CallbackContext when recreating jobs.
        :param args: Arguments to be passed to the SQLAlchemyJobStore constructor.
        """

        super(AdaptedSQLAlchemyJobStore, self).__init__(*args, **kwargs)
        self.dispatcher = dispatcher

    def add_job(self, job: apscheduler.job) -> None:
        """
        Called from apscheduler's internals after adding a new job.
        Args:
            job (:obj:`apscheduler.job`): The job to be persisted.
        """

        job = self._prepare_job(job)
        super(AdaptedSQLAlchemyJobStore, self).add_job(job)

    def update_job(self, job: apscheduler.job) -> None:
        """
        Called from apscheduler's internals after updating a job.
        Args:
            job (:obj:`apscheduler.job`): The job to be updated.
        """
        job = self._prepare_job(job)
        super(AdaptedSQLAlchemyJobStore, self).update_job(job)

    @staticmethod
    def _prepare_job(job: apscheduler.job) -> apscheduler.job:
        """
        Erase all unpickable data from telegram.ext.Job
        Args:
            job (:obj:`apscheduler.job`): The job to be processed.
        """

        # while updating existing job, job.args[0]
        # will be a dict fetched from db instead
        # of CallbackContext.
        if isinstance(job.args[0], dict):
            job_elements = job.args[0]
        else:
            # CallbackContext.job
            tg_job = job.args[0].job
            job_elements = {"context": tg_job.context, "name": tg_job.name}

        job.args = (job_elements,)  # ensure tuple by (,)
        return job

    def _reconstitute_job(self, job_state: str) -> apscheduler.job:
        """
        Called from apscheduler's internals when loading job.
        Args:
            job_state (:obj:`str`): String containing pickled job state.
        """
        job_state = pickle.loads(job_state)  # skipcq: BAN-B301
        telegram_job_elements = job_state["args"][0]
        tg_job = telegram.ext.Job(
            callback=None,
            context=telegram_job_elements["context"],
            name=telegram_job_elements["name"],
        )
        ctx = CallbackContext.from_job(tg_job, self.dispatcher)
        # picked from SQLAlchemyJobStore._reconstitute_job
        job_state["args"] = (ctx,)
        job_state["jobstore"] = self
        job = apscheduler.job.Job.__new__(apscheduler.job.Job)
        job.__setstate__(job_state)
        job._scheduler = self._scheduler  # skipcq: PYL-W0212
        job._jobstore_alias = self._alias  # skipcq: PYL-W0212
        return job
