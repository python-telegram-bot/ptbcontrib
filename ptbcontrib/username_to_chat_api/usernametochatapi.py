#!/usr/bin/env python
#
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
"""
This module contains a class that, once initiated, works as a shortcut to the UsernameToChatAPI
and puts the response in a Chat object, as well as puts the error to the fitting TelegramErrors.
"""
from http import HTTPStatus

from httpx import AsyncClient
from telegram import Bot, Chat, error


class UsernameToChatAPI:
    """
    Args:
        api_url (:obj:`str`): URL to the API instance.
        api_key (:obj:`str`): Key for the API.
        bot (:class:`telegram.Bot`): Bot instance, used to create the Chat object.
        initialized_httpx_client (:class:`httpx.AsyncClient`, optional):
         Initialized httpx AsyncClient. Will be created otherwise
    """

    def __init__(
        self, api_url: str, api_key: str, bot: Bot, httpx_client: AsyncClient = None
    ) -> None:
        if api_url.endswith("/"):
            api_url = api_url[:-1]
        self._url = api_url + "/resolveUsername"
        self._api_key = api_key
        self._bot = bot
        if httpx_client:
            self._client = httpx_client
        else:
            self._client = AsyncClient()

    async def resolve(self, username: str) -> Chat:
        """
        Returns the Chat object for a username.

        Args:
            username (:obj:`str`): The username to get the :obj:`telegram.Chat` for. Passing
            a leading @ is not required, but it will work nonetheless.
        """
        response = await self._client.get(
            self._url, params={"api_key": self._api_key, "username": username}
        )
        result = response.json()
        status_code = response.status_code
        if status_code == HTTPStatus.OK:
            return Chat.de_json(result["result"], self._bot)
        message = result["description"]
        if status_code == HTTPStatus.UNAUTHORIZED:
            raise error.Forbidden(message)
        if status_code == HTTPStatus.BAD_REQUEST:
            raise error.BadRequest(message)
        if status_code == HTTPStatus.TOO_MANY_REQUESTS:
            raise error.RetryAfter(result["retry_after"])
        # this can not happen with the API right now, but we don't want to swallow future
        # errors
        raise error.TelegramError(result["description"])

    async def shutdown(self) -> None:
        """
        This closes the underlying :class:`httpx.AsyncClient`.

        """
        await self._client.aclose()
