#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2022
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
"""This module contains a filter class that applies filters to Message.reply_to_message."""
from typing import Dict, Optional, Union

from telegram import Update
from telegram.ext.filters import BaseFilter, UpdateFilter


class ReplyToMessageFilter(UpdateFilter):
    """
    Applies filters to ``update.effective_message.reply_to_message``.

    Args:
        filters (:class:`telegram.ext.BaseFilter`): The filters to apply. Pass exactly like passing
            filters to :class:`telegram.ext.MessageHandler`.

    Attributes:
        filters (:class:`telegram.ext.BaseFilter`): The filters to apply.
    """

    def __init__(self, filters: BaseFilter):
        super().__init__(name=str(filters), data_filter=filters.data_filter)
        self.filters = filters

    def filter(self, update: Update) -> Optional[Union[bool, Dict]]:
        """See :meth:`telegram.ext.BaseFilter.filter`."""
        if not update.effective_message.reply_to_message:
            return False

        reply_to_message = update.effective_message.reply_to_message
        if update.channel_post:
            return self.filters.check_update(Update(1, channel_post=reply_to_message))
        if update.edited_channel_post:
            return self.filters.check_update(Update(1, edited_channel_post=reply_to_message))
        if update.message:
            return self.filters.check_update(Update(1, message=reply_to_message))
        if update.edited_message:
            return self.filters.check_update(Update(1, edited_message=reply_to_message))
        return False
