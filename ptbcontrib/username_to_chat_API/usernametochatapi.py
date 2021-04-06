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
"""
This module contains a class that, once initiated, works as a shortcut to the UsernameToChatAPI
and puts the response in a Chat object, as well as puts the error to the fitting TelegramErrors.
"""

try:
    import telegram.vendor.ptb_urllib3.urllib3 as urllib3
except ImportError:  # pragma: no cover
    import urllib3

try:
    import ujson as json
except ImportError:  # pragma: no cover
    import json

from telegram import error, Chat, Bot


class UsernameToChatAPI:
    """
    This class stores the URL and api key for a UsernameToChatAPI instance. Then, the correct
    request is being made and the Chat returned.

     Args:
         api_url (:obj:`str`): The base URL (speak: domain) to the API.
         api_key (:obj:`str`): The key, necessary to access the API.
         bot (:obj:`telegram.Bot`): An initiated bot object, to create the Chat object.
         pool_manager (:obj:`urllib3.PoolManager`, optional): Pre initialized
             :obj:`urllib3.PoolManager`.
    """

    def __init__(
        self, api_url: str, api_key: str, bot: Bot, pool_manager: urllib3.PoolManager = None
    ) -> None:
        if api_url.endswith("/"):
            api_url = api_url[:-1]
        self._url = api_url + "/resolveUsername"
        self._api_key = api_key
        self._bot = bot
        if pool_manager:
            self._http = pool_manager
        else:
            self._http = urllib3.PoolManager()

    def resolve(self, username: str) -> Chat:
        """
        Returns the Chat object for an username.
        """
        r = self._http.request(
            'GET', self._url, fields={"api_key": self._api_key, "username": username}
        )
        print(r)
        result = json.loads(r.data.decode('utf-8'))
        if result["ok"]:
            return Chat.de_json(result["result"], self._bot)
        else:
            error_code = result["error_code"]
            message = result["description"]
            if error_code == 401:
                raise error.Unauthorized(message)
            elif error_code == 400:
                raise error.BadRequest(message)
            elif error_code == 429:
                raise error.RetryAfter(result["retry_after"])
            # this can not happen with the API right now, but we don't want to swallow future
            # errors
            raise error.TelegramError(result["description"])
