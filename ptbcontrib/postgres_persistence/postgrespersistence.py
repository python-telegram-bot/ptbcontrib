#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020
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
"""This module contains PostgresqlPersistence class"""


import copy

from logging import getLogger
from typing import Any, DefaultDict, Dict, Optional, Tuple, Callable
from collections import defaultdict
from collections.abc import Iterable

from telegram.ext import BasePersistence
from telegram.utils.types import ConversationDict
from telegram.utils.helpers import (
    encode_conversations_to_json,
    decode_conversations_from_json,
)

from sqlalchemy.orm import scoped_session
from sqlalchemy.sql import text

import ujson as json


class PostgresPersistence(BasePersistence):
    """Using Postgresql database to make user/chat/bot data persistent across reboots.

    Attributes:
        store_user_data (:obj:`bool`): Whether user_data should be saved by this
            persistence class.
        store_chat_data (:obj:`bool`): Whether chat_data should be saved by this
            persistence class.
        store_bot_data (:obj:`bool`): Whether bot_data should be saved by this
            persistence class.

    Args:
        session (:obj:`scoped_session`, Required): sqlalchemy scoped session.
        store_user_data (:obj:`bool`, optional): Whether user_data should be saved by this
            persistence class. Default is :obj:`True`.
        store_chat_data (:obj:`bool`, optional): Whether user_data should be saved by this
            persistence class. Default is :obj:`True`.
        store_bot_data (:obj:`bool`, optional): Whether bot_data should be saved by this
            persistence class. Default is :obj:`True` .

    """

    def __init__(
        self,
        session: scoped_session,
        store_user_data: bool = True,
        store_chat_data: bool = True,
        store_bot_data: bool = True,
    ) -> None:

        super().__init__(
            store_user_data=store_user_data,
            store_chat_data=store_chat_data,
            store_bot_data=store_bot_data,
        )

        self.logger = getLogger(__name__)
        if not isinstance(session, scoped_session):
            raise TypeError("session must be `sqlalchemy.orm.scoped_session` object")

        self._session = session
        self._user_data = None
        self._chat_data = None
        self._bot_data = None
        self._conversations = None
        self.__init_database()
        self.__load_database()

    def __init_database(self) -> None:
        """creates table for persistence data if not exists"""

        create_table_qry = """
            CREATE TABLE IF NOT EXISTS persistence(
            data json NOT NULL);"""
        self._session.execute(text(create_table_qry))
        self._session.commit()

    def __load_database(self) -> None:
        try:
            data_ = self._session.execute(text("SELECT data FROM persistence")).first()
            data = data_[0] if data_ is not None else {}

            self.logger.info("Loading database \n%s", data)
            self._chat_data = defaultdict(dict, self._key_mapper(data.get("chat_data", {}), int))
            self._user_data = defaultdict(dict, self._key_mapper(data.get("user_data", {}), int))
            self._bot_data = data.get("bot_data", {})
            self._conversations = decode_conversations_from_json(data.get("conversations", "{}"))
            self.logger.info("Database loaded successfully!")
        finally:
            self._session.close()

    @property
    def user_data(self) -> Optional[DefaultDict[int, Dict]]:
        """:obj:`dict`: The user_data as a dict."""
        return self._user_data

    @property
    def chat_data(self) -> Optional[DefaultDict[int, Dict]]:
        """:obj:`dict`: The chat_data as a dict."""
        return self._chat_data

    @property
    def bot_data(self) -> Optional[Dict]:
        """:obj:`dict`: The bot_data as a dict."""
        return self._bot_data

    @property
    def conversations(self) -> Optional[Dict[str, Dict[Tuple, Any]]]:
        """:obj:`dict`: The conversations as a dict."""
        return self._conversations

    @staticmethod
    def _key_mapper(iterable: Iterable, func: Callable) -> Dict:
        return {func(k): v for k, v in iterable.items()}

    def get_user_data(self) -> DefaultDict[int, Dict[Any, Any]]:
        """Returns the user_data created from the ``user_data_json`` or an empty
        :obj:`defaultdict`.
        Returns:
            :obj:`defaultdict`: The restored user data.
        """

        return copy.deepcopy(self._user_data)

    def get_chat_data(self) -> DefaultDict[int, Dict[Any, Any]]:
        """Returns the chat_data created from the ``chat_data_json`` or an empty
        :obj:`defaultdict`.
        Returns:
            :obj:`defaultdict`: The restored chat data.
        """

        return copy.deepcopy(self._chat_data)

    def get_bot_data(self) -> Dict[Any, Any]:
        """Returns the bot_data created from the ``bot_data_json`` or an empty :obj:`dict`.
        Returns:
            :obj:`dict`: The restored bot data.
        """

        return copy.deepcopy(self._bot_data)

    def get_conversations(self, name: str) -> ConversationDict:
        """Returns the conversations created from the ``conversations_json`` or an empty
        :obj:`dict`.
        Returns:
            :obj:`dict`: The restored conversations data.
        """

        conversation = self._conversations.get(name, {})
        return copy.deepcopy(conversation)

    def update_user_data(self, user_id: int, data: Dict) -> None:
        """Will be called by the :class:`telegram.ext.Dispatcher` after a handler has
        handled an update.
        Args:
            user_id (:obj:`int`): The user the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.dispatcher.user_data`[user_id].
        """

        if self._user_data.get(user_id) == data:
            return
        self._user_data[user_id] = data

    def update_chat_data(self, chat_id: int, data: Dict) -> None:
        """Will be called by the :class:`telegram.ext.Dispatcher` after a handler has
        handled an update.
        Args:
            chat_id (:obj:`int`): The chat the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.dispatcher.chat_data`[user_id].
        """

        if self._chat_data.get(chat_id) == data:
            return
        self._chat_data[chat_id] = data

    def update_bot_data(self, data: Dict) -> None:
        """Will update the bot_data (if changed).
        Args:
            data (:obj:`dict`): The :attr:`telegram.ext.dispatcher.bot_data`.
        """

        if self._bot_data == data:
            return
        self._bot_data = data.copy()

    def update_conversation(
        self, name: str, key: Tuple[int, ...], new_state: Optional[object]
    ) -> None:
        """Will update the conversations for the given handler.
        Args:
            name (:obj:`str`): The handler's name.
            key (:obj:`tuple`): The key the state is changed for.
            new_state (:obj:`tuple` | :obj:`any`): The new state for the given key.
        """

        # map ints to strings to allow json dump
        if self._conversations.setdefault(name, {}).get(key) == new_state:
            return
        self._conversations[name][key] = new_state

    def _dump_into_json(self) -> Dict[str, Any]:
        """Dumps data into json format for inserting in db."""

        to_dump = {
            "chat_data": self._chat_data,
            "user_data": self._user_data,
            "bot_data": self.bot_data,
            "conversations": encode_conversations_to_json(self._conversations),
        }
        self.logger.info("Dumping %s", to_dump)
        return json.dumps(to_dump)

    def flush(self) -> None:
        """Will be called by :class:`telegram.ext.Updater` upon receiving a stop signal. Gives the
        persistence a chance to finish up saving or close a database connection gracefully. If this
        is not of any importance just pass will be sufficient.
        """

        self.logger.info("Saving user/chat/bot data before shutdown")
        try:
            self._session.execute("DELETE FROM persistence")
            insert_qry = "INSERT INTO persistence (data) VALUES (:jsondata)"
            params = {"jsondata": self._dump_into_json()}
            self._session.execute(text(insert_qry), params)
            self._session.commit()
        except Exception as excp:  # pylint: disable=W0703
            self._session.close()
            self.logger.error(
                "Failed to save user/chat/bot data before shutdown... " "Logging exception:",
                exc_info=excp,
            )
        else:
            self.logger.info("SUCESS! saved user/chat/bot data into database.")

        self.logger.info("Closing database...")
