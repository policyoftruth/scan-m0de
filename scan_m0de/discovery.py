"""Network service discovery engine: mDNS/ZeroConf, UPnP/SSDP, and HTTP title scraping."""

from __future__ import annotations

import contextlib
import logging
import re
import socket
import ssl
import struct
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# SSL context that ignores self-signed certs for local LAN devices (e.g. router web UIs)
_NO_VERIFY_SSL = ssl.create_default_context()
_NO_VERIFY_SSL.check_hostname = False
_NO_VERIFY_SSL.verify_mode = ssl.CERT_NONE


# ---------------------------------------------------------------------------
# 1. UPnP / SSDP Multicast Probe (UDP 1900 -> 239.255.255.250)
# ---------------------------------------------------------------------------


def probe_ssdp(timeout: float = 1.2) -> dict[str, dict[str, str]]:
    """Broadcast an SSDP M-SEARCH packet to discover UPnP devices on the LAN.

    Returns a dict mapping IP -> {
        'friendly_name': ...,
        'model_name': ...,
        'manufacturer': ...,
        'model_number': ...,
        'server': ...
    }
    """
    search_msg = (
        "M-SEARCH * HTTP/1.1\r\n"
        "HOST: 239.255.255.250:1900\r\n"
        'MAN: "ssdp:discover"\r\n'
        "MX: 1\r\n"
        "ST: ssdp:all\r\n"
        "\r\n"
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(timeout)
    with contextlib.suppress(OSError):
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    raw_responses: dict[str, dict[str, str]] = {}

    try:
        sock.sendto(search_msg.encode("utf-8"), ("239.255.255.250", 1900))
        while True:
            try:
                data, addr = sock.recvfrom(2048)
                ip = addr[0]
                if ip not in raw_responses:
                    text = data.decode("utf-8", errors="ignore")
                    loc_match = re.search(r"LOCATION:\s*(\S+)", text, re.IGNORECASE)
                    server_match = re.search(r"SERVER:\s*([^\r\n]+)", text, re.IGNORECASE)
                    raw_responses[ip] = {
                        "location": loc_match.group(1).strip() if loc_match else "",
                        "server": server_match.group(1).strip() if server_match else "",
                    }
            except socket.timeout:
                break
    except OSError as e:
        logger.debug("SSDP multicast query failed: %s", e)
    finally:
        sock.close()

    # Resolve XML device descriptions from responding locations
    results: dict[str, dict[str, str]] = {}
    for ip, info in raw_responses.items():
        dev_info: dict[str, str] = {}
        if info.get("server"):
            dev_info["server"] = info["server"]

        loc = info.get("location")
        if loc and loc.startswith("http"):
            try:
                req = urllib.request.Request(loc, headers={"User-Agent": "scan-m0de/0.1"})
                with urllib.request.urlopen(req, timeout=0.8) as resp:
                    xml_root = ET.fromstring(resp.read())
                    for elem in xml_root.iter():
                        tag = elem.tag.split("}")[-1]
                        if (
                            tag in ("friendlyName", "modelName", "modelNumber", "manufacturer")
                            and elem.text
                            and elem.text.strip()
                        ):
                            key_map = {
                                "friendlyName": "friendly_name",
                                "modelName": "model_name",
                                "modelNumber": "model_number",
                                "manufacturer": "manufacturer",
                            }
                            key = key_map[tag]
                            if key not in dev_info:
                                dev_info[key] = elem.text.strip()
            except (OSError, urllib.error.URLError, ET.ParseError, TimeoutError):
                pass

        if dev_info:
            results[ip] = dev_info

    return results


# ---------------------------------------------------------------------------
# 2. mDNS / Bonjour (ZeroConf) Multicast Probe (UDP 5353 -> 224.0.0.251)
# ---------------------------------------------------------------------------


def _decode_dns_labels(data: bytes, offset: int) -> tuple[str, int]:
    """Decode DNS wire-format labels with pointer compression support."""
    labels: list[str] = []
    visited: set[int] = set()
    orig_offset = offset
    jumped = False

    while offset < len(data):
        if offset in visited:
            break
        visited.add(offset)

        length = data[offset]
        if length == 0:
            offset += 1
            break
        elif (length & 0xC0) == 0xC0:
            # Pointer compression
            if offset + 1 >= len(data):
                break
            pointer = struct.unpack("!H", data[offset : offset + 2])[0] & 0x3FFF
            if not jumped:
                orig_offset = offset + 2
                jumped = True
            offset = pointer
        else:
            offset += 1
            if offset + length <= len(data):
                labels.append(data[offset : offset + length].decode("utf-8", errors="ignore"))
            offset += length

    return ".".join(labels), (orig_offset if jumped else offset)


def _parse_mdns_response(data: bytes) -> dict[str, str]:
    """Parse an mDNS response packet, extracting friendly names and models."""
    if len(data) < 12:
        return {}

    info: dict[str, str] = {}
    try:
        header = struct.unpack("!HHHHHH", data[:12])
        qdcount, ancount, nscount, arcount = header[2], header[3], header[4], header[5]
        total_records = ancount + nscount + arcount

        offset = 12
        # Skip questions
        for _ in range(qdcount):
            _, offset = _decode_dns_labels(data, offset)
            offset += 4  # qtype + qclass

        # Parse resource records
        for _ in range(total_records):
            if offset >= len(data):
                break
            _rname, offset = _decode_dns_labels(data, offset)
            if offset + 10 > len(data):
                break
            rtype, _rclass, _ttl, rdlength = struct.unpack("!HHIH", data[offset : offset + 10])
            offset += 10
            rdata_end = offset + rdlength

            if rtype == 12:  # PTR record
                target, _ = _decode_dns_labels(data, offset)
                instance = target.split("._")[0]
                if instance and not instance.startswith("_"):
                    info["instance_name"] = instance

            elif rtype == 16:  # TXT record
                txt_data = data[offset:rdata_end]
                pos = 0
                while pos < len(txt_data):
                    tlen = txt_data[pos]
                    if pos + 1 + tlen <= len(txt_data):
                        entry = txt_data[pos + 1 : pos + 1 + tlen].decode("utf-8", errors="ignore")
                        entry_lower = entry.lower()
                        # Google Cast / AirPlay friendly name: fn=...
                        if entry_lower.startswith("fn="):
                            info["friendly_name"] = entry[3:].strip()
                        # Model name: md=... or model=...
                        elif entry_lower.startswith("md="):
                            info["model_name"] = entry[3:].strip()
                        elif entry_lower.startswith("model="):
                            info["model_name"] = entry[6:].strip()
                        elif entry_lower.startswith("name="):
                            info["friendly_name"] = entry[5:].strip()
                    pos += 1 + tlen

            offset = rdata_end
    except (struct.error, IndexError):
        pass

    return info


def probe_mdns(timeout: float = 1.2) -> dict[str, dict[str, str]]:
    """Broadcast mDNS queries for common smart home, media, and printer service types.

    Returns a dict mapping IP -> {
        'friendly_name': ...,
        'model_name': ...,
        'instance_name': ...
    }
    """
    services = [
        "_googlecast._tcp.local",
        "_airplay._tcp.local",
        "_spotify-connect._tcp.local",
        "_ipp._tcp.local",
        "_printer._tcp.local",
        "_http._tcp.local",
        "_companion-link._tcp.local",
        "_smb._tcp.local",
        "_device-info._tcp.local",
    ]

    def build_query(name: str) -> bytes:
        header = struct.pack("!HHHHHH", 0x1234, 0x0000, 1, 0, 0, 0)
        qname = b""
        for part in name.split("."):
            qname += struct.pack("B", len(part)) + part.encode("utf-8")
        qname += b"\x00"
        return header + qname + struct.pack("!HH", 12, 1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    with contextlib.suppress(OSError):
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)

    devices: dict[str, dict[str, str]] = {}

    try:
        for svc in services:
            with contextlib.suppress(OSError):
                sock.sendto(build_query(svc), ("224.0.0.251", 5353))

        while True:
            try:
                data, addr = sock.recvfrom(4096)
                ip = addr[0]
                parsed = _parse_mdns_response(data)
                if parsed:
                    if ip not in devices:
                        devices[ip] = {}
                    # Update fields, preserving best friendly name
                    for k, v in parsed.items():
                        if v and (k not in devices[ip] or len(v) > len(devices[ip][k])):
                            devices[ip][k] = v
            except socket.timeout:
                break
    except OSError as e:
        logger.debug("mDNS query failed: %s", e)
    finally:
        sock.close()

    return devices


# ---------------------------------------------------------------------------
# 3. Lightweight HTTP/HTTPS <title> Scraper
# ---------------------------------------------------------------------------


def fetch_http_title(ip: str, open_ports: list[int], timeout: float = 0.6) -> str:
    """If ports 80, 8080, or 443 are open, quickly grab the HTML <title> tag.

    Returns the stripped title string, or empty string if not found.
    """
    web_candidates = []
    if 80 in open_ports:
        web_candidates.append(("http", 80))
    if 8080 in open_ports:
        web_candidates.append(("http", 8080))
    if 443 in open_ports:
        web_candidates.append(("https", 443))

    for proto, port in web_candidates:
        url = f"{proto}://{ip}:{port}/"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "scan-m0de/0.1"})
            ctx = _NO_VERIFY_SSL if proto == "https" else None
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                chunk = resp.read(4096).decode("utf-8", errors="ignore")
                match = re.search(r"<title[^>]*>(.*?)</title>", chunk, re.IGNORECASE | re.DOTALL)
                if match:
                    title = " ".join(match.group(1).split()).strip()
                    # Filter out useless generic titles
                    if title and title.lower() not in (
                        "index of /",
                        "404 not found",
                        "error",
                        "untitled",
                        "loading...",
                    ):
                        return title
        except (OSError, urllib.error.URLError, TimeoutError):
            pass

    return ""


# ---------------------------------------------------------------------------
# 4. Device Category Heuristic
# ---------------------------------------------------------------------------


def infer_device_category(
    vendor: str,
    hostname: str,
    open_ports: list[int],
    model: str = "",
) -> str:
    """Infer device category based on vendor, detected hostname, model, and open ports."""
    combined = f"{vendor} {hostname} {model}".lower()

    # Network Hardware (Routers, Switches, Gateways)
    network_keywords = (
        "router",
        "gateway",
        "access point",
        "switch",
        "ubiquiti",
        "unifi",
        "tp-link",
        "netgear",
        "asus",
        "cisco",
        "mikrotik",
        "eero",
        "synology router",
        "miniupnp",
    )
    if any(kw in combined for kw in network_keywords):
        return "Network"

    # Printers & Imaging
    printer_keywords = (
        "printer",
        "print",
        "brother",
        "hp laser",
        "epson",
        "canon",
        "xerox",
        "kyocera",
        "ricoh",
        "deskjet",
        "laserjet",
        "mfc-",
        "ipp",
    )
    if (
        any(kw in combined for kw in printer_keywords)
        or 515 in open_ports
        or 631 in open_ports
        or 9100 in open_ports
    ):
        return "Printer"

    # Gaming Consoles
    gaming_keywords = (
        "nintendo",
        "switch",
        "playstation",
        "xbox",
        "steam deck",
        "steamdeck",
        "sony interactive",
    )
    if any(kw in combined for kw in gaming_keywords):
        return "Gaming"

    # Smart Home / Streaming / Media / IoT
    smart_home_keywords = (
        "nest",
        "chromecast",
        "cast",
        "google",
        "hub",
        "mini",
        "roku",
        "apple tv",
        "appletv",
        "homepod",
        "echo",
        "alexa",
        "dot",
        "sonos",
        "hue",
        "espressif",
        "esp32",
        "esp8266",
        "smart",
        "tv",
        "speaker",
        "bulb",
        "tuya",
        "shelly",
        "wemo",
        "camera",
        "hisense",
    )
    if any(kw in combined for kw in smart_home_keywords):
        return "Smart Home"

    # Servers & Storage / NAS
    server_keywords = (
        "nas",
        "synology",
        "qnap",
        "truenas",
        "unraid",
        "proxmox",
        "pve",
        "server",
        "storage",
        "plex",
        "pi-hole",
        "pihole",
        "docker",
        "omv",
    )
    if any(kw in combined for kw in server_keywords):
        return "Server"

    # Workstations / PCs
    workstation_keywords = (
        "macmini",
        "macpro",
        "imac",
        "desktop",
        "workstation",
        "thinkcentre",
        "optiplex",
    )
    if any(kw in combined for kw in workstation_keywords):
        return "Workstation"

    # Laptops & Mobile
    mobile_keywords = (
        "iphone",
        "ipad",
        "android",
        "galaxy",
        "pixel",
        "macbook",
        "laptop",
        "thinkpad",
        "mac1",
        "phone",
    )
    if any(kw in combined for kw in mobile_keywords):
        return "Mobile"

    return "Uncategorized"
