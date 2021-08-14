# Persistence class with Postgresql database as backend

## How to use

```python
from ptbcontrib.postgres_persistence import PostgresPersistence


# Your Postgresql database URL
DB_URI = "postgresql://username:pw@hostname:port/db_name"

# And pass it in Updater
updater = Updater(..., persistence=PostgresPersistence(url=DB_URI))
```

## Requirements

*   `python-telegram-bot>=12.0`
*   `SQLAlchemy`
*   `ujson` (Optional)

## Authors

*   [Stɑrry Shivɑm](https://github.com/starry69)
