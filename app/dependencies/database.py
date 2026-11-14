from typing import Annotated

from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import app.models.booking
import app.models.room
import app.models.user

# 1. db url: for engine to know which db it should communicate with
sqlite_fine_name = "database.db"
sqlite_url = f"sqlite+aiosqlite:///{sqlite_fine_name}"

# 2. Create engine
engine = create_async_engine(sqlite_url, echo=True)


@event.listens_for(engine.sync_engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    dbapi_connection.execute("PRAGMA foreign_keys=ON")


# 3. Create db tables
async def create_db_and_tables():
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


# 4. Create reusable session dependency
async def get_session():
    async with AsyncSession(engine) as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
