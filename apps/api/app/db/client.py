from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

client: AsyncIOMotorClient | None = None


async def connect_db() -> AsyncIOMotorDatabase:
    global client
    client = AsyncIOMotorClient(settings.mongodb_url)
    return client[settings.mongodb_db_name]


async def close_db() -> None:
    global client
    if client:
        client.close()
        client = None


def get_db() -> AsyncIOMotorDatabase:
    if client is None:
        raise RuntimeError("Database not connected")
    return client[settings.mongodb_db_name]
