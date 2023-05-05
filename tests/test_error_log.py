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
import logging

import pytest
from telegram.constants import ParseMode

from ptbcontrib.error_log import ErrorBroadcastHandler

logger = logging.getLogger(__name__)

CHAT_ID_1 = -1000000000
CHAT_ID_2 = -2000000000


class TestErrorLog:
    test_flag = False

    @pytest.fixture(scope="function", autouse=True)
    def reset(self):
        self.test_flag = False

    async def test_error_log(self, bot, monkeypatch, caplog):
        logging.getLogger().addHandler(ErrorBroadcastHandler(bot, [logging.ERROR], CHAT_ID_1))

        expected_kwargs = {
            "chat_id": CHAT_ID_1,
            "text": "error",
            "disable_notification": True,
            "parse_mode": ParseMode.HTML,
        }

        def make_assertion(**kw):
            self.test_flag = kw == expected_kwargs

        monkeypatch.setattr(bot, "send_message", make_assertion)

        logger.error("error")

        assert self.test_flag
        assert caplog.records[0].msg == "error"
