# Store a second, longer description

Provides a class `ExtBotCommand` that allows you to store a second, longer description (>256 characters) for a `BotCommand` to be stored alongside a shorter description.
Example:

```python
from typing import List

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from ptbcontrib.long_command_description import ExtBotCommand

updater = Updater("1356182511:AAElUhAsCJKngpDEIeh34hyiEyiPRKGwbgg", use_context=True)
dp = updater.dispatcher

BOT_COMMANDS: List[ExtBotCommand] = [
    ExtBotCommand("start", "Starts the bot"),
    ExtBotCommand("help", "Prints out a list of available commands"),
    ExtBotCommand(
        "get_infinite_money",
        "Instantly gives you an infinite amount of money!",
        "Getting an infinite amount of money is actually super easy and only requires minimal investment\n"
        "To be exact, you need to be able to afford at least one piece of a common household appliance\n"
        "Here's how it's done:\n\n"
        "Step 0: Time is money, right?\n"
        "Step 1: Buy clocks\n"
        "Step 2 (optional): Cover yourself in oil\n"
        "Step 3: Use money from time to buy more clocks\n"
        "Step 4: INFINITE MONEY!!",
    ),
]


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Hi! Use /help to find out what I can do!")


def help(update: Update, context: CallbackContext) -> None:
    for command in context.bot.commands:
        update.message.reply_text(f"/{command.command}\n\n{command.long_description}")


def get_infinite_money(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("KA-CHING!")


dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("help", help))
dp.add_handler(CommandHandler("get_infinite_money", get_infinite_money))

dp.bot.set_my_commands(BOT_COMMANDS)

updater.start_polling()

updater.idle()

```

## Requirements

*   `python-telegram-bot>=13.0`

## Authors

*   [Hinrich Mahler](https://github.com/bibo-joshi)
