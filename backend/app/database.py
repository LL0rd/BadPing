import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from typing import AsyncGenerator

from .config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    pool_recycle=300,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    from .models import Device, PingResult, Notification  # noqa: F401

    async with engine.begin() as conn:
        # Try WAL mode, fall back to DELETE if filesystem doesn't support it (e.g. FUSE/NFS)
        try:
            result = await conn.execute(text("PRAGMA journal_mode=WAL"))
            mode = result.scalar()
            if mode and mode.lower() == "wal":
                logger.info("SQLite journal mode: WAL")
            else:
                logger.warning("WAL mode not supported (got: %s), using default journal mode", mode)
        except Exception as e:
            logger.warning("Failed to set WAL mode: %s, using default journal mode", e)

        await conn.execute(text("PRAGMA synchronous=NORMAL"))
        await conn.execute(text("PRAGMA cache_size=-64000"))
        await conn.execute(text("PRAGMA busy_timeout=5000"))
        await conn.run_sync(Base.metadata.create_all)

        # Migrate existing databases: add columns that may not exist yet
        migrations = [
            "ALTER TABLE devices ADD COLUMN fingerprint_enabled BOOLEAN NOT NULL DEFAULT 0",
        ]
        for sql in migrations:
            try:
                await conn.execute(text(sql))
                logger.info("Migration applied: %s", sql)
            except Exception:
                pass  # Column already exists


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
