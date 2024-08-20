# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2024
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
"""This module contains LogForwarder class"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable

from telegram.constants import ParseMode
from telegram.ext import ExtBot


class LogForwarder(logging.Handler):
    """
    Logging handler to forward specific logs to Telegram chats.
    """

    def __init__(
        self,
        bot: ExtBot,
        chat_ids: Iterable[int],
        parse_mode: ParseMode = ParseMode.MARKDOWN_V2,
        log_levels: Iterable[str] = ("WARN", "ERROR"),
    ):
        super().__init__()
        self._bot = bot
        self._chat_ids = chat_ids
        self._parse_mode = parse_mode
        self._log_levels = log_levels
        self._loop = asyncio.get_event_loop()

    def format_tg_msg(self, text: str) -> str:
        """
        Formats the log message to be sent to Telegram.
        Override this method to customize the message.
        The default implementation applies the handler's formatter
        and puts the result in a Markdown code block.
        """

        msg = "```\n" + text + "\n```"
        return msg

    def emit(self, record: logging.LogRecord) -> None:
        try:
            formatted = self.format(record)
            msg = self.format_tg_msg(formatted)
            if record.levelname in self._log_levels:
                for chat_id in self._chat_ids:
                    f = self._bot.send_message(
                        chat_id=chat_id, text=msg, parse_mode=self._parse_mode
                    )
                    asyncio.run_coroutine_threadsafe(f, self._loop)
        except RecursionError:  # https://bugs.python.org/issue36272
            raise
        except Exception:  # pylint: disable=W0703
            self.handleError(record)
