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
import inspect
import random

import pytest
from telegram import TelegramError

from ptbcontrib.send_by_kwargs import send_by_kwargs
from ptbcontrib.send_by_kwargs.send_by_kwargs import CACHED_SIGNATURES, UNIQUE_KWARGS

temp = list(UNIQUE_KWARGS.items())
random.shuffle(temp)
UNIQUE_KWARGS_SHUFFLED = {key: value for key, value in temp}


class TestSendByKwargs:
    test_flag = False

    @pytest.fixture(scope="function", autouse=True)
    def reset(self):
        self.test_flag = False

    @pytest.mark.parametrize(
        argnames="method,args",
        argvalues=list(UNIQUE_KWARGS_SHUFFLED.items()),
        ids=list(UNIQUE_KWARGS_SHUFFLED),
    )
    def test_correct_selection(self, method, args, bot):
        if method == "send_dice":
            pytest.skip("send_dice only has one required parameter anyway")

        kwargs = {args[0]: args[0]}

        with pytest.raises(
            KeyError, match=f"Selected method '{method}', but the required parameter"
        ):
            send_by_kwargs(bot, kwargs)

        with pytest.raises(
            KeyError, match=f"Selected method '{method}', but the required parameter"
        ):
            send_by_kwargs(bot, **kwargs)

    @pytest.mark.parametrize(
        argnames="method",
        argvalues=list(UNIQUE_KWARGS_SHUFFLED),
    )
    def test_kwargs_passing(self, method, bot, monkeypatch):
        """
        This essentially makes sure that get_relevant_kwargs doesn't pass kwargs that are not
        accepted by the selected method.
        """

        signature = inspect.signature(getattr(bot, method))
        expected_kwargs = {name: True for name, param in signature.parameters.items()}
        kwargs = expected_kwargs.copy()
        kwargs["dummy"] = "this_should_not_be_passed"

        def make_assertion(**_kwargs):
            self.test_flag = _kwargs == expected_kwargs

        # we're a bit tricky here, because otherwise monkeypatch would fiddle with the signature
        CACHED_SIGNATURES["make_assertion"] = signature

        monkeypatch.setattr(bot, method, make_assertion)
        send_by_kwargs(bot, kwargs)
        assert self.test_flag

        self.test_flag = False
        send_by_kwargs(bot, **kwargs)
        assert self.test_flag

    @pytest.mark.parametrize(
        argnames="method",
        argvalues=list(UNIQUE_KWARGS_SHUFFLED),
    )
    @pytest.mark.parametrize(
        argnames="timeout", argvalues=[None, 5], ids=["default_timeout", "custom_timeout"]
    )
    def test_defaults_handling(self, method, timeout, bot, monkeypatch):
        def make_assertion(**kwargs):
            if timeout is None:
                self.test_flag = "timeout" not in kwargs
            else:
                self.test_flag = kwargs.get("timeout", None) == 5

        signature = inspect.signature(getattr(bot, method))
        kwargs = {
            name: True
            for name, param in signature.parameters.items()
            if param.default == inspect.Parameter.empty
            # special casing for some methods where the required arguments are not clear
            # due to the fact that we made them optional in order to allow passing e.g. a Venue
            # directly
            or name in ["latitude", "longitude", "address", "phone_number", "first_name"]
        }
        if timeout is not None:
            kwargs["timeout"] = 5

        # we're a bit tricky here, because otherwise monkeypatch would fiddle with the signature
        CACHED_SIGNATURES["make_assertion"] = signature

        monkeypatch.setattr(bot, method, make_assertion)
        send_by_kwargs(bot, kwargs)
        assert self.test_flag

        self.test_flag = False
        send_by_kwargs(bot, **kwargs)
        assert self.test_flag

    def test_fallback_behavior(self, monkeypatch, bot):
        def make_assertion(**kwargs):
            self.test_flag = True

        signature = inspect.signature(bot.send_dice)
        CACHED_SIGNATURES["make_assertion"] = signature
        monkeypatch.setattr(bot, "send_dice", make_assertion)
        send_by_kwargs(bot, {"chat_id": 1})
        assert self.test_flag

        with pytest.raises(RuntimeError, match="Could not find a bot method"):
            send_by_kwargs(bot, {})

    @pytest.mark.parametrize(
        "kwargs,_kwargs",
        [
            [{"chat_id": 123, "text": "Hello there"}, {}],
            [{}, {"chat_id": 123, "text": "Hello there"}],
            [{"chat_id": 123}, {"text": "Hello there"}],
            [
                {"chat_id": 456, "text": "General Kenobi"},
                {"chat_id": 123, "text": "Hello there"},
            ],
        ],
    )
    def test_kwarg_mixing(self, bot, monkeypatch, kwargs, _kwargs):
        expected_kwargs = {"chat_id": 123, "text": "Hello there"}

        def make_assertion(**kw):
            self.test_flag = kw == expected_kwargs

        signature = inspect.signature(bot.send_message)
        CACHED_SIGNATURES["make_assertion"] = signature
        monkeypatch.setattr(bot, "send_message", make_assertion)
        send_by_kwargs(bot, kwargs, **_kwargs)
        assert self.test_flag

    def test_method_raises_exception(self, bot, monkeypatch):
        def mock(**_kw):
            raise TelegramError()

        signature = inspect.signature(bot.send_message)
        CACHED_SIGNATURES["mock"] = signature
        monkeypatch.setattr(bot, "send_message", mock)
        with pytest.raises(RuntimeError, match="Selected method 'mock', but it raised"):
            send_by_kwargs(bot, chat_id=123, text="Hi")
