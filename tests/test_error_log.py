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
from telegram.error import TelegramError

from ptbcontrib.error_log import ErrorBroadcastHandler

logger = logging.getLogger(__name__)

CHAT_ID_1 = -1000000000
CHAT_ID_2 = -2000000000


@pytest.fixture(scope="function")
def argtest():
    class TestArgs:
        was_called = False

        def __call__(self, *args, **kwargs):
            self.was_called = True
            self.args = list(args)
            self.kwargs = kwargs

    return TestArgs()


@pytest.fixture(autouse=True)
def clean_logging_handlers():
    logging.getLogger().handlers.clear()


class TestErrorLog:
    @pytest.mark.parametrize(
        "levels, chat_id, was_called, kwargs",
        [
            [
                [logging.ERROR],
                CHAT_ID_1,
                True,
                {
                    "chat_id": CHAT_ID_1,
                    "text": "ERROR:tests.test_error_log:message",
                },
            ],
            [[logging.WARNING], CHAT_ID_1, False, None],
            [
                [logging.WARNING, logging.ERROR],
                CHAT_ID_1,
                True,
                {
                    "chat_id": CHAT_ID_1,
                    "text": "ERROR:tests.test_error_log:message",
                },
            ],
        ],
    )
    async def test_send_log(self, bot, monkeypatch, argtest, levels, chat_id, was_called, kwargs):
        logging.getLogger().addHandler(ErrorBroadcastHandler(bot, levels, chat_id))

        monkeypatch.setattr(bot, "send_message", argtest)

        logger.error("message")

        assert argtest.was_called == was_called
        if was_called:
            assert argtest.kwargs == kwargs

    async def test_send_2_chats(self, bot, monkeypatch, argtest):
        logging.getLogger().addHandler(ErrorBroadcastHandler(bot, [logging.ERROR], CHAT_ID_1))
        logging.getLogger().addHandler(ErrorBroadcastHandler(bot, [logging.WARNING], CHAT_ID_2))

        monkeypatch.setattr(bot, "send_message", argtest)

        logger.error("message")

        assert argtest.was_called is True
        assert argtest.kwargs == {
            "chat_id": CHAT_ID_1,
            "text": "ERROR:tests.test_error_log:message",
        }

        argtest.was_called = False
        logger.warning("message")

        assert argtest.was_called is True
        assert argtest.kwargs == {
            "chat_id": CHAT_ID_2,
            "text": "WARNING:tests.test_error_log:message",
        }

    async def test_send_html_encoded(self, bot, monkeypatch, argtest):
        logging.getLogger().addHandler(
            ErrorBroadcastHandler(
                bot,
                [logging.ERROR],
                CHAT_ID_1,
                "<code>%(name)s\t- %(levelname)s\t- %(message)s</code>",
                {"parse_mode": ParseMode.HTML},
            )
        )

        monkeypatch.setattr(bot, "send_message", argtest)

        logger.error("message")

        assert argtest.was_called is True
        assert argtest.kwargs == {
            "chat_id": CHAT_ID_1,
            "text": "<code>tests.test_error_log\t- ERROR\t- message</code>",
            "parse_mode": ParseMode.HTML,
        }

    async def test_send_exception(self, bot, monkeypatch, argtest, capsys):
        logging.getLogger().addHandler(ErrorBroadcastHandler(bot, [logging.ERROR], CHAT_ID_1))

        def mock(**_kw):
            raise TelegramError("Error")

        monkeypatch.setattr(bot, "send_message", mock)

        logger.error("message")

        assert argtest.was_called is False
        captured = capsys.readouterr()
        assert "--- Logging error ---" in captured.err
        assert "Message: 'message'" in captured.err
