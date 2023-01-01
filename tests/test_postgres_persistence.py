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
import pytest
from sqlalchemy.orm import scoped_session  # noqa: E402
from telegram import Chat, Message, Update, User
from telegram.ext import Application, MessageHandler

from ptbcontrib.postgres_persistence import PostgresPersistence  # noqa: E402
from tests.conftest import DictExtBot


@pytest.fixture(scope="function")
def update():
    return Update(
        1, message=Message(1, None, Chat(1, ""), from_user=User(1, "", False), text="Text")
    )


# as __load_database() method calls .first()
# over session.execute() results.
class FakeExecResult:
    def first(self):
        return None


class TestPostgresPersistence:

    executed = ""
    commited = 0
    ses_closed = False
    flush_flag = False

    @pytest.fixture(autouse=True, name="reset")
    def reset_fixture(self):
        self.reset()

    def reset(self):
        self.executed = ""
        self.commited = 0
        self.ses_closed = False
        self.flush_flag = False

    def mocked_execute(self, query, *args, **kwargs):
        self.executed = query
        return FakeExecResult()

    def mock_commit(self):
        self.commited = 555

    def mock_ses_close(self):
        self.ses_closed = True

    def test_no_args(self):
        with pytest.raises(TypeError, match="provide either url or session."):
            PostgresPersistence()

    def test_invalid_scoped_session_obj(self):
        with pytest.raises(TypeError, match="must needs to be `sqlalchemy.orm.scoped"):
            PostgresPersistence(session="scoop")

    def test_invalid_uri(self):
        with pytest.raises(TypeError, match="isn't a valid PostgreSQL"):
            PostgresPersistence(url="sqlite:///owo.db")

    async def test_with_handler(self, bot, update, monkeypatch):
        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", self.mocked_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "close", self.mock_ses_close)

        app = (
            Application.builder()
            .bot(DictExtBot(bot.token))
            .persistence(PostgresPersistence(session=session))
            .build()
        )

        async def first(update, context):
            if not context.user_data == {}:
                pytest.fail()
            if not context.chat_data == {}:
                pytest.fail()
            if not context.bot_data == {}:
                pytest.fail()
            context.user_data["test1"] = "test2"
            context.chat_data[3] = "test4"
            context.bot_data["test1"] = "test2"

        async def second(update, context):
            if not context.user_data["test1"] == "test2":
                pytest.fail()
            if not context.chat_data[3] == "test4":
                pytest.fail()
            if not context.bot_data["test1"] == "test2":
                pytest.fail()

        h1 = MessageHandler(None, first)
        h2 = MessageHandler(None, second)
        app.add_handler(h1)

        async with app:
            await app.process_update(update)
            app.remove_handler(h1)
            app.add_handler(h2)
            await app.process_update(update)

        assert self.executed != ""
        assert self.commited == 555
        assert self.ses_closed is True

    @pytest.mark.parametrize(["on_flush", "expected"], [(False, True)])
    async def test_on_flush(self, bot, update, monkeypatch, on_flush, expected):
        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", self.mocked_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "close", self.mock_ses_close)

        persistence = PostgresPersistence(session=session, on_flush=on_flush)

        def mocked_update_database():
            self.flush_flag = True

        monkeypatch.setattr(persistence, "_update_database", mocked_update_database)
        app = Application.builder().bot(DictExtBot(bot.token)).persistence(persistence).build()

        async def first(update, context):
            context.user_data["test1"] = "test2"
            context.chat_data[3] = "test4"
            context.bot_data["test1"] = "test2"

        async def second(update, context):
            if not context.user_data["test1"] == "test2":
                pytest.fail()
            if not context.chat_data[3] == "test4":
                pytest.fail()
            if not context.bot_data["test1"] == "test2":
                pytest.fail()

        h1 = MessageHandler(None, first)
        h2 = MessageHandler(None, second)

        async with app:
            app.add_handler(h1)
            await app.process_update(update)

            app.remove_handler(h1)
            app.add_handler(h2)
            await app.process_update(update)

            await app.update_persistence()
            assert self.flush_flag is expected

    def test_load_on_boot(self, monkeypatch):
        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", self.mocked_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "close", self.mock_ses_close)

        PostgresPersistence(session=session)
        assert self.executed.text in {
            "SELECT data FROM persistence",
            "INSERT INTO persistence (data) VALUES (:jsondata)",
        }
        assert self.commited == 555
        assert self.ses_closed is True

    async def test_flush(self, bot, update, monkeypatch):
        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", self.mocked_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "close", self.mock_ses_close)

        await PostgresPersistence(session=session).flush()
        assert self.executed != ""
        assert self.commited == 555
