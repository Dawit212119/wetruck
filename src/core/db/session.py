from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from src.core.settings.settings import settings



# Database URL

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{settings.db_username}:"
    f"{settings.db_password}@{settings.db_host}:"
    f"{settings.db_port}/{settings.db_name}"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  
)



# Session factory

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
)



# Base for ALL models

class Base(DeclarativeBase):
    pass

# FastAPI dependency: one DB session per request
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()



# Asynchronous Engine and Session
# async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
# AsyncSessionLocal = sessionmaker(
#     bind=async_engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
# )

# Dependency to get asynchronous DB session
# async def get_async_db():
#     async with AsyncSessionLocal() as db:
#         try:
#             yield db
#         finally:
#             await db.close()

# async_get_db_session =next(get_async_db())

"""
@app.get("/async-customers/")
async def get_customers(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Customer))
    customers = result.scalars().all()
    return customers

https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308
"""