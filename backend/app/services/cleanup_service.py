import asyncio
import logging
import time

from sqlalchemy import delete, select

from ..config import settings
from ..database import async_session
from ..models import Device, PingResult

logger = logging.getLogger(__name__)


class CleanupService:
    def __init__(self):
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._cleanup_loop())
        logger.info("Cleanup service started")

    def stop(self) -> None:
        if self._task:
            self._task.cancel()

    async def _cleanup_loop(self) -> None:
        while True:
            try:
                await self._run_cleanup()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Cleanup error")
            await asyncio.sleep(settings.cleanup_interval)

    async def _run_cleanup(self) -> None:
        async with async_session() as session:
            devices = (await session.execute(select(Device))).scalars().all()
            for device in devices:
                cutoff = time.time() - (device.retention_days * 86400)
                stmt = delete(PingResult).where(
                    PingResult.device_id == device.id,
                    PingResult.timestamp < cutoff,
                )
                result = await session.execute(stmt)
                if result.rowcount > 0:
                    logger.info(
                        "Cleaned %d old ping results for device %s",
                        result.rowcount,
                        device.name,
                    )
            await session.commit()
