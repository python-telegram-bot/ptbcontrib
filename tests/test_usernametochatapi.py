import pytest
from telegram import Chat, error

try:
    import telegram.vendor.ptb_urllib3.urllib3 as urllib3
except ImportError:  # pragma: no cover
    import urllib3

try:
    import ujson as json
except ImportError:
    import json

from ptbcontrib.username_to_chat_api import UsernameToChatAPI


class TestUsernameToChatAPI:
    def test_normal_run(self, monkeypatch, bot):
        api_result = {
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

        response = urllib3.response.HTTPResponse(body=json.dumps(api_result).encode("UTF-8"))

        def mockreturn(*args, **kwargs):
            return response

        monkeypatch.setattr(urllib3.PoolManager, "request", mockreturn)
        wrapper = UsernameToChatAPI("URL", "key", bot)
        chat = wrapper.resolve("username")
        assert type(chat) == Chat
        assert chat.id == 123
        assert chat.type == Chat.PRIVATE
        assert chat.username == "username"
        assert chat.first_name == "name"
        assert chat.last_name == "last_name"
        assert chat.bio == "A description."

    def test_normal_run_channel(self, monkeypatch, bot):
        api_result = {
            "ok": True,
            "result": {
                "id": 123,
                "type": "channel",
                "username": "username",
                "title": "channel_name",
                "description": "A description.",
            },
        }

        response = urllib3.response.HTTPResponse(body=json.dumps(api_result).encode("UTF-8"))

        def mockreturn(*args, **kwargs):
            return response

        monkeypatch.setattr(urllib3.PoolManager, "request", mockreturn)
        wrapper = UsernameToChatAPI("URL", "key", bot)
        chat = wrapper.resolve("username")
        assert type(chat) == Chat
        assert chat.id == 123
        assert chat.type == Chat.CHANNEL
        assert chat.username == "username"
        assert chat.title == "channel_name"
        assert chat.description == "A description."

    def test_errors(self, monkeypatch, bot):
        api_result = {"ok": False, "error_code": 401, "description": "Unauthorized"}

        response = urllib3.response.HTTPResponse(body=json.dumps(api_result).encode("UTF-8"))

        def mockreturn(*args, **kwargs):
            return response

        monkeypatch.setattr(urllib3.PoolManager, "request", mockreturn)
        wrapper = UsernameToChatAPI("URL", "key", bot)
        with pytest.raises(error.Unauthorized):
            wrapper.resolve("username")

        api_result = {"ok": False, "error_code": 400, "description": "Bad Request: chat not found"}
        response = urllib3.response.HTTPResponse(body=json.dumps(api_result).encode("UTF-8"))

        def mockreturn(*args, **kwargs):
            return response

        monkeypatch.setattr(urllib3.PoolManager, "request", mockreturn)
        with pytest.raises(error.BadRequest):
            wrapper.resolve("username")

        api_result = {
            "ok": False,
            "error_code": 429,
            "description": "Bad Request: chat not found",
            "retry_after": 12,
        }
        response = urllib3.response.HTTPResponse(body=json.dumps(api_result).encode("UTF-8"))

        def mockreturn(*args, **kwargs):
            return response

        monkeypatch.setattr(urllib3.PoolManager, "request", mockreturn)
        try:
            wrapper.resolve("username")
        except error.RetryAfter as e:
            assert e.retry_after == 12

        api_result = {"ok": False, "error_code": 499, "description": "This cant happen"}
        response = urllib3.response.HTTPResponse(body=json.dumps(api_result).encode("UTF-8"))

        def mockreturn(*args, **kwargs):
            return response

        monkeypatch.setattr(urllib3.PoolManager, "request", mockreturn)
        with pytest.raises(error.TelegramError):
            wrapper.resolve("username")
