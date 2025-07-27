#!/usr/bin/env python
#
# A library that provides a Python interface to the Telegram Bot API
# Copyright (C) 2015-2025
# Leandro Toledo de Souza <devs@python-telegram-bot.org>
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
"""Here we run tests directly with HTTPXRequest because that's easier than providing dummy
implementations for BaseRequest and we want to test HTTPXRequest anyway."""
import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import Coroutine
from http import HTTPStatus
from typing import Any, Callable, Optional

import aiohttp
import multidict
import pytest
import yarl
from telegram import InputFile
from telegram._utils.defaultvalue import DEFAULT_NONE
from telegram._utils.strings import TextEncoding
from telegram._utils.types import ODVInput
from telegram.error import (
    BadRequest,
    ChatMigrated,
    Conflict,
    Forbidden,
    InvalidToken,
    NetworkError,
    RetryAfter,
    TelegramError,
    TimedOut,
)
from telegram.request import RequestData
from telegram.request._requestparameter import RequestParameter

from ptbcontrib.aiohttp_request import AiohttpRequest


def mocker_factory(
    response: bytes, return_code: int = HTTPStatus.OK
) -> Callable[[tuple[Any]], Coroutine[Any, Any, tuple[int, bytes]]]:
    async def make_assertion(*args, **kwargs):
        return return_code, response

    return make_assertion


class NonchalantAiohttpRequest(AiohttpRequest):
    """This Request class is used in the tests to suppress errors that we don't care about
    in the test suite.
    """

    async def _request_wrapper(
        self,
        method: str,
        url: str,
        request_data: Optional[RequestData] = None,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
    ) -> bytes:
        try:
            return await super()._request_wrapper(
                method=method,
                url=url,
                request_data=request_data,
                read_timeout=read_timeout,
                write_timeout=write_timeout,
                connect_timeout=connect_timeout,
                pool_timeout=pool_timeout,
            )
        except RetryAfter as e:
            pytest.xfail(f"Not waiting for flood control: {e}")
        except TimedOut as e:
            pytest.xfail(f"Ignoring TimedOut error: {e}")


@pytest.fixture
async def aiohttp_request():
    async with NonchalantAiohttpRequest() as rq:
        yield rq


class Response:
    status = HTTPStatus.OK

    @staticmethod
    async def read():
        return b"content"


class TestRequest:
    test_flag = None

    @pytest.fixture(autouse=True)
    def _reset(self):
        self.test_flag = None

    def test_aiohttp_kwargs(self, monkeypatch):
        self.test_flag = {}

        orig_init = aiohttp.ClientSession.__init__

        class Session(aiohttp.ClientSession):
            def __init__(*args, **kwargs):
                orig_init(*args, **kwargs)
                self.test_flag["args"] = args
                self.test_flag["kwargs"] = kwargs

        monkeypatch.setattr(aiohttp, "ClientSession", Session)

        AiohttpRequest(
            client_timeout=aiohttp.ClientTimeout(total=1.0),
            aiohttp_kwargs={
                "timeout": aiohttp.ClientTimeout(total=40.0),
            },
        )
        kwargs = self.test_flag["kwargs"]

        assert kwargs["timeout"].total == 40

    async def test_context_manager(self, monkeypatch):
        async def initialize():
            self.test_flag = ["initialize"]

        async def shutdown():
            self.test_flag.append("stop")

        aiohttp_request = NonchalantAiohttpRequest()

        monkeypatch.setattr(aiohttp_request, "initialize", initialize)
        monkeypatch.setattr(aiohttp_request, "shutdown", shutdown)

        async with aiohttp_request:
            pass

        assert self.test_flag == ["initialize", "stop"]

    async def test_context_manager_exception_on_init(self, monkeypatch):
        async def initialize():
            raise RuntimeError("initialize")

        async def shutdown():
            self.test_flag = "stop"

        aiohttp_request = NonchalantAiohttpRequest()

        monkeypatch.setattr(aiohttp_request, "initialize", initialize)
        monkeypatch.setattr(aiohttp_request, "shutdown", shutdown)

        with pytest.raises(RuntimeError, match="initialize"):
            async with aiohttp_request:
                pass

        assert self.test_flag == "stop"

    async def test_replaced_unprintable_char(self, monkeypatch, aiohttp_request):
        """Clients can send arbitrary bytes in callback data. Make sure that we just replace
        those
        """
        server_response = b'{"result": "test_string\x80"}'

        monkeypatch.setattr(
            aiohttp_request, "do_request", mocker_factory(response=server_response)
        )

        assert await aiohttp_request.post(None, None, None) == "test_string�"
        # Explicitly call `parse_json_payload` here is well so that this public method is covered
        # not only implicitly.
        assert aiohttp_request.parse_json_payload(server_response) == {"result": "test_string�"}

    async def test_illegal_json_response(
        self, monkeypatch, aiohttp_request: AiohttpRequest, caplog
    ):
        # for proper JSON it should be `"result":` instead of `result:`
        server_response = b'{result: "test_string"}'

        monkeypatch.setattr(
            aiohttp_request, "do_request", mocker_factory(response=server_response)
        )

        with (
            pytest.raises(TelegramError, match="Invalid server response"),
            caplog.at_level(logging.ERROR),
        ):
            await aiohttp_request.post(None, None, None)

        await aiohttp_request.shutdown()

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.name == "telegram.request.BaseRequest"
        assert record.getMessage().endswith(f'invalid JSON data: "{server_response.decode()}"')

    async def test_chat_migrated(self, monkeypatch, aiohttp_request: AiohttpRequest):
        server_response = b'{"ok": "False", "parameters": {"migrate_to_chat_id": 123}}'

        monkeypatch.setattr(
            aiohttp_request,
            "do_request",
            mocker_factory(response=server_response, return_code=HTTPStatus.BAD_REQUEST),
        )

        with pytest.raises(ChatMigrated, match="New chat id: 123") as exc_info:
            await aiohttp_request.post(None, None, None)

        assert exc_info.value.new_chat_id == 123

    async def test_retry_after(self, monkeypatch, aiohttp_request: AiohttpRequest):
        server_response = b'{"ok": "False", "parameters": {"retry_after": 42}}'

        monkeypatch.setattr(
            aiohttp_request,
            "do_request",
            mocker_factory(response=server_response, return_code=HTTPStatus.BAD_REQUEST),
        )

        with pytest.raises(RetryAfter, match="Retry in 42") as exc_info:
            await aiohttp_request.post(None, None, None)

        assert exc_info.value.retry_after == 42

    async def test_unknown_request_params(self, monkeypatch, aiohttp_request: AiohttpRequest):
        server_response = b'{"ok": "False", "parameters": {"unknown": "42"}}'

        monkeypatch.setattr(
            aiohttp_request,
            "do_request",
            mocker_factory(response=server_response, return_code=HTTPStatus.BAD_REQUEST),
        )

        with pytest.raises(
            BadRequest,
            match="{'unknown': '42'}",
        ):
            await aiohttp_request.post(None, None, None)

    @pytest.mark.parametrize("description", [True, False])
    async def test_error_description(
        self, monkeypatch, aiohttp_request: AiohttpRequest, description
    ):
        response_data = {"ok": "False"}
        if description:
            match = "ErrorDescription"
            response_data["description"] = match
        else:
            match = "Unknown HTTPError"

        server_response = json.dumps(response_data).encode(TextEncoding.UTF_8)

        monkeypatch.setattr(
            aiohttp_request,
            "do_request",
            mocker_factory(response=server_response, return_code=-1),
        )

        with pytest.raises(NetworkError, match=match):
            await aiohttp_request.post(None, None, None)

        # Special casing for bad gateway
        if not description:
            monkeypatch.setattr(
                aiohttp_request,
                "do_request",
                mocker_factory(response=server_response, return_code=HTTPStatus.BAD_GATEWAY),
            )

            with pytest.raises(NetworkError, match="Bad Gateway"):
                await aiohttp_request.post(None, None, None)

    @pytest.mark.parametrize(
        ("code", "exception_class"),
        [
            (HTTPStatus.FORBIDDEN, Forbidden),
            (HTTPStatus.NOT_FOUND, InvalidToken),
            (HTTPStatus.UNAUTHORIZED, InvalidToken),
            (HTTPStatus.BAD_REQUEST, BadRequest),
            (HTTPStatus.CONFLICT, Conflict),
            (HTTPStatus.BAD_GATEWAY, NetworkError),
            (-1, NetworkError),
        ],
    )
    async def test_special_errors(
        self, monkeypatch, aiohttp_request: AiohttpRequest, code, exception_class
    ):
        server_response = b'{"ok": "False", "description": "Test Message"}'

        monkeypatch.setattr(
            aiohttp_request,
            "do_request",
            mocker_factory(response=server_response, return_code=code),
        )

        with pytest.raises(exception_class, match="Test Message"):
            await aiohttp_request.post("", None, None)

    @pytest.mark.parametrize(
        ("exception", "catch_class", "match"),
        [
            (TelegramError("TelegramError"), TelegramError, "TelegramError"),
            (
                RuntimeError("CustomError"),
                NetworkError,
                r"HTTP implementation: RuntimeError\('CustomError'\)",
            ),
        ],
    )
    async def test_exceptions_in_do_request(
        self, monkeypatch, aiohttp_request: AiohttpRequest, exception, catch_class, match
    ):
        async def do_request(*args, **kwargs):
            raise exception

        monkeypatch.setattr(
            aiohttp_request,
            "do_request",
            do_request,
        )

        with pytest.raises(catch_class, match=match) as exc_info:
            await aiohttp_request.post(None, None, None)

        if catch_class is NetworkError:
            assert exc_info.value.__cause__ is exception

    async def test_retrieve(self, monkeypatch, aiohttp_request):
        """Here we just test that retrieve gives us the raw bytes instead of trying to parse them
        as json
        """
        server_response = b'{"result": "test_string\x80"}'

        monkeypatch.setattr(
            aiohttp_request, "do_request", mocker_factory(response=server_response)
        )

        assert await aiohttp_request.retrieve(None, None) == server_response

    async def test_timeout_propagation_to_do_request(self, monkeypatch, aiohttp_request):
        async def make_assertion(*args, **kwargs):
            self.test_flag = (
                kwargs.get("read_timeout"),
                kwargs.get("connect_timeout"),
                kwargs.get("write_timeout"),
                kwargs.get("pool_timeout"),
            )
            return HTTPStatus.OK, b'{"ok": "True", "result": {}}'

        monkeypatch.setattr(aiohttp_request, "do_request", make_assertion)

        await aiohttp_request.post("url", None)
        assert self.test_flag == (DEFAULT_NONE, DEFAULT_NONE, DEFAULT_NONE, DEFAULT_NONE)

        await aiohttp_request.post(
            "url", None, read_timeout=1, connect_timeout=2, write_timeout=3, pool_timeout=4
        )
        assert self.test_flag == (1, 2, 3, 4)


class TestAiohttpRequest:
    test_flag = None

    @pytest.fixture(autouse=True)
    def _reset(self):
        self.test_flag = None

    def test_init(self, monkeypatch):

        request = AiohttpRequest()
        assert request._session.timeout == aiohttp.ClientTimeout(total=15)
        assert request._session._default_proxy is None
        assert request._session._version is aiohttp.HttpVersion11

        request = AiohttpRequest(
            connection_pool_size=42,
            client_timeout=aiohttp.ClientTimeout(total=25),
            media_total_timeout=200,
            proxy="proxy",
            proxy_auth=aiohttp.BasicAuth("user", "pass"),
            trust_env=True,
        )
        assert request._session._default_proxy == "proxy"
        assert request._session._default_proxy_auth == aiohttp.BasicAuth("user", "pass")
        assert request._session.timeout == aiohttp.ClientTimeout(total=25)
        assert request._media_total_timeout == 200
        assert request._session._trust_env

    async def test_multiple_inits_and_shutdowns(self, monkeypatch):
        self.test_flag = defaultdict(int)

        orig_init = aiohttp.ClientSession.__init__
        orig_close = aiohttp.ClientSession.close

        class Session(aiohttp.ClientSession):
            def __init__(*args, **kwargs):
                orig_init(*args, **kwargs)
                self.test_flag["init"] += 1

            async def close(*args, **kwargs):
                await orig_close(*args, **kwargs)
                self.test_flag["shutdown"] += 1

        monkeypatch.setattr(aiohttp, "ClientSession", Session)

        # Create a new one instead of using the fixture so that the mocking can work
        aiohttp_request = AiohttpRequest()

        await aiohttp_request.initialize()
        await aiohttp_request.initialize()
        await aiohttp_request.initialize()
        await aiohttp_request.shutdown()
        await aiohttp_request.shutdown()
        await aiohttp_request.shutdown()

        assert self.test_flag["init"] == 1
        assert self.test_flag["shutdown"] == 1

    async def test_do_request_after_shutdown(self, aiohttp_request):
        await aiohttp_request.shutdown()
        with pytest.raises(RuntimeError, match="not initialized"):
            await aiohttp_request.do_request(url="url", method="GET")

    async def test_context_manager(self, monkeypatch):
        async def initialize():
            self.test_flag = ["initialize"]

        async def close(*args):
            self.test_flag.append("stop")

        aiohttp_request = NonchalantAiohttpRequest()

        monkeypatch.setattr(aiohttp_request, "initialize", initialize)
        monkeypatch.setattr(aiohttp.ClientSession, "close", close)

        async with aiohttp_request:
            pass

        assert self.test_flag == ["initialize", "stop"]

    async def test_context_manager_exception_on_init(self, monkeypatch):
        async def initialize():
            raise RuntimeError("initialize")

        async def shutdown(*args):
            self.test_flag = "stop"

        aiohttp_request = NonchalantAiohttpRequest()

        monkeypatch.setattr(aiohttp_request, "initialize", initialize)
        monkeypatch.setattr(aiohttp_request, "shutdown", shutdown)

        with pytest.raises(RuntimeError, match="initialize"):
            async with aiohttp_request:
                pass

        assert self.test_flag == "stop"

    async def test_do_request_default_timeouts(self, monkeypatch):
        default_timeouts = aiohttp.ClientTimeout(
            total=42, connect=43, sock_read=44, sock_connect=45, ceil_threshold=46
        )

        async def make_assertion(_, **kwargs):
            self.test_flag = kwargs.get("timeout") == default_timeouts
            return Response()

        async with AiohttpRequest(client_timeout=default_timeouts) as aiohttp_request:
            monkeypatch.setattr(aiohttp.ClientSession, "request", make_assertion)
            await aiohttp_request.do_request(method="GET", url="URL")

        assert self.test_flag

    async def test_do_request_manual_timeouts(self, monkeypatch, aiohttp_request):
        default_timeouts = aiohttp.ClientTimeout(
            total=42, connect=43, sock_read=44, sock_connect=45, ceil_threshold=46
        )
        manual_timeouts = aiohttp.ClientTimeout(
            total=42, connect=53, sock_read=54, sock_connect=55, ceil_threshold=56
        )

        async def make_assertion(_, **kwargs):
            print(kwargs.get("timeout"))
            self.test_flag = kwargs.get("timeout") == manual_timeouts
            return Response()

        async with AiohttpRequest(client_timeout=default_timeouts) as aiohttp_request_ctx:
            monkeypatch.setattr(aiohttp.ClientSession, "request", make_assertion)
            await aiohttp_request_ctx.do_request(
                method="GET",
                url="URL",
                connect_timeout=manual_timeouts.sock_connect,
                read_timeout=manual_timeouts.sock_read,
                write_timeout=manual_timeouts.ceil_threshold,
                pool_timeout=manual_timeouts.connect,
            )

        assert self.test_flag

    async def test_do_request_params_no_data(self, monkeypatch, aiohttp_request):
        async def make_assertion(self, **kwargs):
            method_assertion = kwargs.get("method") == "method"
            url_assertion = kwargs.get("url") == "url"
            data_assertion = kwargs.get("data")._fields == []
            if method_assertion and url_assertion and data_assertion:
                return Response()
            r = Response()
            r.status = HTTPStatus.BAD_REQUEST
            return r

        monkeypatch.setattr(aiohttp.ClientSession, "request", make_assertion)
        code, _ = await aiohttp_request.do_request(method="method", url="url")
        assert code == HTTPStatus.OK

    async def test_do_request_params_with_data(self, monkeypatch, aiohttp_request):
        mixed_rqs = RequestData(
            [
                RequestParameter("name", "value", [InputFile(obj="data", attach=True)]),
                RequestParameter("second_name", "second_value", []),
            ]
        )

        async def make_assertion(self, **kwargs):
            method_assertion = kwargs.get("method") == "method"
            url_assertion = kwargs.get("url") == "url"
            # Kinda annoying to test this right now should be better
            data_assertion = kwargs.get("data") != []
            if method_assertion and url_assertion and data_assertion:
                return Response()
            r = Response()
            r.status = HTTPStatus.BAD_REQUEST
            return r

        monkeypatch.setattr(aiohttp.ClientSession, "request", make_assertion)
        code, _ = await aiohttp_request.do_request(
            method="method",
            url="url",
            request_data=mixed_rqs,
        )
        assert code == HTTPStatus.OK

    async def test_do_request_return_value(self, monkeypatch, aiohttp_request):
        async def make_assertion(self, **kwargs):
            return Response()

        monkeypatch.setattr(aiohttp.ClientSession, "request", make_assertion)
        code, content = await aiohttp_request.do_request(
            "method",
            "url",
        )
        assert code == HTTPStatus.OK
        assert content == b"content"

    @pytest.mark.parametrize(
        ("raised_exception", "expected_class", "expected_message"),
        [
            (aiohttp.SocketTimeoutError("timeout"), TimedOut, "Timed out"),
            (
                aiohttp.ClientResponseError(
                    aiohttp.RequestInfo(
                        yarl.URL(""), "GET", multidict.CIMultiDict({"test": "test"})
                    ),
                    (),
                ),
                NetworkError,
                "aiohttp.ClientResponseError: 0, message='', url=''",
            ),
        ],
    )
    async def test_do_request_exceptions(
        self, monkeypatch, aiohttp_request, raised_exception, expected_class, expected_message
    ):
        async def make_assertion(self, **kwargs):
            raise raised_exception

        monkeypatch.setattr(aiohttp.ClientSession, "request", make_assertion)

        with pytest.raises(expected_class, match=expected_message) as exc_info:
            await aiohttp_request.do_request(
                "method",
                "url",
            )

        assert exc_info.value.__cause__ is raised_exception

    async def test_do_request_server_timeout_timeout(self, monkeypatch):
        server_timeout_timeout = aiohttp.ServerTimeoutError("Server timeout")

        async def request(_, **kwargs):
            if self.test_flag is None:
                self.test_flag = True
            else:
                raise server_timeout_timeout
            return Response()

        monkeypatch.setattr(aiohttp.ClientSession, "request", request)

        async with AiohttpRequest() as httpx_request:
            with pytest.raises(TimedOut, match="Timed out") as exc_info:
                await asyncio.gather(
                    httpx_request.do_request(method="GET", url="URL"),
                    httpx_request.do_request(method="GET", url="URL"),
                )

            assert exc_info.value.__cause__ is server_timeout_timeout

    @pytest.mark.parametrize("read_timeout", [None, 1, 2, 3])
    async def test_read_timeout_property(self, read_timeout):
        assert (
            AiohttpRequest(client_timeout=aiohttp.ClientTimeout(total=read_timeout)).read_timeout
            == read_timeout
        )


class TestAiohttpRequestWithRequest:
    async def test_multiple_init_cycles(self):
        # nothing really to assert - this should just not fail
        aiohttp_request = AiohttpRequest()
        async with aiohttp_request:
            await aiohttp_request.do_request(url="https://python-telegram-bot.org", method="GET")
        async with aiohttp_request:
            await aiohttp_request.do_request(url="https://python-telegram-bot.org", method="GET")

    async def test_do_request_wait_for_pool(self):
        """The pool logic is buried rather deeply in httpxcore, so we make actual requests here
        instead of mocking"""
        aiohttp_request = AiohttpRequest()
        task_1 = asyncio.create_task(
            aiohttp_request.do_request(
                method="GET", url="https://python-telegram-bot.org/static/testfiles/telegram.mp4"
            )
        )
        task_2 = asyncio.create_task(
            aiohttp_request.do_request(
                method="GET", url="https://python-telegram-bot.org/static/testfiles/telegram.mp4"
            )
        )
        done, pending = await asyncio.wait({task_1, task_2}, return_when=asyncio.FIRST_COMPLETED)
        assert len(done) == len(pending) == 1
        done, pending = await asyncio.wait({task_1, task_2}, return_when=asyncio.ALL_COMPLETED)
        assert len(done) == 2
        assert len(pending) == 0
        try:  # retrieve exceptions from tasks
            task_1.exception()
            task_2.exception()
        except (asyncio.CancelledError, asyncio.InvalidStateError):
            pass

    # async def test_input_file_postponed_read(self, bot, chat_id):
    #     """Here we test that `read_file_handle=False` is correctly handled by HTTPXRequest.
    #     Since manually building the RequestData object has no real benefit, we simply use the Bot
    #     for that.
    #     """
    #     message = await bot.send_document(
    #         document=InputFile(data_file("telegram.jpg").open("rb"), read_file_handle=False),
    #         chat_id=chat_id,
    #     )
    #     assert message.document
    #     assert message.document.file_name == "telegram.jpg"
