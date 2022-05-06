# Persistence class with PostgreSQL database as backend

## Notes
Data must needs to be JSON serialisable since `PostgresPersistence` is a
subclass of PTB's `DictPersistence` which encodes and saves data in JSON format.

## How to use

**Using with postgreSQL database URL**

```python
from ptbcontrib.postgres_persistence import PostgresPersistence


# Your Postgresql database URL
DB_URI = "postgresql://username:pw@hostname:port/db_name"

updater = Updater(..., persistence=PostgresPersistence(url=DB_URI))
```

**Using with existing SQLAlchemy scoped session**
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

updater = Updater(..., persistence=PostgresPersistence(session=start_session()))
```


## Requirements

*   `20>python-telegram-bot>=12.0`
*   `SQLAlchemy`
*   `ujson` (Optional)

## Authors

*   [Stɑrry Shivɑm](https://github.com/starry69)

