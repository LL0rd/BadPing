from pydantic import BaseModel, field_validator


class DeviceCheck(BaseModel):
    ip_address: str | None = None
    mac_address: str | None = None

    @field_validator("ip_address", "mac_address", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v


class DeviceCreate(BaseModel):
    name: str
    ip_address: str | None = None
    mac_address: str | None = None
    fingerprint_enabled: bool = False
    ping_type: str = "icmp"
    interval_seconds: float = 1.0
    packet_size: int = 64
    retention_days: int = 14
    monitoring_enabled: bool = True

    @field_validator("ping_type")
    @classmethod
    def validate_ping_type(cls, v):
        if v not in ("icmp", "arp", "both"):
            raise ValueError("ping_type must be 'icmp', 'arp', or 'both'")
        return v

    @field_validator("interval_seconds")
    @classmethod
    def validate_interval(cls, v):
        allowed = [0.01, 0.1, 1.0]
        if v not in allowed:
            raise ValueError(f"interval_seconds must be one of {allowed}")
        return v

    @field_validator("packet_size")
    @classmethod
    def validate_packet_size(cls, v):
        allowed = [64, 128, 256, 512, 1024, 1500]
        if v not in allowed:
            raise ValueError(f"packet_size must be one of {allowed}")
        return v


class DeviceUpdate(BaseModel):
    name: str | None = None
    fingerprint_enabled: bool | None = None
    ping_type: str | None = None
    interval_seconds: float | None = None
    packet_size: int | None = None
    retention_days: int | None = None
    monitoring_enabled: bool | None = None

    @field_validator("ping_type")
    @classmethod
    def validate_ping_type(cls, v):
        if v is not None and v not in ("icmp", "arp", "both"):
            raise ValueError("ping_type must be 'icmp', 'arp', or 'both'")
        return v

    @field_validator("interval_seconds")
    @classmethod
    def validate_interval(cls, v):
        if v is not None and v not in [0.01, 0.1, 1.0]:
            raise ValueError("interval_seconds must be one of [0.01, 0.1, 1.0]")
        return v

    @field_validator("packet_size")
    @classmethod
    def validate_packet_size(cls, v):
        if v is not None and v not in [64, 128, 256, 512, 1024, 1500]:
            raise ValueError("packet_size must be one of [64, 128, 256, 512, 1024, 1500]")
        return v

    @field_validator("retention_days")
    @classmethod
    def validate_retention(cls, v):
        if v is not None and v not in [1, 5, 7, 14, 30, 90]:
            raise ValueError("retention_days must be one of [1, 5, 7, 14, 30, 90]")
        return v


class DeviceResponse(BaseModel):
    id: int
    name: str
    ip_address: str | None
    mac_address: str | None
    manufacturer: str | None
    os_info: str | None
    device_type: str | None
    nmap_raw: str | None
    fingerprint_enabled: bool
    ping_type: str
    interval_seconds: float
    packet_size: int
    retention_days: int
    monitoring_enabled: bool
    status: str
    last_seen_at: float | None
    created_at: float
    updated_at: float

    model_config = {"from_attributes": True}


class DeviceWithStats(DeviceResponse):
    stats_6h: float | None = None
    stats_12h: float | None = None
    stats_24h: float | None = None
    stats_48h: float | None = None


class CheckResult(BaseModel):
    reachable: bool
    ip_address: str | None = None
    mac_address: str | None = None
    message: str
    same_subnet: bool = True


class StatsResponse(BaseModel):
    device_id: int
    stats_6h: float
    stats_12h: float
    stats_24h: float
    stats_48h: float
    total_pings_24h: int
    lost_pings_24h: int
    ok_pings_24h: int
    avg_latency_24h: float | None
    min_latency_24h: float | None
    max_latency_24h: float | None


class GraphPoint(BaseModel):
    timestamp: float
    latency_ms: float | None
    packet_lost: bool
    ping_type: str | None = None


class GraphResponse(BaseModel):
    device_id: int
    points: list[GraphPoint]
    resolution_seconds: float


class NotificationResponse(BaseModel):
    id: int
    device_id: int
    device_name: str | None = None
    type: str
    message: str
    is_read: bool
    created_at: float

    model_config = {"from_attributes": True}


class NotificationList(BaseModel):
    notifications: list[NotificationResponse]
    unread_count: int


class DiscoverRequest(BaseModel):
    subnet: str | None = None


class DiscoveredDevice(BaseModel):
    ip_address: str
    mac_address: str | None = None
    manufacturer: str | None = None
    hostname: str | None = None
