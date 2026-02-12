import asyncio
import json
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session, get_session
from ..models import Device, PingResult
from ..schemas import (
    CheckResult,
    DeviceCheck,
    DeviceCreate,
    DeviceResponse,
    DeviceUpdate,
    DeviceWithStats,
    DiscoverRequest,
    DiscoveredDevice,
)
from ..services.arp_service import discover_network, is_same_subnet, mac_vendor_lookup
from ..services.monitor_service import MonitorService
from ..services.nmap_service import basic_scan, nmap_scan
from ..services.ping_service import icmp_ping

router = APIRouter(tags=["devices"])


async def _calc_loss_pct(session: AsyncSession, device_id: int, seconds: int) -> float | None:
    cutoff = time.time() - seconds
    result = await session.execute(
        select(
            func.count().label("total"),
            func.sum(PingResult.packet_lost.cast(Integer)).label("lost"),
        ).where(
            PingResult.device_id == device_id,
            PingResult.timestamp >= cutoff,
        )
    )
    row = result.one()
    total = row.total or 0
    lost = row.lost or 0
    if total == 0:
        return None
    return round(lost / total * 100, 2)


@router.get("/devices", response_model=list[DeviceWithStats])
async def list_devices(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Device).order_by(Device.name))
    devices = result.scalars().all()

    out = []
    for device in devices:
        d = DeviceWithStats.model_validate(device)
        d.stats_6h = await _calc_loss_pct(session, device.id, 21600)
        d.stats_12h = await _calc_loss_pct(session, device.id, 43200)
        d.stats_24h = await _calc_loss_pct(session, device.id, 86400)
        d.stats_48h = await _calc_loss_pct(session, device.id, 172800)
        out.append(d)
    return out


@router.post("/devices", response_model=DeviceResponse)
async def create_device(
    data: DeviceCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    device = Device(**data.model_dump())
    session.add(device)
    await session.commit()
    await session.refresh(device)

    if device.ip_address:
        asyncio.create_task(_run_nmap_for_device(device.id, device.ip_address, device.fingerprint_enabled))

    if device.monitoring_enabled:
        monitor: MonitorService = request.app.state.monitor_service
        monitor.start_device(device.id)

    return DeviceResponse.model_validate(device)


async def _run_nmap_for_device(device_id: int, ip_address: str, fingerprint_enabled: bool = False) -> None:
    if fingerprint_enabled:
        result = await nmap_scan(ip_address)
    else:
        result = await basic_scan(ip_address)
    async with async_session() as session:
        device = await session.get(Device, device_id)
        if device:
            if result.get("mac_address") and not device.mac_address:
                device.mac_address = result["mac_address"]
            if result.get("manufacturer"):
                device.manufacturer = result["manufacturer"]
            if result.get("os_info"):
                device.os_info = result["os_info"]
            if result.get("device_type"):
                device.device_type = result["device_type"]
            # Manufacturer fallback: if nmap returned "Unknown" or nothing, try scapy OUI lookup
            mac = result.get("mac_address") or device.mac_address
            if mac and (not device.manufacturer or device.manufacturer.lower() == "unknown"):
                vendor = mac_vendor_lookup(mac)
                if vendor:
                    device.manufacturer = vendor
            device.nmap_raw = json.dumps(result)
            await session.commit()


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: int, session: AsyncSession = Depends(get_session)):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceResponse.model_validate(device)


@router.put("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    data: DeviceUpdate,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(device, key, value)

    device.updated_at = time.time()
    await session.commit()
    await session.refresh(device)

    monitor: MonitorService = request.app.state.monitor_service
    if device.monitoring_enabled and not monitor.is_monitoring(device_id):
        monitor.start_device(device_id)
    elif not device.monitoring_enabled and monitor.is_monitoring(device_id):
        await monitor.stop_device(device_id)
    elif device.monitoring_enabled and monitor.is_monitoring(device_id):
        await monitor.restart_device(device_id)

    return DeviceResponse.model_validate(device)


@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    monitor: MonitorService = request.app.state.monitor_service
    await monitor.stop_device(device_id)

    await session.delete(device)
    await session.commit()
    return {"ok": True}


@router.post("/devices/{device_id}/toggle", response_model=DeviceResponse)
async def toggle_monitoring(
    device_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.monitoring_enabled = not device.monitoring_enabled
    device.updated_at = time.time()
    await session.commit()
    await session.refresh(device)

    monitor: MonitorService = request.app.state.monitor_service
    if device.monitoring_enabled:
        monitor.start_device(device_id)
    else:
        await monitor.stop_device(device_id)

    return DeviceResponse.model_validate(device)


@router.post("/devices/{device_id}/rescan")
async def rescan_device(device_id: int, session: AsyncSession = Depends(get_session)):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if not device.ip_address:
        raise HTTPException(status_code=400, detail="Device has no IP address")

    asyncio.create_task(_run_nmap_for_device(device.id, device.ip_address, fingerprint_enabled=True))
    return {"ok": True, "message": "Rescan started"}


@router.post("/devices/check", response_model=CheckResult)
async def check_device(data: DeviceCheck):
    if not data.ip_address and not data.mac_address:
        raise HTTPException(status_code=400, detail="IP or MAC address required")

    ip = data.ip_address
    if not ip:
        return CheckResult(
            reachable=False,
            mac_address=data.mac_address,
            message="Cannot ping by MAC only. Please provide an IP address.",
            same_subnet=True,
        )

    same_sub = is_same_subnet(ip)
    result = await icmp_ping(ip)

    return CheckResult(
        reachable=not result["packet_lost"],
        ip_address=ip,
        mac_address=data.mac_address,
        message="Device is reachable" if not result["packet_lost"] else "Device is not reachable via ICMP",
        same_subnet=same_sub,
    )


@router.post("/devices/discover", response_model=list[DiscoveredDevice])
async def discover_devices(data: DiscoverRequest = DiscoverRequest()):
    devices = await discover_network(data.subnet)
    return [DiscoveredDevice(**d) for d in devices]
