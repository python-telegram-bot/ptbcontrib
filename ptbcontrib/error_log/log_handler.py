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
"""This module contains a helper function to pipe logging messages to Telegram chat."""
from logging import LogRecord, StreamHandler
from typing import List

from telegram import Bot
from telegram.constants import ParseMode


class ErrorBroadcastHandler(StreamHandler):
    """
    Allows to send records from logging module to a specified Telegram chat.

    Args:
        bot (:obj:`Bot`): The bot object
        levels (:obj:`List[int]`): List of logging levels caught by this handler
    """

    def __init__(
        self,
        bot: Bot,
        levels: List[int],
        chat_id: int,
        is_silent: bool = True,
    ):
        super().__init__()
        self.levels = levels
        self.send = lambda msg: bot.send_message(
            text=msg, chat_id=chat_id, disable_notification=is_silent, parse_mode=ParseMode.HTML
        )
        self.is_muted = False

    def emit(self, record: LogRecord) -> None:
        """
        Handles the LogRecord

        Args:
            record (:obj:`LogRecord`):
        """
        super().emit(record)
        if record.levelno in self.levels and not self.is_muted:
            try:
                msg = self.format(record)
                self.send(msg)
            except Exception:  # pylint: disable=W0718
                self.handleError(record)

    def set_muted(self, is_muted: bool) -> None:
        """
        Disables the handler
        """
        self.is_muted = is_muted
