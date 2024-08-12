# Logging handler for python-telegram-bot
Extension to forward application logs to specific Telegram chats through a `logging.Handler` class.

## Usage
Initialize the log forwarder in a method that runs in the `post_init` hook of `Application`:

```python
async def on_startup(app: Application):
    error_forwarder = LogForwarder(
        app.bot, [CHAT_ID], log_levels=["ERROR", "WARNING"]
    )
    # Add handler to the root logger to apply to all other loggers
    logging.getLogger().addHandler(error_forwarder)

application: Application = (
    ApplicationBuilder()
    .token("BOT_TOKEN")
    .post_init(on_startup)
    .build()
)
```
