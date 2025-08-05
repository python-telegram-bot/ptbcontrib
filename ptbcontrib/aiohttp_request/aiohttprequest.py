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
"""This module contains methods to make POST and GET requests using the aiohttp library."""
import asyncio
import logging
from typing import Any, Optional, Union

import aiohttp
import yarl
from telegram.error import NetworkError, TimedOut
from telegram.request import BaseRequest, RequestData

_LOGGER = logging.getLogger("AiohttpRequest")


class AiohttpRequest(BaseRequest):
    """Implementation of :class:`~telegram.request.BaseRequest` using the aiohttp library.

    Args:
        connection_pool_size (:obj:`int`, optional): Number of connections to keep in the
            connection pool. Defaults to ``1``.
        client_timeout (``aiohttp.ClientTimeout``, optional): Overrides the client timeout
            behaviour if passed. By default all timeout checks are disabled, and total is set
            to ``15`` seconds.

            Note:
                :paramref:`media_total_timeout` will still be applied if a file is send, so be sure
                to also set it to an appropriate value.
        media_total_timeout (:obj:`float` | :obj:`None`, optional): This overrides the total
            timeout with requests that upload media/files. Defaults to ``20`` seconds.
        proxy (:obj:`str` | `yarl.URL``, optional): The URL to a proxy server, aiohttp supports
            plain HTTP proxies and HTTP proxies that can be upgraded to HTTPS via the HTTP
            CONNECT method. See the docs of aiohttp: https://docs.aiohttp.org/en/stable/
            client_advanced.html#aiohttp-client-proxy-support.
        proxy_auth (``aiohttp.BasicAuth``, optional): Proxy authorization, see :paramref:`proxy`.
        trust_env (:obj:`bool`, optional): In order to read proxy environmental variables, see the
            docs of aiohttp: https://docs.aiohttp.org/en/stable/client_advanced.html
            #aiohttp-client-proxy-support.
        aiohttp_kwargs (dict[:obj:`str`, Any], optional): Additional keyword arguments to be passed
            to the aiohttp.ClientSession https://docs.aiohttp.org/en/stable/client_reference.html
            #aiohttp.ClientSession constructor.

            Warning:
                This parameter is intended for advanced users that want to fine-tune the behavior
                of the underlying ``aiohttp`` clientSession. The values passed here will override
                all the defaults set previously and all other parameters passed to
                :class:`ClientSession`, if applicable. The only exception is the
                :paramref:`media_total_timeout` parameter, which is not passed to the client
                constructor. No runtime warnings will be issued about parameters that are
                overridden in this way.

    """

    __slots__ = ("_session", "_session_kwargs", "_media_total_timeout", "_connection_pool_size")

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        connection_pool_size: int = 1,
        client_timeout: Optional[aiohttp.ClientTimeout] = None,
        media_total_timeout: Optional[float] = 30.0,
        proxy: Optional[Union[str, yarl.URL]] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        trust_env: Optional[bool] = None,
        aiohttp_kwargs: Optional[dict[str, Any]] = None,
    ):
        self._media_total_timeout = media_total_timeout
        # this needs to be saved in case of initialize gets a closed session
        self._connection_pool_size = connection_pool_size
        timeout = (
            client_timeout
            if client_timeout
            else aiohttp.ClientTimeout(
                total=15.0,
            )
        )
        # this is needed because there are errors if one uses async with or a normal def
        # with ApplicationBuilder, apparently. I am confused. But it works.

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()

        # I decided against supporting passing options to this one, in comparison to httpx
        # easy to implement if there is demand
        conn = aiohttp.TCPConnector(limit=connection_pool_size, loop=loop)

        self._session_kwargs = {
            "timeout": timeout,
            "connector": conn,
            "proxy": proxy,
            "proxy_auth": proxy_auth,
            "trust_env": trust_env,
            **(aiohttp_kwargs or {}),
        }

        self._session = self._build_client()

    @property
    def read_timeout(self) -> Optional[float]:
        """See :attr:`BaseRequest.read_timeout`.

        aiohttp does not have a read timeout. Instead the total timeout for a request (including
        connection establishment, request sending and response reading) is returned.
        """
        return self._session.timeout.total

    def _build_client(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(**self._session_kwargs)

    async def initialize(self) -> None:
        """See :meth:`BaseRequest.initialize`."""
        if self._session.closed:
            # this means the TCPConnector has been closed, so we need to recreate it
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()

            conn = aiohttp.TCPConnector(limit=self._connection_pool_size, loop=loop)
            self._session_kwargs["connector"] = conn
            self._session = self._build_client()

    async def shutdown(self) -> None:
        """See :meth:`BaseRequest.shutdown`."""
        if self._session.closed:
            _LOGGER.debug("This AiohttpRequest is already shut down. Returning.")
            return

        await self._session.close()

    async def do_request(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        url: str,
        method: str,
        request_data: Optional[RequestData] = None,
        read_timeout: Optional[float] = BaseRequest.DEFAULT_NONE,
        write_timeout: Optional[float] = BaseRequest.DEFAULT_NONE,
        connect_timeout: Optional[float] = BaseRequest.DEFAULT_NONE,
        pool_timeout: Optional[float] = BaseRequest.DEFAULT_NONE,
    ) -> tuple[int, bytes]:
        """See :meth:`BaseRequest.do_request`.

        Since aiohttp has different timeouts, the params were mapped.

        * :paramref:`pool_timeout` is mapped to :attr`~aiohttp.ClientTimeout.connect`
        * :paramref:`connect_timeout` is mapped to :attr`~aiohttp.ClientTimeout.sock_connect`
        * :paramref:`read_timeout` is mapped to :attr`~aiohttp.ClientTimeout.sock_read`
        * :paramref:`write_timeout` is mapped to :attr`~aiohttp.ClientTimeout.ceil_threshold`

        The :attr`~aiohttp.ClientTimeout.total` timeout is not changed since it also includes
        response reading. You can only change them when initializing the class.
        """
        if self._session.closed:
            raise RuntimeError("This AiohttpRequest is not initialized!")

        if request_data and request_data.json_parameters:
            data = aiohttp.FormData(request_data.json_parameters)
        else:
            data = aiohttp.FormData()
        if request_data and request_data.multipart_data:
            for field_name in request_data.multipart_data:
                data.add_field(
                    field_name,
                    request_data.multipart_data[field_name][1],
                    filename=request_data.multipart_data[field_name][0],
                )

        # If user did not specify timeouts (for e.g. in a bot method), use the default ones when we
        # created this instance.
        if read_timeout is BaseRequest.DEFAULT_NONE:
            read_timeout = self._session_kwargs["timeout"].sock_read
        if connect_timeout is BaseRequest.DEFAULT_NONE:
            connect_timeout = self._session_kwargs["timeout"].sock_connect
        if pool_timeout is BaseRequest.DEFAULT_NONE:
            pool_timeout = self._session_kwargs["timeout"].connect
        if write_timeout is BaseRequest.DEFAULT_NONE:
            write_timeout = self._session_kwargs["timeout"].ceil_threshold

        timeout = aiohttp.ClientTimeout(
            total=(
                self._media_total_timeout
                if (request_data and request_data.contains_files)
                else self._session_kwargs["timeout"].total
            ),
            connect=pool_timeout,
            sock_read=read_timeout,
            sock_connect=connect_timeout,
            ceil_threshold=write_timeout,
        )

        try:
            res = await self._session.request(
                method=method,
                url=url,
                headers={"User-Agent": self.USER_AGENT},
                timeout=timeout,
                data=data,
            )
        # asyncio.TimeoutError is an alias of TimeoutError only starting with Python 3.11.
        except asyncio.TimeoutError as err:
            if isinstance(err, aiohttp.ConnectionTimeoutError):
                raise TimedOut(
                    message=(
                        "Pool timeout: All connections in the connection pool are occupied. "
                        "Request was *not* sent to Telegram. Consider adjusting the connection "
                        "pool size or the pool timeout."
                    )
                ) from err
            raise TimedOut from err
        except aiohttp.ClientError as err:
            # HTTPError must come last as its the base aiohttp exception class
            # p4: do something smart here; for now just raise NetworkError

            # We include the class name for easier debugging. Especially useful if the error
            # message of `err` is empty.
            raise NetworkError(f"aiohttp.{err.__class__.__name__}: {err}") from err

        return res.status, await res.read()
