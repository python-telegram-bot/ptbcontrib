import asyncio
from collections.abc import Iterable
import logging
from telegram.constants import ParseMode

from telegram.ext import ExtBot


class LogForwarder(logging.Handler):
    def __init__(
        self,
        bot: ExtBot,
        chat_ids: Iterable[int],
        parse_mode: ParseMode = ParseMode.MARKDOWN_V2,
        log_levels: list[str] = ["WARN", "ERROR"],
    ):
        super().__init__()
        self._bot = bot
        self._chat_ids = chat_ids
        self._parse_mode = parse_mode
        self._log_levels = log_levels
        self._loop = asyncio.get_event_loop()

    def format_tg_msg(self, text: str) -> str:
        """
        Formats the log message to be sent to Telegram. Override this method to customize the message.
        The default implementation applies the handler's formatter and puts the result in a Markdown code block.
        """
        msg = "```\n" + text + "\n```"
        return msg

    def emit(self, record):
        try:
            formatted = self.format(record)
            msg = self.format_tg_msg(formatted)
            if record.levelname in self._log_levels:
                for chat_id in self._chat_ids:
                    f = self._bot.send_message(
                        chat_id=chat_id, text=msg, parse_mode=self._parse_mode
                    )
                    asyncio.run_coroutine_threadsafe(f, self._loop)
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)
