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
"""This module contains logging handler which pipes logs to a Telegram chat."""
from logging import BASIC_FORMAT, Formatter, LogRecord
from logging.handlers import HTTPHandler
from typing import Any, Dict, List, Optional

import requests
from telegram.constants import ParseMode

TELEGRAM_API_HOST = "api.telegram.org"
TELEGRAM_API_URL = "bot{token}/sendMessage"


class PTBChatLoggingHandler(HTTPHandler):
    """
    A handler class which sends the logging records, appropriately formatted,
    to a Telegram chat.

    Args:
        token (str): The Telegram bot token.
        levels (:obj:`list` of :obj:`int`): The logging levels handled.
        chat_id (int): The ID of the recipient Telegram chat.
        log_format (str): The format string for the logger.
        parse_mode (:obj:`bool`, optional): The parse mode for Telegram, e.g. HTML.
        disable_notification (:obj:`bool`, optional): The API flag to disable notifications.
        disable_web_page_preview (:obj:`bool`, optional): The API flag to disable web page preview.
    """

    def __init__(
        self,
        token: str,
        levels: List[int],
        chat_id: int,
        *,
        log_format: str = BASIC_FORMAT,
        parse_mode: Optional[ParseMode] = None,
        disable_notification: Optional[bool] = None,
        disable_web_page_preview: Optional[bool] = None,
    ):
        # `method` and `secure` arguments are technically not needed as we use the requests library
        # passing them for visibility
        super().__init__(
            TELEGRAM_API_HOST, TELEGRAM_API_URL.format(token=token), method="POST", secure=True
        )
        self.setFormatter(Formatter(log_format))
        self.levels = levels
        self.chat_id = str(chat_id)
        self.parse_mode = parse_mode
        self.disable_notification = disable_notification
        self.disable_web_page_preview = disable_web_page_preview

    def mapLogRecord(self, record: LogRecord) -> Dict[str, Any]:
        """
        Override the default HTTPHandler implementation of mapping the log record to data.

        Args:
            record (:obj:`LogRecord`): The entity to be logged.

        Returns:
            dict(str, :obj:`Any`): The payload for the requests.post call.
        """
        payload = {
            "text": self.format(record),
            "chat_id": self.chat_id,
        }  # type: Dict[str, Any]
        # could use a lambda here if more arguments needed
        if self.parse_mode is not None:
            payload["parse_mode"] = self.parse_mode
        if self.disable_web_page_preview is not None:
            payload["disable_web_page_preview"] = self.disable_web_page_preview
        if self.disable_notification is not None:
            payload["disable_notification"] = self.disable_notification
        return payload

    def emit(self, record: LogRecord) -> None:
        """
        Emit a record.
        Sends the formatted log to Telegram API via requests.post method.

        Args:
            record (:obj:`LogRecord`): The entity to be logged.
        """
        if record.levelno in self.levels:
            try:
                requests.post(
                    f"https://{self.host}/{self.url}",
                    data=self.mapLogRecord(record),
                    headers={"content-type": "application/json"},
                )
            except Exception:  # pylint: disable=W0718
                self.handleError(record)
