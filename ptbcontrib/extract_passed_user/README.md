# Extract passed user

This module intended for a single function:   
Extract side user from the message provided by current user.
i.e. 1 user passes data of third-party user.

Currently, the function will check:
1. `Message.users_shared`
2. `Message.contact`
3. `Message.text` with numbers (if user id typed manually)
4. `Message.text` with @name (if user @name typed manually)

## Usage:

### 1. By the users_shared:
Note: `users_shared` object is tuple and may contain many users but only first of them will be returned. 
```python
Message=(..., users_shared)
shared_user = extract_passed_user(message=message)  # Just the first user in the users_shared tuple 
```

### 2. By the contact:  
Note: PTB `Contact.user_id` field is optional but required for the extraction or `None` otherwise will be returned. 
```python
Message=(..., contact=Contact(...))
shared_user = extract_passed_user(message=message) 
```

### 3. By the text id:   
Note: Only first found number in the text will be used as `user_id`.
```python
Message=(..., text='Here my fried id - 123456, only numbers will be extracted.')
shared_user = extract_passed_user(message=message) 
```

### 4. By the text @name:  
Note: telegram bot API has no method to convert `@name` into `user_id`, 
so ptbcontrlib module `username_to_chat_api` will be user for this.
`username_resolver` parameter required for this, 
it should be `UsernameToChatAPI` instance or custom async function.  
Only first found world with `@` prefix in the text will be used as future `user_id`.
```python
Message=(..., text='@friend_nickname')
shared_user = extract_passed_user(message=message, username_resolver=UsernameToChatAPI(..., )) 
```

### `get_num_from_text` function:
helper function which extracts first found number from the string as said in the docs above

## Requirements

*   `python-telegram-bot>=21.1`

## Authors

*   [david Shiko](https://github.com/david-shiko)
