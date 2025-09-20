from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import structlog
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from pymongo import MongoClient

from app.core.config import settings

if TYPE_CHECKING:
    import gridfs

logger = structlog.get_logger()


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database = None
    gridfs_bucket: Optional[AsyncIOMotorGridFSBucket] = None


class MongoDBSync:
    client: Optional[MongoClient] = None
    database = None
    gridfs: Optional[gridfs.GridFS] = None


mongodb = MongoDB()
mongodb_sync = MongoDBSync()


async def connect_to_mongo():
    mongodb.client = AsyncIOMotorClient(settings.MONGO_URI)
    mongodb.database = mongodb.client[settings.MONGO_DB]
    mongodb.gridfs_bucket = AsyncIOMotorGridFSBucket(mongodb.database)
    
    await mongodb.client.admin.command('ping')
    logger.info("Connected to MongoDB", database=settings.MONGO_DB)


async def close_mongo_connection():
    if mongodb.client:
        mongodb.client.close()
        logger.info("Disconnected from MongoDB")


def connect_to_mongo_sync():
    import gridfs
    
    mongodb_sync.client = MongoClient(settings.MONGO_URI)
    mongodb_sync.database = mongodb_sync.client[settings.MONGO_DB]
    mongodb_sync.gridfs = gridfs.GridFS(mongodb_sync.database)
    
    mongodb_sync.client.admin.command('ping')
    logger.info("Connected to MongoDB (sync)", database=settings.MONGO_DB)


def close_mongo_connection_sync():
    if mongodb_sync.client:
        mongodb_sync.client.close()
        logger.info("Disconnected from MongoDB (sync)")


async def get_gridfs_bucket() -> AsyncIOMotorGridFSBucket:
    return mongodb.gridfs_bucket


def get_gridfs_sync():
    import gridfs
    return mongodb_sync.gridfs


async def get_mongo_database():
    return mongodb.database


def get_mongo_database_sync():
    return mongodb_sync.database
