#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2026
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
import pytest
from telegram import Chat
from telegram.error import BadRequest

from ptbcontrib.get_chat_link import get_chat_link

from .conftest import make_bot


@pytest.fixture(scope="module")
def bot_factory():
    bot = make_bot()
    post = bot._post
    yield bot
    bot._post = post


@pytest.fixture(scope="function")
def chat(bot_factory):
    chat = Chat(1, type="channel", title="test channel")
    chat.set_bot(bot_factory)
    chat._unfreeze()
    return chat


@pytest.fixture(scope="function")
def bot_chat_dict():
    return {
        "id": 1,
        "type": "channel",
        "title": "test channel",
    }


class TestChatToLink:
    async def test_chat_username(self, chat):
        username = "test_username"
        chat.username = username

        link = await get_chat_link(chat)

        assert link == f"https://t.me/{username}"

    async def test_chat_invite_link(self, chat):
        invite_link = "https://t.me/joinchat/RQ4-ELmRIl82ZDZk"
        chat.invite_link = invite_link

        link = await get_chat_link(chat)

        assert link == invite_link

    async def test_bot_chat_invite_link(self, chat, bot_chat_dict, monkeypatch):
        invite_link = "https://t.me/joinchat/RQ4-ELmRIl82ZDZk"
        res = bot_chat_dict
        res["invite_link"] = invite_link

        async def post(*args, **kwargs):
            return bot_chat_dict

        monkeypatch.setattr(chat.get_bot().request, "post", post)

        link = await get_chat_link(chat)

        assert link == invite_link

    async def test_export_chat_invite_link(self, chat, bot_chat_dict, monkeypatch):
        invite_link = "https://t.me/joinchat/m4Zho4YdtexiMzI0"
        call = [0]

        async def post(*args, **kwargs):
            if call[0] == 0:
                call[0] += 1
                return bot_chat_dict
            return invite_link

        monkeypatch.setattr(chat.get_bot().request, "post", post)

        link = await get_chat_link(chat)

        assert link == invite_link

    async def test_bot_permission_error(self, chat, bot_chat_dict, monkeypatch):
        call = [0]

        async def post(*args, **kwargs):
            if call[0] == 0:
                call[0] += 1
                return bot_chat_dict
            raise BadRequest("Not enough rights to manage chat invite link")

        monkeypatch.setattr(chat.get_bot().request, "post", post)

        link = await get_chat_link(chat)

        assert link is None

    async def test_bot_other_error(self, chat, bot_chat_dict, monkeypatch):
        call = [0]

        async def post(*args, **kwargs):
            if call[0] == 0:
                call[0] += 1
                return bot_chat_dict
            raise BadRequest("Some other error")

        monkeypatch.setattr(chat.get_bot().request, "post", post)

        with pytest.raises(BadRequest):
            await get_chat_link(chat)
