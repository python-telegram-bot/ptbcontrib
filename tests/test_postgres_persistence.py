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

    def mocked_execute(self, query, params=None):  # pylint: disable=unused-argument
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
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

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
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

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
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

        PostgresPersistence(session=session)
        # Check that either SELECT or UPSERT query was executed (upsert for fresh db)
        executed_text = self.executed.text.strip()
        assert "SELECT data FROM persistence" in executed_text or (
            "INSERT INTO persistence (id, data) VALUES (:id, :jsondata)" in executed_text
            and "ON CONFLICT (id) DO UPDATE SET data = :jsondata" in executed_text
        )
        assert self.commited == 555
        assert self.ses_closed is True

    async def test_flush(self, monkeypatch):
        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", self.mocked_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

        await PostgresPersistence(session=session).flush()
        assert self.executed != ""
        assert self.commited == 555

    def test_new_schema_creation(self, monkeypatch):
        """Test that new tables are created with id column and single_row constraint"""
        executed_queries = []

        def mock_execute(query, params=None):  # pylint: disable=unused-argument
            executed_queries.append(query.text)
            return FakeExecResult()

        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", mock_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

        PostgresPersistence(session=session)

        # Check that CREATE TABLE was called with new schema
        create_table_found = any(
            "CREATE TABLE IF NOT EXISTS persistence" in query for query in executed_queries
        )
        assert create_table_found

        # Check that the schema includes id column and constraint
        create_table_query = next(
            q for q in executed_queries if "CREATE TABLE IF NOT EXISTS persistence" in q
        )
        assert "id INT PRIMARY KEY DEFAULT 1" in create_table_query
        assert "CONSTRAINT single_row CHECK (id = 1)" in create_table_query

    def test_schema_migration_detection(self, monkeypatch):
        """Test that valid schema with PRIMARY KEY and id=1 row is detected correctly"""
        executed_queries = []

        class FakeExecResultValidPK:
            """Simulates that id column exists as PRIMARY KEY"""

            def first(self):
                return (1,)  # Primary key validation passes

        class FakeExecResultValidData:
            """Simulates that row with id=1 exists"""

            def first(self):
                return (1,)

        def mock_execute(query, params=None):
            executed_queries.append(query.text)

            # Match the full primary key validation query
            if all(
                x in query.text
                for x in [
                    "information_schema.columns",
                    "key_column_usage",
                    "table_constraints",
                    "PRIMARY KEY",
                    "column_name = 'id'",
                ]
            ):
                return FakeExecResultValidPK()

            # Check for data validation query (id=1 exists)
            if "WHERE id = :id" in query.text and "information_schema" not in query.text:
                return FakeExecResultValidData()

            return FakeExecResult()

        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", mock_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

        PostgresPersistence(session=session)

        # Verify no migration commands were run
        migration_commands = [
            "ALTER TABLE persistence ADD COLUMN id INT",
            "UPDATE persistence SET id = :id",
            "DELETE FROM persistence WHERE id IS NULL",
        ]
        for migration_cmd in migration_commands:
            assert not any(migration_cmd in query for query in executed_queries)

        # Verify the PK validation query was actually executed
        pk_validation_executed = any(
            all(x in query for x in ["key_column_usage", "table_constraints", "PRIMARY KEY"])
            for query in executed_queries
        )
        assert pk_validation_executed

    def test_migration_when_id_not_primary_key(self, monkeypatch):
        """Test that migration runs when id column exists but is not a PRIMARY KEY"""
        executed_queries = []

        class FakeExecResultNoPK:
            """Simulates id column exists but is NOT a primary key"""

            def first(self):
                return None

        def mock_execute(query, params=None):
            executed_queries.append(query.text)

            # Simulate failure of primary key validation
            if all(
                x in query.text
                for x in [
                    "information_schema.columns",
                    "key_column_usage",
                    "table_constraints",
                    "PRIMARY KEY",
                ]
            ):
                return FakeExecResultNoPK()

            return FakeExecResult()

        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", mock_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

        PostgresPersistence(session=session)

        # Verify migration was triggered even though id column might exist
        migration_triggered = any(
            "ALTER TABLE persistence ADD PRIMARY KEY (id)" in query for query in executed_queries
        )
        assert migration_triggered

    def test_full_migration_from_old_schema(self, monkeypatch):
        """Test that migration is executed when old schema is detected"""
        executed_queries = []

        class FakeExecResultNoColumn:
            """Simulates that id column doesn't exist (migration needed)"""

            def first(self):
                return None  # Column doesn't exist

        def mock_execute(query, params=None):  # pylint: disable=unused-argument
            executed_queries.append(query.text)
            # Check if this is the column check query
            if "information_schema.columns" in query.text and "column_name = 'id'" in query.text:
                return FakeExecResultNoColumn()
            return FakeExecResult()

        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", mock_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

        PostgresPersistence(session=session)

        # Verify migration commands were run in correct order
        expected_migration_steps = [
            "ALTER TABLE persistence ADD COLUMN id INT",
            "UPDATE persistence SET id = :id",
            "DELETE FROM persistence WHERE id IS NULL",
            "ALTER TABLE persistence ALTER COLUMN id SET NOT NULL",
            "ALTER TABLE persistence ADD PRIMARY KEY (id)",
            "ALTER TABLE persistence ADD CONSTRAINT single_row CHECK (id = :id)",
        ]

        for expected_step in expected_migration_steps:
            assert any(
                expected_step in query for query in executed_queries
            ), f"Expected migration step not found: {expected_step}"

    def test_migration_preserves_data(self, monkeypatch):
        """Test that existing data survives migration"""
        executed_queries = []
        test_data = {"user_data": '{"1": {"test": "value"}}'}

        class FakeExecResultNoColumn:
            def first(self):
                return None

        class FakeExecResultWithData:
            def first(self):
                return (test_data,)

        def mock_execute(query, params=None):
            executed_queries.append(query.text)
            # Simulate failure of primary key validation
            if "information_schema" in query.text and "PRIMARY KEY" in query.text:
                return FakeExecResultNoColumn()
            # Simulate data exists
            if "SELECT data FROM persistence" in query.text:
                return FakeExecResultWithData()
            return FakeExecResult()

        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", mock_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

        persistence = PostgresPersistence(session=session)

        # Verify data was loaded
        assert persistence is not None

    def test_upsert_query_on_fresh_database(self, monkeypatch):
        """Test that upsert query is used when initializing fresh database"""
        executed_queries = []

        def mock_execute(query, params=None):  # pylint: disable=unused-argument
            executed_queries.append(query.text)
            return FakeExecResult()

        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", mock_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

        PostgresPersistence(session=session)

        # Check that upsert query was used for initialization
        upsert_found = any(
            "INSERT INTO persistence (id, data) VALUES (:id, :jsondata)" in query
            and "ON CONFLICT (id) DO UPDATE SET data = :jsondata" in query
            for query in executed_queries
        )
        assert upsert_found

    def test_upsert_query_on_update(self, monkeypatch):
        """Test that upsert query is used when updating database"""
        executed_queries = []
        executed_params = []

        def mock_execute(query, params=None):
            executed_queries.append(query.text)
            if params:
                executed_params.append(params)
            return FakeExecResult()

        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", mock_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "remove", self.mock_ses_close)
        monkeypatch.setattr(session, "rollback", lambda: None)

        persistence = PostgresPersistence(session=session)

        # Clear previous queries
        executed_queries.clear()
        executed_params.clear()

        # Trigger update  # pylint: disable=protected-access
        persistence._update_database()

        # Verify upsert query was used
        upsert_found = any(
            "INSERT INTO persistence (id, data) VALUES (:id, :jsondata)" in query
            and "ON CONFLICT (id) DO UPDATE SET data = :jsondata" in query
            for query in executed_queries
        )
        assert upsert_found

        # Verify parameters were passed
        assert len(executed_params) > 0
        assert "jsondata" in executed_params[0]
        assert "id" in executed_params[0]

    def test_single_row_constraint_in_schema(self, monkeypatch):
        """Test that single_row constraint is present in schema"""
        executed_queries = []

        def mock_execute(query, params=None):  # pylint: disable=unused-argument
            executed_queries.append(query.text)
            return FakeExecResult()

        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", mock_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

        PostgresPersistence(session=session)

        # Find the CREATE TABLE query
        create_table_query = next(
            (q for q in executed_queries if "CREATE TABLE IF NOT EXISTS persistence" in q), None
        )

        assert create_table_query is not None
        assert "CONSTRAINT single_row CHECK (id = 1)" in create_table_query

    def test_migration_preserves_single_row(self, monkeypatch):
        """Test that migration deletes extra rows and keeps only one"""
        executed_queries = []

        class FakeExecResultNoColumn:
            def first(self):
                return None

        def mock_execute(query, params=None):  # pylint: disable=unused-argument
            executed_queries.append(query.text)
            if "information_schema.columns" in query.text and "column_name = 'id'" in query.text:
                return FakeExecResultNoColumn()
            return FakeExecResult()

        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", mock_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

        PostgresPersistence(session=session)

        # Verify that migration includes step to update first row to id=1
        update_first_row = any(
            "UPDATE persistence SET id = :id" in query and "LIMIT 1" in query
            for query in executed_queries
        )
        assert update_first_row

        # Verify that migration deletes rows without id
        delete_extra_rows = any(
            "DELETE FROM persistence WHERE id IS NULL" in query for query in executed_queries
        )
        assert delete_extra_rows

    async def test_data_persistence_with_upsert(self, bot, update, monkeypatch):
        """Test that data is correctly persisted using upsert"""
        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", self.mocked_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

        app = (
            Application.builder()
            .bot(DictExtBot(bot.token))
            .persistence(PostgresPersistence(session=session))
            .build()
        )

        async def handler(upd, context):  # pylint: disable=unused-argument
            context.user_data["key"] = "value"
            context.chat_data["chat_key"] = "chat_value"
            context.bot_data["bot_key"] = "bot_value"

        h = MessageHandler(None, handler)
        app.add_handler(h)

        async with app:
            await app.process_update(update)

        # Verify that update was executed
        assert self.executed != ""
        assert self.commited == 555

    def test_migration_error_handling(self, monkeypatch):
        """Test that migration errors are handled gracefully"""

        class FakeExecResultNoColumn:
            def first(self):
                return None

        def mock_execute_with_error(query, params=None):  # pylint: disable=unused-argument
            if "information_schema.columns" in query.text:
                return FakeExecResultNoColumn()
            # Simulate error during migration
            if "ALTER TABLE" in query.text:
                raise RuntimeError("Migration failed")
            return FakeExecResult()

        rollback_called = False

        def mock_rollback():
            nonlocal rollback_called
            rollback_called = True

        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", mock_execute_with_error)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "remove", self.mock_ses_close)
        monkeypatch.setattr(session, "rollback", mock_rollback)

        # Should not raise exception, but handle it gracefully
        PostgresPersistence(session=session)

        # Verify rollback was called
        assert rollback_called

    def test_migration_uses_ctid(self, monkeypatch):
        """Test that migration correctly uses ctid for selecting first row"""
        executed_queries = []

        class FakeExecResultNoColumn:
            def first(self):
                return None

        def mock_execute(query, params=None):
            executed_queries.append(query.text)
            if "information_schema" in query.text and "PRIMARY KEY" in query.text:
                return FakeExecResultNoColumn()
            return FakeExecResult()

        session = scoped_session("a")
        monkeypatch.setattr(session, "execute", mock_execute)
        monkeypatch.setattr(session, "commit", self.mock_commit)
        monkeypatch.setattr(session, "remove", self.mock_ses_close)

        PostgresPersistence(session=session)

        # Verify ctid is used in UPDATE during migration
        ctid_query = any("ctid" in query for query in executed_queries)
        assert ctid_query
