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
from telegram.error import TelegramError

from ptbcontrib.send_by_kwargs import send_by_kwargs
from ptbcontrib.send_by_kwargs.send_by_kwargs import _CACHED_SIGNATURES, _UNIQUE_KWARGS

temp = list(_UNIQUE_KWARGS.items())
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
    async def test_correct_selection(self, method, args, bot):
        if method == "send_dice":
            pytest.skip("send_dice only has one required parameter anyway")

        kwargs = {args[0]: args[0]}

        with pytest.raises(
            KeyError, match=f"Selected method '{method}', but the required parameter"
        ):
            await send_by_kwargs(bot, kwargs)

        with pytest.raises(
            KeyError, match=f"Selected method '{method}', but the required parameter"
        ):
            await send_by_kwargs(bot, **kwargs)

    async def test_correct_selection_none(self, bot):
        """Makes sure that send_photo is selected even if a key `document` is present if the
        value is None"""
        with pytest.raises(KeyError, match="Selected method 'send_photo'"):
            await send_by_kwargs(bot, document=None, photo="photo")

    @pytest.mark.parametrize(
        argnames="method",
        argvalues=list(UNIQUE_KWARGS_SHUFFLED),
    )
    async def test_kwargs_passing(self, method, bot, monkeypatch):
        """
        This essentially makes sure that get_relevant_kwargs doesn't pass kwargs that are not
        accepted by the selected method.
        """

        signature = inspect.signature(getattr(bot, method))
        expected_kwargs = {name: True for name, param in signature.parameters.items()}
        kwargs = expected_kwargs.copy()
        kwargs["dummy"] = "this_should_not_be_passed"

        async def make_assertion(**_kwargs):
            self.test_flag = _kwargs == expected_kwargs

        # we're a bit tricky here, because otherwise monkeypatch would fiddle with the signature
        _CACHED_SIGNATURES["make_assertion"] = signature

        monkeypatch.setattr(bot, method, make_assertion)
        await send_by_kwargs(bot, kwargs)
        assert self.test_flag

        self.test_flag = False
        await send_by_kwargs(bot, **kwargs)
        assert self.test_flag

    @pytest.mark.parametrize(
        argnames="method",
        argvalues=list(UNIQUE_KWARGS_SHUFFLED),
    )
    @pytest.mark.parametrize(
        argnames="parse_mode",
        argvalues=[None, "HTML"],
        ids=["default_parse_mode", "custom_parse_mode"],
    )
    async def test_defaults_handling(self, method, parse_mode, bot, monkeypatch):
        """We only test with parse_mode - should suffice"""

        async def make_assertion(**kwargs):
            if parse_mode is None:
                self.test_flag = "parse_mode" not in kwargs
            else:
                self.test_flag = kwargs.get("parse_mode", None) == "HTML"

        signature = inspect.signature(getattr(bot, method))
        if "parse_mode" not in signature.parameters.keys():
            return

        kwargs = {
            name: True
            for name, param in signature.parameters.items()
            if param.default == inspect.Parameter.empty
            # special casing for some methods where the required arguments are not clear
            # due to the fact that we made them optional in order to allow passing e.g. a Venue
            # directly
            or name in ["latitude", "longitude", "address", "phone_number", "first_name"]
        }
        if parse_mode is not None:
            kwargs["parse_mode"] = "HTML"

        # we're a bit tricky here, because otherwise monkeypatch would fiddle with the signature
        _CACHED_SIGNATURES["make_assertion"] = signature

        monkeypatch.setattr(bot, method, make_assertion)
        await send_by_kwargs(bot, kwargs)
        assert self.test_flag

        self.test_flag = False
        await send_by_kwargs(bot, **kwargs)
        assert self.test_flag

    async def test_fallback_behavior(self, monkeypatch, bot):
        async def make_assertion(**kwargs):
            self.test_flag = True

        signature = inspect.signature(bot.send_dice)
        _CACHED_SIGNATURES["make_assertion"] = signature
        monkeypatch.setattr(bot, "send_dice", make_assertion)
        await send_by_kwargs(bot, {"chat_id": 1})
        assert self.test_flag

        with pytest.raises(RuntimeError, match="Could not find a bot method"):
            await send_by_kwargs(bot, {})

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
    async def test_kwarg_mixing(self, bot, monkeypatch, kwargs, _kwargs):
        expected_kwargs = {"chat_id": 123, "text": "Hello there"}

        async def make_assertion(**kw):
            self.test_flag = kw == expected_kwargs

        signature = inspect.signature(bot.send_message)
        _CACHED_SIGNATURES["make_assertion"] = signature
        monkeypatch.setattr(bot, "send_message", make_assertion)
        await send_by_kwargs(bot, kwargs, **_kwargs)
        assert self.test_flag

    async def test_method_raises_exception(self, bot, monkeypatch):
        async def mock(**_kw):
            raise TelegramError("Error")

        signature = inspect.signature(bot.send_message)
        _CACHED_SIGNATURES["mock"] = signature
        monkeypatch.setattr(bot, "send_message", mock)
        with pytest.raises(RuntimeError, match="Selected method 'mock', but it raised"):
            await send_by_kwargs(bot, chat_id=123, text="Hi")
