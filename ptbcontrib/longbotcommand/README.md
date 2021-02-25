# `BotCommand` class with a second, longer description

Provides a `LongBotCommand` class that allows you to store a second, longer description (>256 characters) for a `BotCommand` to be stored alongside a shorter description.
Example:

```python
from typing import List

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from ptbcontrib.longbotcommand import LongBotCommand

updater = Updater("TOKEN", use_context=True)
dp = updater.dispatcher

lorem_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor "
				"incididunt ut labore et dolore magna aliqua."

lorem_desc = "Lorem Ipsum is simply dummy text of the printing and typesetting industry. "
		"Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an "
		"unknown printer took a galley of type and scrambled it to make a type specimen book. "
		"It has survived not only five centuries, but also the leap into electronic typesetting, "
		"remaining essentially unchanged."

BOT_COMMANDS: List[LongBotCommand] = [
    LongBotCommand("help", "Prints out a list of available commands"),
    LongBotCommand(
        "lorem",
        "Prints Lorem Ipsum",
        long_description = lorem_desc,
    ),
]

def help(update: Update, context: CallbackContext) -> None:
    for command in context.bot.commands:
        # This will only work if you already used set_my_commands!
        update.message.reply_text(f"/{command.command}\n\n{command.long_description}")

def lorem(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(lorem_text)


dp.add_handler(CommandHandler("help", help))
dp.add_handler(CommandHandler("lorem", lorem))

dp.bot.set_my_commands(BOT_COMMANDS)

updater.start_polling()

updater.idle()

```

## Requirements

*   `python-telegram-bot>=13.0`

## Authors

*   [bqback](https://github.com/bqback)
