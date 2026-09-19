# `BotCommand` class with a second, longer description

Provides a `LongBotCommand` class that allows you to store a second, longer description (>256 characters) for a `BotCommand` to be stored alongside a shorter description.
Example:

```python
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from ptbcontrib.longbotcommand import LongBotCommand

lorem_text = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor "
    "incididunt ut labore et dolore magna aliqua."
)

lorem_desc = (
    "Lorem Ipsum is simply dummy text of the printing and typesetting industry. "
    "Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an "
    "unknown printer took a galley of type and scrambled it to make a type specimen book. "
    "It has survived not only five centuries, but also the leap into electronic typesetting, "
    "remaining essentially unchanged."
)

BOT_COMMANDS = [
    LongBotCommand("help", "Prints out a list of available commands"),
    LongBotCommand(
        "lorem",
        "Prints Lorem Ipsum",
        long_description=lorem_desc,
    ),
]

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    for command in BOT_COMMANDS:
        await update.effective_message.reply_text(
            f"/{command.command}\n\n{command.long_description}"
        )

async def lorem_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(lorem_text)

async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(BOT_COMMANDS)

application = Application.builder().token("TOKEN").post_init(post_init).build()
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("lorem", lorem_command))
application.run_polling()

```

## Requirements

*   `python-telegram-bot>=20.0`

## Authors

*   [bqback](https://github.com/bqback)
