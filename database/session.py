from sqlalchemy.ext.asyncio import async_sessionmaker,create_async_engine

from config import DB_URL
from database.models import Base

engine=create_async_engine(DB_URL,echo=False)
async_session=async_sessionmaker(engine,expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)