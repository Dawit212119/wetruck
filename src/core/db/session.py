from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.core.settings.settings import settings
# "sqlalchemy.url = postgresql+psycopg2://username:password@localhost:5432/database_name
# "
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.db_username}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
#SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Or your actual database URL


engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        db.flush()
        raise e
    finally:
        db.close()

get_db_session =next(get_db())


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