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
from unittest.mock import Mock

import pytest
from telegram import Chat
from telegram.error import BadRequest
from ptbcontrib.chat_to_link import get_chat_link

from .conftest import make_bot


@pytest.fixture(scope="module")
def bot_factory():
    bot = make_bot()
    post = bot._post
    yield bot
    bot._post = post


@pytest.fixture(scope="function")
def chat(bot_factory):
    return Chat(1, type="channel", name="test channel", bot=bot_factory)


@pytest.fixture(scope="function")
def bot_chat_dict():
    return {
        'id': 1,
        'type': 'channel',
        'title': 'test channel',
    }


class TestChatToLink:
    def test_chat_username(self, chat):
        username = "test_username"
        chat.username = username

        link = get_chat_link(chat)

        assert link == f"https://t.me/{username}"

    def test_chat_invite_link(self, chat):
        invite_link = "https://t.me/joinchat/RQ4-ELmRIl82ZDZk"
        chat.invite_link = invite_link

        link = get_chat_link(chat)

        assert link == invite_link

    def test_bot_chat_invite_link(self, chat, bot_chat_dict):
        invite_link = "https://t.me/joinchat/RQ4-ELmRIl82ZDZk"
        res = bot_chat_dict
        res["invite_link"] = invite_link
        chat.bot._post = Mock(side_effect=[bot_chat_dict])

        link = get_chat_link(chat)

        assert link == invite_link

    def test_export_chat_invite_link(self, chat, bot_chat_dict):
        invite_link = 'https://t.me/joinchat/m4Zho4YdtexiMzI0'
        res = invite_link
        chat.bot._post = Mock(side_effect=[bot_chat_dict, res])

        link = get_chat_link(chat)

        assert link == invite_link

    def test_bot_permission_error(self, chat, bot_chat_dict):
        chat.bot._post = Mock(
            side_effect=[bot_chat_dict, BadRequest("Not enough rights to manage chat invite link")]
        )

        link = get_chat_link(chat)

        assert link is None

    def test_bot_other_error(self, chat, bot_chat_dict):
        chat.bot._post = Mock(side_effect=[bot_chat_dict, BadRequest("Some other error")])

        with pytest.raises(BadRequest):
            get_chat_link(chat)
