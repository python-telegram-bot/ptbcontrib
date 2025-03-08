#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2025
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

from __future__ import annotations

from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, create_autospec, patch

import pytest
from telegram import Chat, Contact, Message, SharedUser, UsersShared
from telegram.constants import ChatType

from ptbcontrib.extract_passed_user import extract, extract_passed_user, get_num_from_text
from ptbcontrib.username_to_chat_api import UsernameToChatAPI

if TYPE_CHECKING:
    from unittest.mock import MagicMock

chat = Chat(
    id=1,
    type=ChatType.PRIVATE,
    username="username",
    first_name="first_name",
    last_name="last_name",
)
message_fabric = partial(
    Message,
    message_id=1,
    date=datetime.now(),
    chat=chat,
)
shared_user = SharedUser(
    user_id=1,
    username=chat.username,
    first_name=chat.first_name,
    last_name=chat.last_name,
)


class TestGetNumsFromText:
    """test_get_nums_from_text"""

    @staticmethod
    @pytest.mark.parametrize(
        argnames="text, expected",
        argvalues=[
            ("abc123xyz", 123),
            ("98765", 98765),
            ("  ab#$@c9def8g7h6 ", 9),
        ],
    )
    def test_success(
        text: str,
        expected: int,
    ):
        assert (
            get_num_from_text(
                text=text,
            )
            == expected
        )

    @staticmethod
    def test_exceptions():
        for text in ("abcdef", ""):
            assert (
                get_num_from_text(
                    text=text,
                )
                is None
            )


def test_default_resolver():
    extract.default_resolver(
        username="username",
        wrapper=create_autospec(
            spec=UsernameToChatAPI,
            spec_set=True,
            instance=False,
        ),
    )


@pytest.fixture(
    scope="function",
)
def mock_message():
    result = create_autospec(
        spec=message_fabric(
            text="foo",
        ),
        users_shared=None,
        contact=None,
        spec_set=True,
    )
    result.get_bot.return_value.get_chat = AsyncMock(
        spec_set=True,
        return_value=chat,
    )
    yield result


async def test_shared_user():
    result = await extract_passed_user(
        message=message_fabric(
            users_shared=UsersShared(
                request_id=1,
                users=(shared_user,),
            ),
        ),
    )
    assert result == shared_user


async def test_text_username():
    async def resolver(
        **_,
    ):
        return chat

    result = await extract_passed_user(
        message=message_fabric(
            text="  foo 434 @username @second_user ",
        ),
        username_resolver=resolver,
    )
    assert result == shared_user


async def test_text_username_default_resolver():
    with patch.object(
        target=extract,
        attribute="default_resolver",
        autospec=True,
        spec_set=True,
        return_value=chat,
    ):
        result = await extract_passed_user(
            message=message_fabric(
                text="  @username ",
            ),
            username_resolver=create_autospec(
                spec=UsernameToChatAPI,
                spec_set=True,
                instance=False,
            ),
        )
        assert result == shared_user


async def test_contact_with_user_id(
    mock_message: MagicMock,
):
    mock_message.contact = Contact(
        phone_number="qwerty123",
        first_name="John",
        user_id=1,
    )
    result = await extract_passed_user(
        message=mock_message,
    )
    assert result == shared_user


async def test_contact_without_user_id():
    result = await extract_passed_user(
        message=message_fabric(
            contact=Contact(
                phone_number="qwerty123",
                first_name="John",
            ),
            users_shared=None,
        ),
    )
    assert result is None


async def test_text_with_user_id(
    mock_message: MagicMock,
):
    mock_message.text = " qwerty123 bla bla 456 "
    result = await extract_passed_user(
        message=mock_message,
    )
    assert result == shared_user
