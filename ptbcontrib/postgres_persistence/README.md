# Persistence class with Postgresql database as backend.

* How to use:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from ptbcontrib.postgres_persistence import PostgresPersistence


# Your Postgresql database URL
DB_URI = "postgresql://username:pw@hostname:port/db_name"

# SQLAlchemy session maker
def start_session() -> scoped_session:
    engine = create_engine(DB_URI, client_encoding="utf8")
    return scoped_session(sessionmaker(bind=engine, autoflush=False))

# start the session
session = start_session()

# And pass it in Updater...
updater = Updater(...., persistence=PostgresPersistence(session))
```

## Requirements

*   `python-telegram-bot>=12.0`
*   `SQLAlchemy`
*   `ujson`

## Authors

*   [Stɑrry Shivɑm](https://github.com/starry69)
