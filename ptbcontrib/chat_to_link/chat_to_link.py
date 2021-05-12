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
"""This module contains a helper function to get joinable links from chats."""
from telegram import Chat
from telegram.error import BadRequest


def get_chat_link(
    chat: Chat,
) -> str:
    """
    Gets a link for the chat in the following order if the link is valid:
     1. Chat's username (`chat.username`).
     2. Chat's invite link (`chat.invite_link`).
     3. Chat's invite link from bot (`bot.get_chat.invite_link`)
     4. Export primary invite link (`bot.export_chat_invite_link`).
     5. Empty string since there is no valid link and the bot doesn't have permission
        to create one either.

    This function doesn't check to see if the bot has enough permissions to create/export
    invite links. Instead, it makes the API call and relies on the response (new link or
    error message) to determine the outcome. This way we can avoid an extra API call.

    Warning:
        This function might make up to 2 API calls to get a valid chat link.

    Args:
        chat (:obj:`telegram.Chat`): The chat to get a link from.

    Returns:
        :obj:`str`: Chat link as a URL if there is any. Otherwise an empty string.
    """
    bot = chat.bot
    if chat.username:
        return f"https://t.me/{chat.username}"
    if chat.invite_link:
        return chat.invite_link

    bot_chat = bot.get_chat(chat.id)
    if bot_chat.invite_link:
        return bot_chat.invite_link

    try:
        return chat.export_invite_link()
    except BadRequest as exc:
        if exc.message == "Not enough rights to manage chat invite link":
            return ""
        raise exc
