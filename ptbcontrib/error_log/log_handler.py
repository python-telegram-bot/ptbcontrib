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
from logging import BASIC_FORMAT, Formatter, LogRecord, StreamHandler
from typing import List

from telegram import Bot


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
        log_format: str = BASIC_FORMAT,
        # pylint: disable=R0913, W0102
        send_message_kwargs: dict = {},
    ):
        super().__init__()
        self.setFormatter(Formatter(log_format))
        self.levels = levels
        self.send = lambda msg: bot.send_message(
            text=msg,
            chat_id=chat_id,
            **send_message_kwargs,
        )

    def emit(self, record: LogRecord) -> None:
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.

        Args:
            record (:obj:`LogRecord`): The LogRecord object from logging.
        """
        if record.levelno in self.levels:
            try:
                msg = self.format(record)
                self.send(msg)
            except Exception:  # pylint: disable=W0718
                self.handleError(record)
