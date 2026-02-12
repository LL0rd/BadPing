from ..database import async_session
from ..models import Device, Notification


async def create_notification(device_id: int, notification_type: str, message: str) -> None:
    async with async_session() as session:
        notification = Notification(
            device_id=device_id,
            type=notification_type,
            message=message,
        )
        session.add(notification)
        await session.commit()


async def notify_device_down(device: Device) -> None:
    await create_notification(
        device.id,
        "device_down",
        f"{device.name} ({device.ip_address}) is offline",
    )


async def notify_high_packet_loss(device: Device, loss_pct: float) -> None:
    await create_notification(
        device.id,
        "high_packet_loss",
        f"{device.name} ({device.ip_address}) has {loss_pct:.1f}% packet loss",
    )


async def notify_device_recovered(device: Device) -> None:
    await create_notification(
        device.id,
        "device_recovered",
        f"{device.name} ({device.ip_address}) is back online",
    )
