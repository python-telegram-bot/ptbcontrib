# `BotCommand` class with a second, longer description

Provides a `LongBotCommand` class that allows you to store a second, longer description (>256 characters) for a `BotCommand` to be stored alongside a shorter description.
Example:

```python
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from ptbcontrib.longbotcommand import LongBotCommand

details_text = "This bot shows how to attach a longer help description to a command."
details_desc = (
    "Show the details of this example bot. The longer description appears in /help, while the "
    "short description is sent to Telegram's command menu."
)

BOT_COMMANDS = [
    LongBotCommand("help", "Prints out a list of available commands"),
    LongBotCommand(
        "details",
        "Show bot details",
        long_description=details_desc,
    ),
]


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    commands = await context.bot.get_my_commands()
    descriptions = {command.command: command.long_description for command in BOT_COMMANDS}
    await update.effective_message.reply_text(
        "\n\n".join(f"/{command.command}\n\n{descriptions[command.command]}" for command in commands)
    )


async def details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(details_text)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(BOT_COMMANDS)


application = Application.builder().token("TOKEN").post_init(post_init).build()
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("details", details))

application.run_polling()

```

## Requirements

*   `python-telegram-bot~=20.0`

## Authors

*   [bqback](https://github.com/bqback)
