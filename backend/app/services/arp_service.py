import asyncio
import ipaddress
import logging
import time

logger = logging.getLogger(__name__)

# Checked once on first use
_arp_available: bool | None = None


def _check_arp_once() -> bool:
    """Test if we can create raw sockets for ARP."""
    global _arp_available
    if _arp_available is not None:
        return _arp_available
    try:
        from scapy.layers.l2 import ARP, Ether, srp
        # Try sending to an impossible target with tiny timeout — we only care about permission
        packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst="0.0.0.0")
        srp(packet, timeout=0.1, verbose=False)
        _arp_available = True
        logger.info("ARP: raw socket access available")
    except PermissionError:
        _arp_available = False
        logger.warning("ARP: no root privileges — ARP ping and network discovery disabled")
    except OSError as e:
        if "Operation not permitted" in str(e):
            _arp_available = False
            logger.warning("ARP: no root privileges — ARP ping and network discovery disabled")
        else:
            _arp_available = True  # other OS errors don't mean permission denied
    except Exception:
        _arp_available = True  # assume available, let real calls fail naturally
    return _arp_available


def is_arp_available() -> bool:
    """Return whether ARP functionality is available (has root/capabilities)."""
    return _check_arp_once()


def _arp_ping_sync(ip_address: str) -> dict | None:
    if not _check_arp_once():
        return None
    try:
        from scapy.layers.l2 import ARP, Ether, srp

        packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip_address)
        answered, _ = srp(packet, timeout=2, verbose=False)

        if answered:
            sent_pkt, recv_pkt = answered[0]
            elapsed = (recv_pkt.time - sent_pkt.sent_time) * 1000
            return {
                "timestamp": time.time(),
                "ping_type": "arp",
                "latency_ms": round(elapsed, 3),
                "packet_lost": False,
            }
        return {
            "timestamp": time.time(),
            "ping_type": "arp",
            "latency_ms": None,
            "packet_lost": True,
        }
    except Exception as e:
        logger.warning("ARP ping failed for %s: %s", ip_address, e)
        return {
            "timestamp": time.time(),
            "ping_type": "arp",
            "latency_ms": None,
            "packet_lost": True,
        }


async def arp_ping(ip_address: str) -> dict | None:
    """Returns None if ARP is unavailable (no root), otherwise a ping result dict."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _arp_ping_sync, ip_address)


def _get_netmask(addr_info: dict) -> str | None:
    """Get netmask from addr_info, handling both 'netmask' and 'mask' keys."""
    return addr_info.get("netmask") or addr_info.get("mask")


def is_same_subnet(ip_address: str) -> bool:
    """Check if an IP is on the same subnet as any local interface."""
    try:
        try:
            import netifaces2 as netifaces
        except ImportError:
            import netifaces

        target = ipaddress.ip_address(ip_address)
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                for addr_info in addrs[netifaces.AF_INET]:
                    ip = addr_info.get("addr")
                    netmask = _get_netmask(addr_info)
                    if ip and netmask:
                        try:
                            network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                            if target in network:
                                return True
                        except ValueError:
                            continue
        return False
    except Exception:
        return True


def _discover_sync(subnet: str) -> list[dict]:
    """Synchronous ARP scan of a subnet."""
    if not _check_arp_once():
        return []
    try:
        from scapy.layers.l2 import ARP, Ether, srp

        packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)
        answered, _ = srp(packet, timeout=3, verbose=False)

        devices = []
        for sent, received in answered:
            mac = received.hwsrc
            ip = received.psrc
            manufacturer = mac_vendor_lookup(mac)
            devices.append({
                "ip_address": ip,
                "mac_address": mac,
                "manufacturer": manufacturer,
            })
        return devices
    except Exception as e:
        logger.warning("Network discovery failed: %s", e)
        return []


def mac_vendor_lookup(mac: str) -> str | None:
    """Look up MAC vendor from OUI prefix using scapy's OUI database."""
    try:
        from scapy.layers.l2 import conf
        result = conf.manufdb._resolve_MAC(mac)
        # scapy returns the MAC unchanged when it can't resolve
        if not result or result.upper() == mac.upper():
            return None
        # Extract just the vendor name (format: "VendorName:XX:XX:XX")
        vendor = result.split(":")[0] if ":" in result else result
        return vendor if vendor else None
    except Exception:
        return None


async def discover_network(subnet: str | None = None) -> list[dict]:
    """Discover devices on the network via ARP scan."""
    if subnet is None:
        subnet = _detect_subnet()
    if not subnet:
        return []
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _discover_sync, subnet)


def _detect_subnet() -> str | None:
    """Auto-detect the local subnet."""
    try:
        try:
            import netifaces2 as netifaces
        except ImportError:
            import netifaces

        gateways = netifaces.gateways()

        # Try "default" key (original netifaces) first
        default_gw = gateways.get("default", {}).get(netifaces.AF_INET)

        # Fallback: netifaces2 uses AF_INET as key with (gw, iface, is_default) tuples
        if not default_gw:
            af_inet_gws = gateways.get(netifaces.AF_INET, [])
            for entry in af_inet_gws:
                if len(entry) >= 3 and entry[2]:  # is_default flag
                    default_gw = entry
                    break
            if not default_gw and af_inet_gws:
                default_gw = af_inet_gws[0]  # use first gateway if none marked default

        if not default_gw:
            return None

        iface = default_gw[1]
        addrs = netifaces.ifaddresses(iface)
        if netifaces.AF_INET not in addrs:
            return None

        addr_info = addrs[netifaces.AF_INET][0]
        ip = addr_info["addr"]
        netmask = _get_netmask(addr_info)
        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
        return str(network)
    except Exception:
        return None
