# Get joinable link from Chat

Provides a method to get a joinable link from a `telegram.Chat` object. To do so, it tries
to get a link in the following order:
1.  Chat's link (`chat.link`).

2.  Chat's invite link (`chat.invite_link`).

3.  Chat's invite link from bot (`bot.get_chat(chat.id).invite_link`).

4.  Export primary invite link (`bot.export_chat_invite_link`).

5.  `None` since there is no valid link and the bot doesn't have permission
   to create one either.

**Warning**: This function might make up to 2 API calls to get a valid chat link.

Please see the docstrings for more details.

## Requirements

*   `python-telegram-bot~=20.0`

## Authors

*   [Allerter](https://github.com/allerter)
