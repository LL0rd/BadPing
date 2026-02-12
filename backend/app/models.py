import time

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String, nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String, nullable=True)
    os_info: Mapped[str | None] = mapped_column(String, nullable=True)
    device_type: Mapped[str | None] = mapped_column(String, nullable=True)
    nmap_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    fingerprint_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ping_type: Mapped[str] = mapped_column(String, nullable=False, default="icmp")
    interval_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    packet_size: Mapped[int] = mapped_column(Integer, nullable=False, default=64)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    monitoring_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="unknown")
    last_seen_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[float] = mapped_column(Float, nullable=False, default=time.time)
    updated_at: Mapped[float] = mapped_column(Float, nullable=False, default=time.time, onupdate=time.time)

    ping_results: Mapped[list["PingResult"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )


class PingResult(Base):
    __tablename__ = "ping_results"
    __table_args__ = (
        Index("idx_ping_results_device_time", "device_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[float] = mapped_column(Float, nullable=False, default=time.time)
    ping_type: Mapped[str] = mapped_column(String, nullable=False)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    packet_lost: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    device: Mapped["Device"] = relationship(back_populates="ping_results")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[float] = mapped_column(Float, nullable=False, default=time.time)

    device: Mapped["Device"] = relationship(back_populates="notifications")
