import asyncio
import logging
import re

logger = logging.getLogger(__name__)


async def basic_scan(ip_address: str) -> dict:
    """Run a basic nmap -sn scan (no port scan, no OS detection)."""
    return await _run_nmap(ip_address, ["-sn"])


async def nmap_scan(ip_address: str) -> dict:
    # Try full OS fingerprint first (requires root + port scan)
    result = await _run_nmap(ip_address, ["-O", "--osscan-guess"], timeout=60)
    raw = (result.get("raw") or "").lower()

    if "requires root" in raw or "quitting" in raw:
        logger.info("nmap OS detection failed (%s), falling back to basic scan",
                     "no root" if "requires root" in raw else "incompatible flags")
        basic = await _run_nmap(ip_address, ["-sn"])
        basic["raw"] = (
            "Note: OS fingerprinting requires root privileges and a port scan. "
            "Run in Docker with NET_RAW/NET_ADMIN for full device detection.\n\n"
            + basic.get("raw", "")
        )
        return basic

    return result


async def _run_nmap(ip_address: str, flags: list[str], timeout: int = 30) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            "nmap", *flags, ip_address,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode("utf-8", errors="replace")
        err_output = stderr.decode("utf-8", errors="replace")

        # nmap prints the root error to stdout or stderr depending on version
        if proc.returncode != 0:
            output = output + "\n" + err_output

        result = {
            "raw": output.strip(),
            "os_info": None,
            "manufacturer": None,
            "mac_address": None,
            "device_type": None,
        }

        mac_match = re.search(r"MAC Address:\s+([0-9A-F:]{17})\s+\((.+?)\)", output)
        if mac_match:
            result["mac_address"] = mac_match.group(1)
            result["manufacturer"] = mac_match.group(2)

        os_match = re.search(r"OS details?:\s+(.+)", output)
        if os_match:
            result["os_info"] = os_match.group(1).strip()
        else:
            aggressive_match = re.search(r"Aggressive OS guesses?:\s+(.+)", output)
            if aggressive_match:
                result["os_info"] = aggressive_match.group(1).strip()

        type_match = re.search(r"Device type:\s+(.+)", output)
        if type_match:
            result["device_type"] = type_match.group(1).strip()

        return result

    except asyncio.TimeoutError:
        return {"raw": "nmap scan timed out", "os_info": None, "manufacturer": None, "mac_address": None, "device_type": None}
    except FileNotFoundError:
        return {"raw": "nmap not installed", "os_info": None, "manufacturer": None, "mac_address": None, "device_type": None}
    except Exception as e:
        return {"raw": str(e), "os_info": None, "manufacturer": None, "mac_address": None, "device_type": None}
