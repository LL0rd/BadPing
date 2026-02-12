import asyncio
import logging
import time
from collections import defaultdict

from sqlalchemy import select

from ..config import settings
from ..database import async_session
from ..models import Device, PingResult
from .arp_service import arp_ping
from .notification_service import notify_device_down, notify_device_recovered, notify_high_packet_loss
from .ping_service import icmp_ping

logger = logging.getLogger(__name__)


class MonitorService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._tasks: dict[int, asyncio.Task] = {}
        self._write_buffer: list[dict] = []
        self._buffer_lock = asyncio.Lock()
        self._flush_task: asyncio.Task | None = None
        self._consecutive_success: dict[int, int] = defaultdict(int)
        self._consecutive_fail: dict[int, int] = defaultdict(int)

    async def start(self) -> None:
        self._flush_task = asyncio.create_task(self._flush_loop())
        async with async_session() as session:
            result = await session.execute(
                select(Device).where(Device.monitoring_enabled == True)  # noqa: E712
            )
            devices = result.scalars().all()
            for device in devices:
                self.start_device(device.id)
        logger.info("Monitor service started, %d devices active", len(self._tasks))

    async def stop(self) -> None:
        if self._flush_task:
            self._flush_task.cancel()
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()
        await self._flush_buffer()

    def start_device(self, device_id: int) -> None:
        if device_id in self._tasks:
            return
        self._tasks[device_id] = asyncio.create_task(self._monitor_device(device_id))
        logger.info("Started monitoring device %d", device_id)

    async def stop_device(self, device_id: int) -> None:
        task = self._tasks.pop(device_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._consecutive_success.pop(device_id, None)
        self._consecutive_fail.pop(device_id, None)
        logger.info("Stopped monitoring device %d", device_id)

    def is_monitoring(self, device_id: int) -> bool:
        return device_id in self._tasks

    async def restart_device(self, device_id: int) -> None:
        await self.stop_device(device_id)
        self.start_device(device_id)

    async def _monitor_device(self, device_id: int) -> None:
        try:
            while True:
                async with async_session() as session:
                    device = await session.get(Device, device_id)
                    if not device or not device.monitoring_enabled:
                        break

                    interval = device.interval_seconds
                    ping_type = device.ping_type
                    ip = device.ip_address
                    packet_size = device.packet_size

                results = []

                if ping_type in ("icmp", "both") and ip:
                    result = await icmp_ping(ip, packet_size)
                    result["device_id"] = device_id
                    results.append(result)

                if ping_type in ("arp", "both") and ip:
                    result = await arp_ping(ip)
                    if result is not None:
                        result["device_id"] = device_id
                        results.append(result)

                async with self._buffer_lock:
                    self._write_buffer.extend(results)

                await self._update_status(device_id, results)
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Monitor error for device %d", device_id)

    async def _update_status(self, device_id: int, results: list[dict]) -> None:
        if not results:
            return

        any_success = any(not r["packet_lost"] for r in results)

        if any_success:
            self._consecutive_success[device_id] += 1
            self._consecutive_fail[device_id] = 0
        else:
            self._consecutive_fail[device_id] += 1
            self._consecutive_success[device_id] = 0

        async with async_session() as session:
            device = await session.get(Device, device_id)
            if not device:
                return

            old_status = device.status
            new_status = old_status

            if any_success:
                device.last_seen_at = time.time()

            if old_status == "unknown" and any_success:
                new_status = "online"
            elif old_status == "offline" and self._consecutive_success[device_id] >= settings.recovery_count:
                new_status = "online"
            elif old_status in ("online", "degraded") and not any_success:
                fail_duration = self._consecutive_fail[device_id] * device.interval_seconds
                if fail_duration >= settings.offline_loss_seconds:
                    new_status = "offline"
                elif old_status == "online":
                    new_status = "degraded"
            elif old_status == "unknown" and not any_success:
                fail_duration = self._consecutive_fail[device_id] * device.interval_seconds
                if fail_duration >= settings.offline_loss_seconds:
                    new_status = "offline"

            if new_status != old_status:
                device.status = new_status

                if new_status == "offline":
                    await notify_device_down(device)
                elif new_status == "online" and old_status == "offline":
                    await notify_device_recovered(device)
                elif new_status == "degraded":
                    total = self._consecutive_fail[device_id] + self._consecutive_success[device_id]
                    loss_pct = self._consecutive_fail[device_id] / max(1, total) * 100
                    await notify_high_packet_loss(device, loss_pct)

            await session.commit()

    async def _flush_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(settings.batch_write_interval)
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Flush error")

    async def _flush_buffer(self) -> None:
        async with self._buffer_lock:
            if not self._write_buffer:
                return
            batch = self._write_buffer.copy()
            self._write_buffer.clear()

        async with async_session() as session:
            for item in batch:
                session.add(PingResult(
                    device_id=item["device_id"],
                    timestamp=item["timestamp"],
                    ping_type=item["ping_type"],
                    latency_ms=item.get("latency_ms"),
                    packet_lost=item["packet_lost"],
                ))
            await session.commit()
