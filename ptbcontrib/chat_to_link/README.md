# Get Joinable Link from Chat

Provides a method to get a joinable link from a `telegram.Chat` object. To do so, it tries
to get a link in the following order:
1. Chat's username (`chat.username`).
2. Chat's invite link (`chat.invite_link`).
3. Chat's invite link from bot (`bot.get_chat.invite_link`)
4. Create invite link if `member_limit` or `expire_date` is passed
   (`bot.create_chat_invite_link`).
5. Otherwise export primary invite link (`bot.export_chat_invite_link`).
6. Empty string since there is no valid link and the bot doesn't have permission
   to create one either.

Please see the docstrings for more details.

## Requirements

*   `python-telegram-bot>=13.4`

## Authors

*   [Allerter](https://github.com/allerter)
