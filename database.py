from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base

# Sync for startup (create tables)
SYNC_DB_URL = "postgresql://gateway_user:gateway_pass@localhost:5432/gateway_db"
engine = create_engine(SYNC_DB_URL)

# Async for runtime
ASYNC_DB_URL = "postgresql+asyncpg://gateway_user:gateway_pass@localhost:5432/gateway_db"
async_engine = create_async_engine(ASYNC_DB_URL, echo=False)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(engine)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
