import csv
import io
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import Integer, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Device, PingResult
from ..schemas import GraphPoint, GraphResponse, StatsResponse

router = APIRouter(tags=["stats"])


@router.get("/stats/{device_id}", response_model=StatsResponse)
async def get_stats(device_id: int, session: AsyncSession = Depends(get_session)):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    now = time.time()

    async def calc(seconds: int):
        cutoff = now - seconds
        result = await session.execute(
            select(
                func.count().label("total"),
                func.sum(PingResult.packet_lost.cast(Integer)).label("lost"),
                func.avg(PingResult.latency_ms).label("avg"),
                func.min(PingResult.latency_ms).label("min"),
                func.max(PingResult.latency_ms).label("max"),
            ).where(
                PingResult.device_id == device_id,
                PingResult.timestamp >= cutoff,
            )
        )
        return result.one()

    r6 = await calc(21600)
    r12 = await calc(43200)
    r24 = await calc(86400)
    r48 = await calc(172800)

    def pct(row):
        total = row.total or 0
        lost = row.lost or 0
        return round(lost / total * 100, 2) if total > 0 else 0.0

    return StatsResponse(
        device_id=device_id,
        stats_6h=pct(r6),
        stats_12h=pct(r12),
        stats_24h=pct(r24),
        stats_48h=pct(r48),
        total_pings_24h=r24.total or 0,
        lost_pings_24h=r24.lost or 0,
        avg_latency_24h=round(r24.avg, 3) if r24.avg else None,
        min_latency_24h=round(r24.min, 3) if r24.min else None,
        max_latency_24h=round(r24.max, 3) if r24.max else None,
    )


@router.get("/stats/{device_id}/graph", response_model=GraphResponse)
async def get_graph_data(
    device_id: int,
    start: float | None = Query(None),
    end: float | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    now = time.time()
    if end is None:
        end = now
    if start is None:
        start = end - 3600

    time_range = end - start

    if time_range > 86400:
        bucket = 60.0
    elif time_range > 21600:
        bucket = 10.0
    elif time_range > 3600:
        bucket = 1.0
    else:
        bucket = 0.0

    if bucket > 0:
        bucket_col = (PingResult.timestamp / bucket).cast(Integer)
        result = await session.execute(
            select(
                (bucket_col * bucket).label("bucket_ts"),
                func.avg(PingResult.latency_ms).label("avg_latency"),
                func.max(PingResult.packet_lost.cast(Integer)).label("any_lost"),
                PingResult.ping_type,
            )
            .where(
                PingResult.device_id == device_id,
                PingResult.timestamp >= start,
                PingResult.timestamp <= end,
            )
            .group_by(bucket_col, PingResult.ping_type)
            .order_by(bucket_col)
        )
        rows = result.all()
        points = [
            GraphPoint(
                timestamp=row.bucket_ts,
                latency_ms=round(row.avg_latency, 3) if row.avg_latency else None,
                packet_lost=bool(row.any_lost),
                ping_type=row.ping_type,
            )
            for row in rows
        ]
        resolution = bucket
    else:
        result = await session.execute(
            select(PingResult)
            .where(
                PingResult.device_id == device_id,
                PingResult.timestamp >= start,
                PingResult.timestamp <= end,
            )
            .order_by(PingResult.timestamp)
            .limit(10000)
        )
        rows = result.scalars().all()
        points = [
            GraphPoint(
                timestamp=r.timestamp,
                latency_ms=r.latency_ms,
                packet_lost=r.packet_lost,
                ping_type=r.ping_type,
            )
            for r in rows
        ]
        resolution = device.interval_seconds

    return GraphResponse(
        device_id=device_id,
        points=points,
        resolution_seconds=resolution,
    )


@router.delete("/stats/{device_id}/data")
async def clear_data(device_id: int, session: AsyncSession = Depends(get_session)):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    result = await session.execute(
        delete(PingResult).where(PingResult.device_id == device_id)
    )
    await session.commit()
    return {"ok": True, "deleted": result.rowcount}


@router.get("/stats/{device_id}/export")
async def export_csv(
    device_id: int,
    start: float | None = Query(None),
    end: float | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    now = time.time()
    if end is None:
        end = now
    if start is None:
        start = end - 86400

    result = await session.execute(
        select(PingResult)
        .where(
            PingResult.device_id == device_id,
            PingResult.timestamp >= start,
            PingResult.timestamp <= end,
        )
        .order_by(PingResult.timestamp)
    )
    rows = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "ping_type", "latency_ms", "packet_lost"])
    for r in rows:
        writer.writerow([r.timestamp, r.ping_type, r.latency_ms, int(r.packet_lost)])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="badping_{device.name}_{device_id}.csv"'
        },
    )
