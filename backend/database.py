from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .config import settings


def _make_async_url(url: str) -> str:
    """
    Convert a Supabase / standard postgres URL to asyncpg format.
    Supabase connection strings look like:
      postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
    We replace the scheme and append SSL mode required by Supabase.
    """
    url = url.replace("postgresql://", "postgresql+asyncpg://")
    url = url.replace("postgres://",   "postgresql+asyncpg://")
    return url


# Supabase pooler (port 6543) uses PgBouncer — disable prepared statements
_is_supabase = "supabase.com" in settings.DATABASE_URL

engine = create_async_engine(
    _make_async_url(settings.DATABASE_URL),
    echo=settings.APP_ENV == "development",
    pool_size=5,
    max_overflow=10,
    connect_args={
        "ssl": "require",
        "statement_cache_size": 0,  # required for PgBouncer / Supabase pooler
    } if _is_supabase else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
