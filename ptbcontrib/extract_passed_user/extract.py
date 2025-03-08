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

"""This module attempts to extract side user passed actual user from incoming message"""

from __future__ import annotations
from typing import TYPE_CHECKING, Callable
import asyncio

from telegram.error import TelegramError
from telegram import SharedUser
from ..username_to_chat_api import UsernameToChatAPI

if TYPE_CHECKING:
    from telegram import Message, Chat


def get_nums_from_text(text: str, ) -> int | None:
    try:
        return int(''.join([letter for letter in text if letter.isdigit()]))
    except ValueError:
        return None


def default_resolver(wrapper: UsernameToChatAPI, username: str, ) -> Chat | None:
    # Catch exceptions from username_to_chat_api ?
    return asyncio.run(wrapper.resolve(username=username.strip(), ))


async def extract_passed_user(
        message: Message,
        username_resolver: Callable | UsernameToChatAPI | None = None,
) -> SharedUser | None:
    """
    4 cases:
    1. message.users_shared
    2. message.contact.user_id
    3. message.text starts with '@' and resolved by wrapper
    4. message.text has only numbers, resolved by get_nums_from_text

    About contact entity:
        1. `contact` may be without user_id.
        2. `contact` not contain @name at all, so not convertable to complete SharedUser.
    """
    if message.users_shared:  # Note: May be select multiple
        return message.users_shared.users[0]
    elif username_resolver and message.text and message.text.strip().startswith('@'):
        if isinstance(username_resolver, UsernameToChatAPI):
            chat = default_resolver(wrapper=username_resolver, username=message.text, )
        else:
            chat: Chat | None = await username_resolver(username=message.text, )
        if chat:
            return SharedUser(
                user_id=chat.id,
                username=chat.username,
                first_name=chat.first_name,
                last_name=chat.last_name,
            )
        return None
    elif hasattr(message.contact, 'user_id', ):
        user_id = message.contact.user_id
    elif message.text:
        user_id = get_nums_from_text(text=message.text, )
    else:
        return None  # pragma: no cover

    if not user_id:
        return None  # pragma: no cover
    try:
        chat_info = (await message.get_bot().get_chat(chat_id=user_id, ))
    except TelegramError:  # pragma: no cover
        return None
    return SharedUser(
        user_id=chat_info.id,
        username=chat_info.username,
        first_name=chat_info.first_name,
        last_name=chat_info.last_name,
    )
