from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Device, Notification
from ..schemas import NotificationList, NotificationResponse

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=NotificationList)
async def list_notifications(
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Notification, Device.name)
        .join(Device, Notification.device_id == Device.id)
        .order_by(Notification.is_read, Notification.created_at.desc())
        .limit(limit)
    )
    rows = result.all()

    notifications = []
    for notif, device_name in rows:
        resp = NotificationResponse.model_validate(notif)
        resp.device_name = device_name
        notifications.append(resp)

    unread_result = await session.execute(
        select(func.count()).where(Notification.is_read == False)  # noqa: E712
    )
    unread_count = unread_result.scalar() or 0

    return NotificationList(notifications=notifications, unread_count=unread_count)


@router.put("/notifications/{notification_id}/read")
async def mark_read(notification_id: int, session: AsyncSession = Depends(get_session)):
    notif = await session.get(Notification, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    await session.commit()
    return {"ok": True}


@router.put("/notifications/read-all")
async def mark_all_read(session: AsyncSession = Depends(get_session)):
    await session.execute(
        update(Notification).where(Notification.is_read == False).values(is_read=True)  # noqa: E712
    )
    await session.commit()
    return {"ok": True}
