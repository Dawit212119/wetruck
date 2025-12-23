from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Use the provided DATABASE_URL from spec
# Convert postgresql:// to postgresql+asyncpg:// for async operations
# Note: Remove sslmode from URL as asyncpg doesn't support it as a query parameter
DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_SPoQi2u9lcLJ@ep-snowy-dust-a44okve2-pooler.us-east-1.aws.neon.tech/neondb"

# Create async engine with SSL configuration for asyncpg
# asyncpg requires SSL to be passed as 'ssl' parameter, not 'sslmode'
# For Neon database, SSL is required, so we set ssl=True
async_engine = create_async_engine(
    DATABASE_URL,
    connect_args={
        "ssl": True  # asyncpg uses 'ssl=True' for SSL-required connections (Neon requires SSL)
    },
    echo=False,
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db():
    """
    Dependency function to get async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
