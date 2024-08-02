from telegram.constants import ParseMode
from ptbcontrib.log_forwarder import LogForwarder
from unittest.mock import MagicMock
import logging


async def test_log_forwarder():
    root_logger = logging.getLogger()
    chat_ids = [69420]
    bot = MagicMock()
    log_forwarder = LogForwarder(bot, chat_ids)
    root_logger.addHandler(log_forwarder)

    logger = logging.getLogger("test_logger")
    logger.error("TEST")

    bot.send_message.assert_called_with(
        chat_id=69420, text="```\nTEST\n```", parse_mode=ParseMode.MARKDOWN_V2
    )
