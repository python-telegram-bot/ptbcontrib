#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2023
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


import json
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text
from telegram.ext import DictPersistence

CDCData = Tuple[List[Tuple[str, float, Dict[str, Any]]], Dict[str, str]]


class PostgresPersistence(DictPersistence):
    """Using Postgresql database to make user/chat/bot data persistent across reboots.

    Args:
        url (:obj:`str`, Optional) the postgresql database url.
        session (:obj:`scoped_session`, Optional): sqlalchemy scoped session.
        on_flush (:obj:`bool`, optional): if set to :obj:`True` :class:`PostgresPersistence`
            will only update bot/chat/user data when :meth:flush is called.
        **kwargs (:obj:`dict`): Arbitrary keyword Arguments to be passed to
            the DictPersistence constructor.

    Attributes:
        store_data (:class:`PersistenceInput`): Specifies which kinds of data will be saved by this
            persistence instance.
    """

    def __init__(
        self,
        url: str = None,
        session: scoped_session = None,
        on_flush: bool = False,
        **kwargs: Any,
    ) -> None:
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
            raise TypeError("You must need to provide either url or session.")

        self.logger = getLogger(__name__)

        self.on_flush = on_flush
        self.__init_database()
        try:
            self.logger.info("Loading database....")
            data_ = self._session.execute(text("SELECT data FROM persistence")).first()
            data = data_[0] if data_ is not None else {}

            chat_data_json = data.get("chat_data", "")
            user_data_json = data.get("user_data", "")
            bot_data_json = data.get("bot_data", "")
            conversations_json = data.get("conversations", "{}")
            callback_data_json = data.get("callback_data_json", "")

            self.logger.info("Database loaded successfully!")

            # if it is a fresh setup we'll add some placeholder data so we
            # can perform `UPDATE` operations on it, cause SQL only allows
            # `UPDATE` operations if column have some data already present inside it.
            if not data:
                insert_qry = "INSERT INTO persistence (data) VALUES (:jsondata)"
                self._session.execute(text(insert_qry), {"jsondata": "{}"})
                self._session.commit()

            super().__init__(
                **kwargs,
                chat_data_json=chat_data_json,
                user_data_json=user_data_json,
                bot_data_json=bot_data_json,
                callback_data_json=callback_data_json,
                conversations_json=conversations_json,
            )
        finally:
            self._session.close()

    def __init_database(self) -> None:
        """
        creates table for storing the data if table
        doesn't exist already inside database.
        """
        create_table_qry = """
            CREATE TABLE IF NOT EXISTS persistence(
            data json NOT NULL);"""
        self._session.execute(text(create_table_qry))
        self._session.commit()

    def _dump_into_json(self) -> Any:
        """Dumps data into json format for inserting in db."""

        to_dump = {
            "chat_data": self.chat_data_json,
            "user_data": self.user_data_json,
            "bot_data": self.bot_data_json,
            "conversations": self.conversations_json,
            "callback_data": self.callback_data_json,
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

    async def update_conversation(
        self, name: str, key: Tuple[int, ...], new_state: Optional[object]
    ) -> None:
        """Will update the conversations for the given handler.

        Args:
            name (:obj:`str`): The handler's name.
            key (:obj:`tuple`): The key the state is changed for.
            new_state (:obj:`tuple` | :obj:`any`): The new state for the given key.
        """
        await super().update_conversation(name, key, new_state)
        if not self.on_flush:
            await self.flush()

    async def update_user_data(self, user_id: int, data: Dict) -> None:
        """Will update the user_data (if changed).
        Args:
            user_id (:obj:`int`): The user the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.user_data` ``[user_id]``.
        """
        await super().update_user_data(user_id, data)
        if not self.on_flush:
            await self.flush()

    async def update_chat_data(self, chat_id: int, data: Dict) -> None:
        """Will update the chat_data (if changed).
        Args:
            chat_id (:obj:`int`): The chat the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.chat_data` ``[chat_id]``.
        """
        await super().update_chat_data(chat_id, data)
        if not self.on_flush:
            await self.flush()

    async def update_bot_data(self, data: Dict) -> None:
        """Will update the bot_data (if changed).
        Args:
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.bot_data`.
        """
        await super().update_bot_data(data)
        if not self.on_flush:
            await self.flush()

    async def update_callback_data(self, data: CDCData) -> None:
        """Will update the callback_data (if changed).

        Args:
            data (Tuple[List[Tuple[:obj:`str`, :obj:`float`, Dict[:obj:`str`, :class:`object`]]], \
                Dict[:obj:`str`, :obj:`str`]]): The relevant data to restore
                :class:`telegram.ext.CallbackDataCache`.
        """
        await super().update_callback_data(data)
        if not self.on_flush:
            await self.flush()

    async def flush(self) -> None:
        """Will be called by :class:`telegram.ext.Updater` upon receiving a stop signal. Gives the
        persistence a chance to finish up saving or close a database connection gracefully.
        """
        self._update_database()
        if not self.on_flush:
            self.logger.info("Closing database...")
