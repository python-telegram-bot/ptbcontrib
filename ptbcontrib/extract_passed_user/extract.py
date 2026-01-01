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

"""This module attempts to extract side user passed actual user from incoming message"""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Callable

from telegram import SharedUser
from telegram.error import TelegramError

from ..username_to_chat_api import UsernameToChatAPI

if TYPE_CHECKING:
    from telegram import Chat, Message


def get_num_from_text(
    text: str,
) -> int | None:
    """Extract first number from text"""
    if matched_number := re.search(r"\d+", text):
        return int(matched_number.group())
    return None


def _default_resolver(
    wrapper: UsernameToChatAPI,
    username: str,
) -> Chat | None:
    """
    Try to resolve username to Chat object.
    Catch exceptions from username_to_chat_api ?
    """
    return asyncio.run(
        wrapper.resolve(
            username=username.strip(),
        )
    )


async def extract_passed_user(
    message: Message,
    username_resolver: Callable | UsernameToChatAPI | None = None,
) -> SharedUser | None:
    """
    4 cases:
    1. message.users_shared
    2. message.contact.user_id
    3. message.text starts with '@' and resolved by wrapper
    4. message.text has only numbers, resolved by get_num_from_text

    About contact entity:
        1. `contact` may be without user_id.
        2. `contact` not contain @name at all, so not convertable to complete SharedUser.
    """
    chat = user_id = None
    if message.users_shared:  # Note: May be select multiple
        return message.users_shared.users[0]
    if username_resolver and message.text and (username := re.search(r"@\S+", message.text)):
        if isinstance(username_resolver, UsernameToChatAPI):
            chat = _default_resolver(
                wrapper=username_resolver,
                username=username.group(),
            )
        else:
            chat: Chat | None = await username_resolver(  # type: ignore[no-redef]
                username=message.text,
            )
    elif message.contact and message.contact.user_id:
        user_id = message.contact.user_id
    elif message.text:
        user_id = get_num_from_text(
            text=message.text,
        )

    if user_id:
        try:
            chat = await message.get_bot().get_chat(
                chat_id=user_id,
            )
        except TelegramError:  # pragma: no cover
            return None
    if chat:
        return SharedUser(
            user_id=chat.id,
            username=chat.username,
            first_name=chat.first_name,
            last_name=chat.last_name,
        )
    return None
