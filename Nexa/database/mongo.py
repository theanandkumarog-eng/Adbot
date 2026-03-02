# Nexa/database/mongo.py
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME
from typing import Optional, List, Dict

# -----------------------------
# MongoDB client
# -----------------------------
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]


# -----------------------------
# Auto Setup Indexes
# -----------------------------
async def ensure_indexes():
    """
    Ensures necessary indexes exist for collections.
    - users: unique on user_id
    - ads: unique on ad_id
    """
    try:
        # Users collection
        user_indexes = await db.users.index_information()
        if "user_id_1" not in user_indexes:
            await db.users.create_index("user_id", unique=True)
            print("✅ Created unique index on users.user_id")

        # Ads collection
        ad_indexes = await db.ads.index_information()
        if "ad_id_1" not in ad_indexes:
            await db.ads.create_index("ad_id", unique=True)
            print("✅ Created unique index on ads.ad_id")

    except Exception as e:
        print(f"[DB WARNING] Index setup skipped: {type(e).__name__}: {e}")


# -----------------------------
# Check Connection
# -----------------------------
async def check_connection() -> bool:
    try:
        await client.admin.command("ping")
        print("✅ MongoDB Connected Successfully")
        return True
    except Exception as e:
        print(f"[DB ERROR] Connection failed: {type(e).__name__}: {e}")
        return False


# -----------------------------
# Users CRUD
# -----------------------------
async def add_user(user_id: int, username: str, data: Optional[dict] = None):
    """
    Insert a new user or update if exists
    """
    data = data or {}
    try:
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"username": username, **data}},
            upsert=True
        )
    except Exception as e:
        print(f"[DB ERROR] Failed to add/update user {user_id}: {e}")


async def get_user(user_id: int) -> Optional[Dict]:
    return await db.users.find_one({"user_id": user_id})


async def delete_user(user_id: int) -> bool:
    result = await db.users.delete_one({"user_id": user_id})
    return result.deleted_count > 0


async def get_all_users() -> List[Dict]:
    cursor = db.users.find({})
    return await cursor.to_list(length=None)


# -----------------------------
# Ads CRUD
# -----------------------------
async def add_ad(ad_id: str, content: str, metadata: Optional[dict] = None):
    metadata = metadata or {}
    try:
        await db.ads.update_one(
            {"ad_id": ad_id},
            {"$set": {"content": content, **metadata}},
            upsert=True
        )
    except Exception as e:
        print(f"[DB ERROR] Failed to add/update ad {ad_id}: {e}")


async def get_ad(ad_id: str) -> Optional[Dict]:
    return await db.ads.find_one({"ad_id": ad_id})


async def get_all_ads() -> List[Dict]:
    cursor = db.ads.find({})
    return await cursor.to_list(length=None)


async def delete_ad(ad_id: str) -> bool:
    result = await db.ads.delete_one({"ad_id": ad_id})
    return result.deleted_count > 0


# -----------------------------
# Logs (Optional)
# -----------------------------
async def log_event(event_type: str, message: str, extra: Optional[dict] = None):
    """
    Stores bot logs for debugging or analytics
    """
    extra = extra or {}
    await db.logs.insert_one({
        "event_type": event_type,
        "message": message,
        "extra": extra,
        "timestamp": client.server_info()["localTime"]
    })


# -----------------------------
# Initialize DB (call at startup)
# -----------------------------
async def init_db():
    connected = await check_connection()
    if not connected:
        raise ConnectionError("Cannot connect to MongoDB")
    await ensure_indexes()