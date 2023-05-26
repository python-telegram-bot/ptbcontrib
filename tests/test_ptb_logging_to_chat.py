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

try:
    # python-telegram-bot >= 20.0.0
    from telegram.constants import ParseMode
except ImportError:
    # python-telegram-bot < 20.0.0
    from telegram import ParseMode

from ptbcontrib.ptb_logging_to_chat import PTBChatLoggingHandler

logger = logging.getLogger(__name__)

TOKEN = "TOKEN"
CHAT_ID_1 = -1000000000
CHAT_ID_2 = -2000000000


@pytest.fixture(scope="function")
def argtest():
    class TestArgs:
        was_called = False

        def __call__(self, data):
            self.was_called = True
            self.data = data

    return TestArgs()


@pytest.fixture(autouse=True)
def clean_logging_handlers():
    logger.handlers.clear()


class TestPTBLoggingToChat:
    @pytest.mark.parametrize(
        "levels, chat_id, was_called, data",
        [
            [
                [logging.ERROR],
                CHAT_ID_1,
                True,
                {
                    "chat_id": str(CHAT_ID_1),
                    "text": "ERROR:tests.test_ptb_logging_to_chat:message",
                },
            ],
            [[logging.WARNING], CHAT_ID_1, False, None],
            [
                [logging.WARNING, logging.ERROR],
                CHAT_ID_1,
                True,
                {
                    "chat_id": str(CHAT_ID_1),
                    "text": "ERROR:tests.test_ptb_logging_to_chat:message",
                },
            ],
        ],
    )
    @pytest.mark.asyncio
    async def test_send_log(self, monkeypatch, argtest, levels, chat_id, was_called, data):
        logger.addHandler(PTBChatLoggingHandler(TOKEN, levels, chat_id))

        monkeypatch.setattr(PTBChatLoggingHandler, "_emit", argtest)

        logger.error("message")

        assert argtest.was_called == was_called
        if was_called:
            assert argtest.data == data

    async def test_send_2_chats(self, monkeypatch, argtest):
        logger.addHandler(PTBChatLoggingHandler(TOKEN, [logging.ERROR], CHAT_ID_1))
        logger.addHandler(PTBChatLoggingHandler(TOKEN, [logging.WARNING], CHAT_ID_2))

        monkeypatch.setattr(PTBChatLoggingHandler, "_emit", argtest)

        logger.error("message")

        assert argtest.was_called is True
        assert argtest.data == {
            "chat_id": str(CHAT_ID_1),
            "text": "ERROR:tests.test_ptb_logging_to_chat:message",
        }

        argtest.was_called = False
        logger.warning("message")

        assert argtest.was_called is True
        assert argtest.data == {
            "chat_id": str(CHAT_ID_2),
            "text": "WARNING:tests.test_ptb_logging_to_chat:message",
        }

    async def test_send_html_encoded(self, monkeypatch, argtest):
        logger.addHandler(
            PTBChatLoggingHandler(
                TOKEN,
                [logging.ERROR],
                CHAT_ID_1,
                log_format="<code>%(name)s\t- %(levelname)s\t- %(message)s</code>",
                parse_mode=ParseMode.HTML,
            )
        )

        monkeypatch.setattr(PTBChatLoggingHandler, "_emit", argtest)

        logger.error("message")

        assert argtest.was_called is True
        assert argtest.data == {
            "chat_id": str(CHAT_ID_1),
            "text": "<code>tests.test_ptb_logging_to_chat\t- ERROR\t- message</code>",
            "parse_mode": ParseMode.HTML,
        }

    async def test_send_exception(self, monkeypatch, argtest, capsys):
        logger.addHandler(PTBChatLoggingHandler(TOKEN, [logging.ERROR], CHAT_ID_1))

        def mock(**_kw):
            raise RuntimeError("Error")

        monkeypatch.setattr(PTBChatLoggingHandler, "_emit", mock)

        logger.error("message")

        assert argtest.was_called is False
        captured = capsys.readouterr()
        assert "--- Logging error ---" in captured.err
        assert "Message: 'message'" in captured.err
