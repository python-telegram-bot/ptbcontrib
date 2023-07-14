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
"""This file contains PTBStoreAdapter."""
from typing import Any

from apscheduler.job import Job as APSJob
from telegram.ext import Application, Job


class PTBStoreAdapter:
    """
    Store Adapter to make :class:`telegram.ext.Job` class storable.
    """

    def __init__(self, application: Application, **kwargs: Any) -> None:
        """
        Args:
            application (:class:`telegram.ext.Application`): Application instance
                that will be passed to CallbackContext when recreating jobs.
            **kwargs (:obj:`dict`): Arbitrary keyword Arguments to be passed to
                the JobStore constructor.
        """

        self.application = application
        super().__init__(**kwargs)

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
        # Get the tg_job instance in memory
        tg_job = Job.from_aps_job(job)
        # or the one that we deserialized during _reconstitute (first arg in args)
        # Extract relevant information from the job and
        # store it in the job's args.
        prepped_job.args = (
            tg_job.name,
            tg_job.data,
            tg_job.chat_id,
            tg_job.user_id,
            tg_job.callback,
        )
        return prepped_job

    def _restore_job(self, job: APSJob) -> APSJob:
        """
        Restore all telegram.ext.Job data.
        Args:
            job (:obj:`apscheduler.job`): The job to be processed.
        """
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
                self.application,
                tg_job,
            )
        )
        return job
