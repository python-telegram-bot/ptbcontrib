#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2022
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
"""This module contains the RolesHandler class."""
from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar, Union

from telegram import Update
from telegram.ext import Application, CallbackContext, Handler

from .roles import InvertedRole, Role, Roles

BOT_DATA_KEY: str = "ptbcontrib_roles_bot_data_key"
""":obj:`str`: The key used to store roles in ``bot_data``."""


class RolesBotData(ABC):
    """
    Abstract base class providing an interface to be used by :meth:`set_roles`.
    Inherit from this class when using a custom type for ``bot_data``
    """

    @abstractmethod
    def get_roles(self) -> Optional[Roles]:
        """
        An abstract method meant to fetch an existing set of roles.
        Must be overridden.

        Returns:
            The preexisting :class: 'Roles' instance, if there is one
        """

    @abstractmethod
    def set_roles(self, roles: Roles) -> None:
        """
        An abstract method that implements a set of roles.
        Must be overridden.

        Args:
            roles (:class: 'Roles'): The set of roles
        """


def setup_roles(application: Application) -> Roles:
    """
    Checks if :attr:`application.bot_data` stores an instance
    of the class :class:`ptbcontrib.roles.Roles` and creates a new one, if not.
    If :attr:`application.bot_data` is a dict, the ``Roles`` object will be saved  under the key
    :attr:`BOT_DATA_KEY`. Otherwise, :attr:`application.bot_data` must be an instance of
    :class:`RolesBotData` and the corresponding methods will be used to retrieve and save the
    ``Roles`` object.

    Args:
        application (:class:`telegram.ext.Application`): The application

    Returns:
        The :class:`ptbcontrib.roles.Roles` instance to be used.
    """
    if isinstance(application.bot_data, RolesBotData):
        roles = application.bot_data.get_roles()
        if roles is None:
            roles = Roles(application.bot)
            application.bot_data.set_roles(roles)
            return roles

        return roles

    if isinstance(application.bot_data, dict):
        return application.bot_data.setdefault(BOT_DATA_KEY, Roles(application.bot))

    raise TypeError("bot_data must either be a dict or implement RolesBotData!")


_CCT = TypeVar("_CCT", bound=CallbackContext)


class RolesHandler(Handler[Update, _CCT]):
    """
    A handler that acts as wrapper for existing handler classes allowing to add roles for
    user access management. You must call :meth:`setup_roles` before this handler can work.
    The :class:`ptbcontrib.roles.Roles` instance will then be available as ``context.roles`` in the
    callback.

    Note:
        As :class:`ptbcontrib.roles.Roles` does not allow updates that have neither effective user
        nor effective chat, this handler wrapper should not be used in combination with handlers
        that handle such updates, e.g. :class:`telegram.ext.StringCommandHandler`.

    Args:
        handler (:class:`telegram.ext.Handler`): The handler to wrap.
        roles (:class:`ptbcontrib.roles.Roles`): The roles to apply to the handler. Can be combined
            with bitwise operations.
    """

    def __init__(self, handler: Handler[Update, _CCT], roles: Role) -> None:
        self.handler = handler
        self.roles: Union[Role, InvertedRole] = roles
        super().__init__(self.handler.callback)

    def check_update(self, update: object) -> Any:
        """Checks if the update should be handled."""
        if not isinstance(update, Update):
            return False
        if self.roles.check_update(update):
            return self.handler.check_update(update)
        return False

    def collect_additional_context(
        self,
        context: _CCT,
        update: Update,
        application: Application,
        check_result: Any,
    ) -> None:
        """Makes the roles accessible via ``context.roles``."""
        self.handler.collect_additional_context(context, update, application, check_result)

        if isinstance(context.bot_data, dict):
            if BOT_DATA_KEY not in context.bot_data:
                raise RuntimeError(
                    "You must set a Roles instance before you can use RolesHandlers."
                )
            context.roles = context.bot_data[BOT_DATA_KEY]
            return

        if isinstance(context.bot_data, RolesBotData):
            roles = application.bot_data.get_roles()
            if roles is None:
                raise RuntimeError(
                    "You must set a Roles instance before you can use RolesHandlers."
                )
            context.roles = roles
            return

        raise TypeError("bot_data must either be a dict or implement RolesBotData!")
