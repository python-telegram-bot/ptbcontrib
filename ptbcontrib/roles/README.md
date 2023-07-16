# Dynamic User Access Management

Provides classes and methods for granular, hierarchical user access management. Example:

```python
from telegram import Update
from telegram.ext import TypeHandler, ApplicationBuilder, MessageHandler, SomeHandler, filters
from ptbcontrib.roles import setup_roles, RolesHandler, Role


async def add_to_my_role_2(update, context):
    user = update.effective_user
    # 'roles' is stored in context.bot_data[BOT_DATA_KEY]
    context.roles['my_role_2'].add_member(user.id)
    
async def add_to_my_role_1(update, context):
    user_id = int(update.message.text)
    context.roles['my_role_1'].add_member(user_id)
    

async def post_init(application):
    # This is called after the application has been initialized
    # and before the polling starts.
    # This ensures that the roles are initialized *after* the
    # persistence has been loaded, if persistence is used.
    # See also the wiki page at
    # https://github.com/python-telegram-bot/python-telegram-bot/wiki/Making-your-bot-persistent
    roles = setup_roles(application)

    if 'my_role_1' not in roles:
        roles.add_role(name='my_role_1')
    my_role_1 = roles['my_role_1']
    
    if 'my_role_2' not in roles:
        roles.add_role(name='my_role_2')
    
    roles.add_admin(123)
    my_role_2 = roles['my_role_2']
    my_role_1.add_child_role(my_role_2)

    # Anyone can add themself to my_role_2
    application.add_handler(RolesHandler(TypeHandler(Update, add_to_my_role_2), roles=None))
    
    # Only the admin can add users to my_role_1
    application.add_handler(
        RolesHandler(MessageHandler(filters.TEXT, add_to_my_role_1), roles=roles.admins)
    )
    
    # This will be accessible by my_role_2, my_role_1 and the admin
    application.add_handler(RolesHandler(SomeHandler(...), roles=my_role_2))
    
    # This will be accessible by my_role_1 and the admin
    application.add_handler(RolesHandler(SomeHandler(...), roles=my_role_1))
    
    # This will be accessible by anyone except my_role_1 and my_role_2
    application.add_handler(RolesHandler(SomeHandler(...), roles=~my_role_1))

    # You can compare the roles regarding hierarchy:
    roles['my_role_1'] >= roles['my_role_2']  # True
    roles['my_role_1'] < roles['my_role_2']  # False
    roles.admins >= Role(...)  # False, since neither of those is a parent of the other

application = ApplicationBuilder().token('TOKEN').post_init(post_init).build()
```

Please see the docstrings for more details.

## Note on `ConversationHandler`

Unfortunately `RolesHandler(my_conversation_handler, roles=roles)` does *not* work. However, checking the roles for every step of the conversation is rather inefficient anyway. Instead, by applying `RolesHandler` to the `entry_points` of the `ConversationHandler`, the conversation can only be started by the selected roles and re-checking the roles within the conversation is not necessary.

## Requirements

*   `python-telegram-bot~=20.0`

## Authors

*   [Hinrich Mahler](https://github.com/bibo-joshi)
*   [GrandMoffPinky](https://github.com/grandmoffpinky)
