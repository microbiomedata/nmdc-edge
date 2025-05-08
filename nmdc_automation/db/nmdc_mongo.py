import os
from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase


@lru_cache
def get_db() -> MongoDatabase:
    _client = MongoClient(
        host=os.getenv("MONGO_HOST", "localhost"),
        port=int(os.getenv("MONGO_PORT", "27018")),
        username=os.getenv("MONGO_USERNAME", None),
        password=os.getenv("MONGO_PASSWORD", None),
        directConnection=True,
    )[os.getenv("MONGO_DBNAME", "nmdc")]
    return _client
