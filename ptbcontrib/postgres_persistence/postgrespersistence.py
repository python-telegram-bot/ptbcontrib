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
"""This module contains PostgresqlPersistence class"""


from logging import getLogger
from collections import defaultdict
from typing import Dict, Tuple, Any, Callable, Optional

from telegram.ext import DictPersistence
from telegram.utils.helpers import (
    encode_conversations_to_json,
    decode_conversations_from_json,
)

from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker, scoped_session

try:
    import ujson as json
except ImportError:
    import json  # type: ignore[no-redef]


class PostgresPersistence(DictPersistence):
    """Using Postgresql database to make user/chat/bot data persistent across reboots.

    Attributes:
        store_user_data (:obj:`bool`): Whether user_data should be saved by this
            persistence class.
        store_chat_data (:obj:`bool`): Whether chat_data should be saved by this
            persistence class.
        store_bot_data (:obj:`bool`): Whether bot_data should be saved by this
            persistence class.

    Args:
        url (:obj:`str`, Optional) the postgresql database url.
        session (:obj:`scoped_session`, Optional): sqlalchemy scoped session.
        on_flush (:obj:`bool`, optional): if set to :obj:`True` :class:`PostgresPersistence`
            will only update bot/chat/user data in database on shutdown.
        store_user_data (:obj:`bool`, optional): Whether user_data should be saved by this
            persistence class. Default is :obj:`True`.
        store_chat_data (:obj:`bool`, optional): Whether user_data should be saved by this
            persistence class. Default is :obj:`True`.
        store_bot_data (:obj:`bool`, optional): Whether bot_data should be saved by this
            persistence class. Default is :obj:`True` .

    """

    # pylint: disable=R0913
    def __init__(
        self,
        url: str = None,
        session: scoped_session = None,
        on_flush: bool = False,
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

        if url:
            if not url.startswith("postgresql://"):
                raise TypeError(f"{url} isn't a valid PostgreSQL database URL.")
            engine = create_engine(url, client_encoding="utf8")
            self._session = scoped_session(sessionmaker(bind=engine, autoflush=False))

        elif session:
            if not isinstance(session, scoped_session):
                raise TypeError("session must needs to be `sqlalchemy.orm.scoped_session` object")
            self._session = session

        else:
            raise TypeError("You must needs to provide either url or session.")

        self.on_flush = on_flush
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

            self.logger.info("Loading database....")
            self._chat_data = defaultdict(dict, self._key_mapper(data.get("chat_data", {}), int))
            self._user_data = defaultdict(dict, self._key_mapper(data.get("user_data", {}), int))
            self._bot_data = data.get("bot_data", {})
            self._conversations = decode_conversations_from_json(data.get("conversations", "{}"))
            self.logger.info("Database loaded successfully!")
        finally:
            self._session.close()

    @staticmethod
    def _key_mapper(iterable: Dict, func: Callable) -> Dict:
        return {func(k): v for k, v in iterable.items()}

    def _dump_into_json(self) -> Any:
        """Dumps data into json format for inserting in db."""

        to_dump = {
            "chat_data": self._chat_data,
            "user_data": self._user_data,
            "bot_data": self.bot_data,
            "conversations": encode_conversations_to_json(self._conversations),
        }
        self.logger.debug("Dumping %s", to_dump)
        return json.dumps(to_dump)

    def _update_database(self) -> None:
        self.logger.debug("Updating database...")
        try:
            insert_qry = "UPDATE persistence SET data = :jsondata"
            params = {"jsondata": self._dump_into_json()}
            self._session.execute(text(insert_qry), params)
            self._session.commit()
        except Exception as excp:  # pylint: disable=W0703
            self._session.close()
            self.logger.error(
                "Failed to save data in the database.\nLogging exception: ",
                exc_info=excp,
            )

    def update_conversation(
        self, name: str, key: Tuple[int, ...], new_state: Optional[object]
    ) -> None:
        """Will update the conversations for the given handler.
        Args:
            name (:obj:`str`): The handler's name.
            key (:obj:`tuple`): The key the state is changed for.
            new_state (:obj:`tuple`
        """
        super().update_conversation(name, key, new_state)
        if not self.on_flush:
            self._update_database()

    def update_user_data(self, user_id: int, data: Dict) -> None:
        """Will update the user_data (if changed).
        Args:
            user_id (:obj:`int`): The user the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.user_data` ``[user_id]``.
        """
        super().update_user_data(user_id, data)
        if not self.on_flush:
            self._update_database()

    def update_chat_data(self, chat_id: int, data: Dict) -> None:
        """Will update the chat_data (if changed).
        Args:
            chat_id (:obj:`int`): The chat the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.chat_data` ``[chat_id]``.
        """
        super().update_chat_data(chat_id, data)
        if not self.on_flush:
            self._update_database()

    def update_bot_data(self, data: Dict) -> None:
        """Will update the bot_data (if changed).
        Args:
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.bot_data`.
        """
        super().update_bot_data(data)
        if not self.on_flush:
            self._update_database()

    def flush(self) -> None:
        """Will be called by :class:`telegram.ext.Updater` upon receiving a stop signal. Gives the
        persistence a chance to finish up saving or close a database connection gracefully.
        """
        self._update_database()
        self.logger.info("Closing database...")
