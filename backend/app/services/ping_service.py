import logging
import time

from icmplib import async_ping

logger = logging.getLogger(__name__)

# Auto-detect whether we can use privileged (raw) sockets
_use_privileged: bool | None = None


async def icmp_ping(ip_address: str, packet_size: int = 64) -> dict:
    global _use_privileged

    if _use_privileged is None:
        # First call: try privileged, fall back to unprivileged
        try:
            result = await async_ping(
                ip_address, count=1, timeout=2,
                payload_size=max(0, packet_size - 28), privileged=True,
            )
            _use_privileged = True
            logger.info("ICMP: using privileged (raw) sockets")
        except PermissionError:
            _use_privileged = False
            logger.info("ICMP: no root, using unprivileged sockets")
            result = await async_ping(
                ip_address, count=1, timeout=2,
                payload_size=max(0, packet_size - 28), privileged=False,
            )
        except Exception:
            _use_privileged = False
            result = await async_ping(
                ip_address, count=1, timeout=2,
                payload_size=max(0, packet_size - 28), privileged=False,
            )

        return _make_result(result)

    try:
        result = await async_ping(
            ip_address,
            count=1,
            timeout=2,
            payload_size=max(0, packet_size - 28),
            privileged=_use_privileged,
        )
        return _make_result(result)
    except Exception:
        return {
            "timestamp": time.time(),
            "ping_type": "icmp",
            "latency_ms": None,
            "packet_lost": True,
        }


def _make_result(result) -> dict:
    ts = time.time()
    if result.packets_received > 0:
        return {
            "timestamp": ts,
            "ping_type": "icmp",
            "latency_ms": result.avg_rtt,
            "packet_lost": False,
        }
    return {
        "timestamp": ts,
        "ping_type": "icmp",
        "latency_ms": None,
        "packet_lost": True,
    }
