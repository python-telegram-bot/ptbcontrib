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
import datetime as dtm
import os
import pickle
import sys
from copy import deepcopy
from typing import Optional

import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import CallbackContext, MessageHandler, PicklePersistence, filters

from ptbcontrib.roles import BOT_DATA_KEY, Role, Roles, RolesBotData, RolesHandler, setup_roles


@pytest.fixture(scope="function")
def update():
    update = Update(
        0,
        Message(
            0, dtm.datetime.utcnow(), Chat(0, "private"), from_user=User(0, "TestUser", False)
        ),
    )
    update._unfreeze()
    update.message._unfreeze()
    update.message.from_user._unfreeze()
    update.message.chat._unfreeze()
    return update


@pytest.fixture(scope="function")
def roles(bot):
    return Roles(bot)


@pytest.fixture(scope="function")
def parent_role():
    return Role(name="parent_role")


@pytest.fixture(scope="function")
def role():
    return Role(name="role")


@pytest.fixture(autouse=True)
def change_directory(tmp_path):
    orig_dir = os.getcwd()
    # Switch to a temporary directory so we don't have to worry about cleaning up files
    # (str() for py<3.6)
    os.chdir(str(tmp_path))
    yield
    # Go back to original directory
    os.chdir(orig_dir)


class TestRole:
    def test_creation(self, parent_role):
        r = Role(child_roles=[parent_role, parent_role])
        assert r.chat_ids == set()
        assert str(r) == "Role({})"
        assert r.child_roles == {parent_role}
        assert isinstance(r._admin, Role)
        assert str(r._admin) == f"Role({Role._DEFAULT_ADMIN_NAME})"

        r = Role(1)
        assert r.chat_ids == {1}
        assert str(r) == "Role({1})"

        r = Role([1, 2])
        assert r.chat_ids == {1, 2}
        assert str(r) == "Role({1, 2})"

        r = Role([1, 2], name="role")
        assert r.chat_ids == {1, 2}
        assert str(r) == "Role(role)"

    def test_add_member(self, role):
        assert role.chat_ids == set()
        role.add_member(1)
        assert role.chat_ids == {1}
        role.add_member(2)
        assert role.chat_ids == {1, 2}
        role.add_member(1)
        assert role.chat_ids == {1, 2}

    def test_kick_member(self, role):
        assert role.chat_ids == set()
        role.add_member(1)
        role.add_member(2)
        assert role.chat_ids == {1, 2}
        role.kick_member(1)
        assert role.chat_ids == {2}
        role.kick_member(1)
        assert role.chat_ids == {2}
        role.kick_member(2)
        assert role.chat_ids == set()

    def test_add_remove_child_role(self, role, parent_role):
        assert role.child_roles == set()
        parent2 = Role(chat_ids=456, name="pr2")
        role.add_child_role(parent_role)
        assert role.child_roles == {parent_role}
        role.add_child_role(parent2)
        assert role.child_roles == {parent_role, parent2}

        role.remove_child_role(parent_role)
        assert role.child_roles == {parent2}
        role.remove_child_role(parent2)
        assert role.child_roles == set()

        with pytest.raises(ValueError, match="You must not add a role as its own child!"):
            role.add_child_role(role)

        parent_role.add_child_role(role)
        with pytest.raises(ValueError, match="You must not add a parent role as a child!"):
            role.add_child_role(parent_role)

    def test_equals(self, role, parent_role):
        r = Role(name="test1")
        r2 = Role(name="test2")
        r3 = Role(name="test3", chat_ids=[1, 2])
        r4 = Role(name="test4")
        assert role.equals(parent_role)
        role.add_child_role(r)
        assert not role.equals(parent_role)
        parent_role.add_child_role(r2)
        assert role.equals(parent_role)
        parent_role.add_child_role(r3)
        role.add_child_role(r4)
        assert not role.equals(parent_role)
        role.remove_child_role(r4)
        parent_role.remove_child_role(r3)

        role.add_member(1)
        assert not role.equals(parent_role)
        parent_role.add_member(1)
        assert role.equals(parent_role)
        role.add_member(2)
        assert not role.equals(parent_role)
        parent_role.add_member(2)
        assert role.equals(parent_role)
        role.kick_member(2)
        assert not role.equals(parent_role)
        parent_role.kick_member(2)
        assert role.equals(parent_role)

        r.add_member(1)
        assert not role.equals(parent_role)
        r2.add_member(1)
        assert role.equals(parent_role)

    def test_comparison(self, role, parent_role):
        assert not role <= 1
        assert not role >= 1

        assert not role < parent_role
        assert not parent_role < role
        assert role <= role
        assert role >= role
        assert parent_role <= parent_role
        assert parent_role >= parent_role

        parent_role.add_child_role(role)
        assert role < parent_role
        assert role <= parent_role
        assert parent_role >= role
        assert parent_role > role

        parent_role.remove_child_role(role)
        assert not role < parent_role
        assert not parent_role < role

    def test_hash(self, role, parent_role):
        assert role != parent_role
        assert hash(role) != hash(parent_role)

        assert role == role
        assert hash(role) == hash(role)

        assert parent_role == parent_role
        assert hash(parent_role) == hash(parent_role)

    def test_deepcopy(self, role, parent_role):
        child = Role(name="cr", chat_ids=[1, 2, 3])
        role.add_child_role(child)
        role.add_member(7)
        copied_role = deepcopy(role)

        assert role is not copied_role
        assert role.equals(copied_role)
        assert role.chat_ids is not copied_role.chat_ids
        assert role.chat_ids == copied_role.chat_ids
        (copied_child,) = copied_role.child_roles
        assert child is not copied_child
        assert child.equals(copied_child)

    def test_filter_user(self, update, role, parent_role):
        update.message.chat = None
        assert not role.check_update(update)

        role.add_member(0)
        assert role.check_update(update)

        update.message.from_user.id = 1
        assert not role.check_update(update)

        parent_role.add_child_role(role)
        parent_role.add_member(1)
        assert role.check_update(update)

    def test_filter_chat(self, update, role, parent_role):
        update.message.from_user = None
        assert not role.check_update(update)

        role.add_member(0)
        assert role.check_update(update)

        update.message.chat.id = 1
        assert not role.check_update(update)

        parent_role.add_child_role(role)
        parent_role.add_member(1)
        assert role.check_update(update)

    def test_filter_merged_roles(self, update, role):
        role.add_member(0)
        r = Role(0)
        assert not (role & (~r)).check_update(update)

        r = Role(1)
        assert not (role & r).check_update(update)
        assert (role | r).check_update(update)

    def test_filter_allow_parent(self, update, role, parent_role):
        role.add_member(0)
        parent_role.add_member(1)
        parent_role.add_child_role(role)

        test_role = ~role
        assert not test_role.check_update(update)
        update.message.from_user.id = 1
        update.message.chat.id = 1
        assert test_role.check_update(update)

    def test_filter_exclude_children(self, update, role, parent_role):
        parent_role.add_child_role(role)
        parent_role.add_member(0)
        role.add_member(1)

        test_role = ~parent_role
        assert not test_role.check_update(update)
        update.message.from_user.id = 1
        update.message.chat.id = 1
        assert not test_role.check_update(update)
        update.message.from_user.id = 2
        update.message.chat.id = 1
        assert not test_role.check_update(update)

    def test_filter_without_user_and_chat(self, update, role):
        role.add_member(0)
        update.message = None
        assert not role.check_update(update)
        assert not (~role).check_update(update)

    def test_always_allow_admin(self, update, role):
        role._admin.add_member(0)
        try:
            assert (~Role(0)).check_update(update)
            assert (Role(0) & ~Role(0)).check_update(update)
            assert (Role(1) & ~Role(0)).check_update(update)
            assert (Role(1) & ~Role(2)).check_update(update)
            assert (Role(0) | ~Role(0)).check_update(update)
            assert (Role(1) | ~Role(0)).check_update(update)
            assert (Role(1) | ~Role(2)).check_update(update)
        finally:
            role._admin.kick_member(0)

    def test_pickle(self, role, parent_role):
        role.add_member([0, 1, 3])
        parent_role.add_member([4, 5, 6])
        child_role = Role(name="child_role", chat_ids=[7, 8, 9])
        role.add_child_role(child_role)
        parent_role.add_child_role(child_role)

        data = {
            "role": role,
            "parent": parent_role,
            "child": child_role,
        }
        with open("pickle", "wb") as file:
            pickle.dump(data, file)
        with open("pickle", "rb") as file:
            data = pickle.load(file)

        assert data["role"].equals(role)
        assert data["parent"].equals(parent_role)
        assert data["child"].equals(child_role)

        (child_1,) = data["role"].child_roles
        (child_2,) = data["parent"].child_roles
        assert child_1 is child_2

        assert data["role"] in Role._admin.child_roles
        assert data["parent"] in Role._admin.child_roles
        assert data["child"] in Role._admin.child_roles
        assert data["child"] <= data["role"]
        assert data["child"] <= data["parent"]
        assert not data["role"] <= data["parent"]


class TestRoles:
    def test_creation(self, bot):
        roles = Roles(bot)
        assert isinstance(roles.admins, Role)
        assert roles.bot is bot

    def test_set_bot(self, bot):
        roles = Roles(1)
        assert roles.bot == 1
        roles.set_bot(2)
        assert roles.bot == 2
        roles.set_bot(bot)
        assert roles.bot is bot
        with pytest.raises(ValueError, match="already set"):
            roles.set_bot(bot)

    def test_add_kick_admin(self, roles):
        assert roles.admins.chat_ids == set()
        roles.add_admin(1)
        assert roles.admins.chat_ids == {1}
        roles.add_admin(2)
        assert roles.admins.chat_ids == {1, 2}
        roles.kick_admin(1)
        assert roles.admins.chat_ids == {2}
        roles.kick_admin(2)
        assert roles.admins.chat_ids == set()

    @pytest.mark.skipif(sys.version_info < (3, 6), reason="dicts are not ordered in py<=3.5")
    def test_dict_functionality(self, roles):
        roles.add_role("role0", 0)
        roles.add_role("role1", 1)
        roles.add_role("role2", 2)

        assert "role2" in roles
        assert "role3" not in roles

        a = {name for name in roles}
        assert a == {f"role{k}" for k in range(3)}

        b = {name: role.chat_ids for name, role in roles.items()}
        assert b == {f"role{k}": {k} for k in range(3)}

        c = [name for name in roles.keys()]
        assert c == [f"role{k}" for k in range(3)]

        d = [r.chat_ids for r in roles.values()]
        assert d == [{k} for k in range(3)]

    def test_add_remove_role(self, roles, parent_role):
        roles.add_role("role", child_roles=[parent_role])
        role = roles["role"]
        assert role.chat_ids == set()
        assert role.child_roles == {parent_role}
        assert str(role) == "Role(role)"
        assert role <= roles.admins
        assert role not in Role._admin.child_roles

        with pytest.raises(ValueError, match="Role name is already taken."):
            roles.add_role("role")

        roles.remove_role("role")
        assert not roles.get("role", None)
        assert not role <= roles.admins
        assert role in Role._admin.child_roles

    def test_handler_admins(self, roles, update):
        roles.add_role("role", 0)
        roles.add_admin(1)
        assert roles["role"].check_update(update)
        update.message.from_user.id = 1
        update.message.chat.id = 1
        assert roles["role"].check_update(update)
        roles.kick_admin(1)
        assert not roles["role"].check_update(update)

    def test_handler_admins_merged(self, roles, update):
        roles.add_role("role_1", 0)
        roles.add_role("role_2", 1)
        roles.add_admin(2)
        test_role = roles["role_1"] & ~roles["role_2"]
        assert test_role.check_update(update)
        update.message.from_user.id = 2
        update.message.chat.id = 2
        assert test_role.check_update(update)
        roles.kick_admin(2)
        assert not test_role.check_update(update)

    @pytest.mark.filterwarnings("ignore:BasePersistence")
    async def test_pickle(self, roles, bot):
        persistence = PicklePersistence(filepath="pickle", on_flush=False)
        persistence.set_bot(bot)

        roles.add_role("role", [1, 2, 3])
        roles.add_role("parent", [4, 5, 6])
        roles.add_role("child", [7, 8, 9])
        roles["role"].add_child_role(roles["child"])
        roles["parent"].add_child_role(roles["child"])

        roles.admins.add_member(10)

        await persistence.update_bot_data(roles)
        persistence = PicklePersistence(filepath="pickle", on_flush=False)
        copied_roles = await persistence.get_bot_data()

        assert copied_roles["role"].equals(roles["role"])
        assert copied_roles["parent"].equals(roles["parent"])
        assert copied_roles["child"].equals(roles["child"])

        (child_1,) = roles["role"].child_roles
        (child_2,) = roles["parent"].child_roles
        assert child_1 is child_2

        assert copied_roles["role"] <= copied_roles.admins
        assert copied_roles["role"] in copied_roles.admins.child_roles
        assert copied_roles["parent"] in copied_roles.admins.child_roles
        assert copied_roles["child"] in copied_roles.admins.child_roles
        assert copied_roles["child"] <= copied_roles["role"]
        assert copied_roles["child"] <= copied_roles["parent"]
        assert not copied_roles["role"] <= copied_roles["parent"]


@pytest.fixture(scope="function", autouse=True)
def clear_bot_data(app):
    yield
    app.bot_data = dict()


class RolesData(RolesBotData):
    def __init__(self):
        self.roles = None

    def get_roles(self) -> Optional[Roles]:
        return self.roles

    def set_roles(self, roles: Roles) -> None:
        self.roles = roles


class TestRolesHandler:
    @pytest.mark.parametrize("roles_bot_data", [True, False])
    def test_setup_roles(self, app, roles_bot_data):
        if roles_bot_data:
            app.bot_data = RolesData()
        roles = setup_roles(app)
        assert isinstance(roles, Roles)
        if not roles_bot_data:
            assert app.bot_data[BOT_DATA_KEY] is roles
        else:
            assert app.bot_data.get_roles() is roles
        # We test twice to make sure everything nothing goes wrong when roles is already there
        roles = setup_roles(app)
        assert isinstance(roles, Roles)
        if not roles_bot_data:
            assert app.bot_data[BOT_DATA_KEY] is roles
        else:
            assert app.bot_data.get_roles() is roles

    def test_setup_roles_invalid_bot_data_type(self, app):
        app.bot_data = 17
        with pytest.raises(TypeError, match="dict or implement RolesBotData"):
            setup_roles(app)

    def test_collect_additional_context_invalid_bot_data(self, app, update):
        app.bot_data = "yet another deathstar"

        def callback(_, __):
            pass

        handler = MessageHandler(filters.ALL, callback=callback)
        roles_handler = RolesHandler(handler, roles=None)
        context = CallbackContext.from_update(update, app)
        with pytest.raises(TypeError, match="dict or implement RolesBotData"):
            roles_handler.collect_additional_context(context, app, update, True)

    @pytest.mark.parametrize("roles_bot_data", [True, False])
    async def test_callback_and_context(self, app, update, roles_bot_data):
        if roles_bot_data:
            app.bot_data = RolesData()
        self.roles = setup_roles(app)
        self.roles.admins.add_member(42)
        self.roles.add_role(name="role", chat_ids=[1])
        self.test_flag = False

        def callback(_, context: CallbackContext):
            self.test_flag = context.roles is self.roles

        handler = MessageHandler(filters.ALL, callback=callback)
        roles_handler = RolesHandler(handler, roles=self.roles["role"])

        assert not roles_handler.check_update(update)
        update.message.from_user.id = 1
        assert roles_handler.check_update(update)
        update.message.from_user.id = 42
        assert roles_handler.check_update(update)

        app.add_handler(roles_handler)
        async with app:
            await app.process_update(update)
        assert self.test_flag

    @pytest.mark.parametrize("roles_bot_data", [True, False])
    async def test_handler_error_message(self, app, update, roles_bot_data):
        if roles_bot_data:
            app.bot_data = RolesData()
        handler = MessageHandler(filters.ALL, callback=lambda u, c: 1)
        roles_handler = RolesHandler(handler, roles=Role(0))
        app.add_handler(roles_handler)
        self.test_flag = False

        async def error_handler(_, context: CallbackContext):
            self.test_flag = "You must set a Roles instance" in str(context.error)

        app.add_error_handler(error_handler)
        async with app:
            await app.process_update(update)

        assert self.test_flag
