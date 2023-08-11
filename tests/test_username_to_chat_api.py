import pytest
from httpx import AsyncClient, Response
from telegram import Chat, error

from ptbcontrib.username_to_chat_api import UsernameToChatAPI


class TestUsernameToChatAPI:
    async def test_normal_run(self, monkeypatch, bot):
        api_result_json = {
            "ok": True,
            "result": {
                "id": 123,
                "type": "private",
                "username": "username",
                "first_name": "name",
                "last_name": "last_name",
                "bio": "A description.",
            },
        }
        api_result = Response(200, json=api_result_json)

        async def get(*args, **kwargs):
            return api_result

        # this tests the non initialized AsyncClient

        wrapper = UsernameToChatAPI("URL", "key", bot)
        monkeypatch.setattr(wrapper._client, "get", get)
        chat = await wrapper.resolve("username")
        assert type(chat) is Chat
        assert chat.id == 123
        assert chat.type == Chat.PRIVATE
        assert chat.username == "username"
        assert chat.first_name == "name"
        assert chat.last_name == "last_name"
        assert chat.bio == "A description."

    async def test_normal_run_channel(self, monkeypatch, bot):
        api_result_json = {
            "ok": True,
            "result": {
                "id": 123,
                "type": "channel",
                "username": "username",
                "title": "channel_name",
                "description": "A description.",
            },
        }
        api_result = Response(200, json=api_result_json)

        async def get(*args, **kwargs):
            return api_result

        # this tests passing the initialized AsyncClient
        test_client = AsyncClient()
        wrapper = UsernameToChatAPI("URL", "key", bot, test_client)
        monkeypatch.setattr(wrapper._client, "get", get)
        chat = await wrapper.resolve("username")
        assert type(chat) is Chat
        assert chat.id == 123
        assert chat.type == Chat.CHANNEL
        assert chat.username == "username"
        assert chat.title == "channel_name"
        assert chat.description == "A description."

    @pytest.mark.parametrize(
        "error_code,description, error_object",
        [
            (401, "Unauthorized", error.Forbidden),
            (400, "Bad Request: chat not found", error.BadRequest),
            (429, "Telegram forces us to wait", error.RetryAfter),
            (499, "This cant happen", error.TelegramError),
        ],
    )
    async def test_errors(self, monkeypatch, bot, error_code, description, error_object):
        api_result_json = {"ok": False, "error_code": error_code, "description": description}
        if error_code == 429:
            # this adds the flood wait time when the flood wait error happens
            api_result_json["retry_after"] = 12
        api_result = Response(error_code, json=api_result_json)

        async def get(*args, **kwargs):
            return api_result

        wrapper = UsernameToChatAPI("URL", "key", bot)
        monkeypatch.setattr(wrapper._client, "get", get)

        with pytest.raises(error_object):
            await wrapper.resolve("username")

        if error_code == 429:
            try:
                await wrapper.resolve("username")
            except error.RetryAfter as e:
                # specific check that the flood wait time out is provided
                assert e.retry_after == 12

    async def test_shutdown(self, bot):
        # not much to test here, just making sure no errors are raised

        wrapper = UsernameToChatAPI("URL", "key", bot)
        await wrapper.shutdown()

        test_client = AsyncClient()
        wrapper = UsernameToChatAPI("URL", "key", bot, test_client)
        await test_client.aclose()
        await wrapper.shutdown()
