"""Local network discovery engine using fast concurrent ping probes & system ARP table parsing."""

from __future__ import annotations

import ipaddress
import logging
import re
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import netifaces

from scan_m0de.oui import lookup_oui

logger = logging.getLogger(__name__)

COMMON_PORTS = [22, 80, 443, 53, 445, 8080, 8443]

# Reject subnets larger than /16 to prevent accidental resource exhaustion
MIN_PREFIX_LENGTH = 16


def validate_subnet(subnet: str) -> str:
    """Validate and normalize a subnet CIDR string. Raises ValueError on invalid input."""
    try:
        network = ipaddress.IPv4Network(subnet, strict=False)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError) as e:
        raise ValueError(f"Invalid subnet CIDR: {subnet!r} — {e}") from e

    if network.prefixlen < MIN_PREFIX_LENGTH:
        raise ValueError(
            f"Subnet /{network.prefixlen} is too large (>{2 ** (32 - network.prefixlen):,} hosts). "
            f"Use /{MIN_PREFIX_LENGTH} or smaller to avoid resource exhaustion."
        )
    return str(network)


def get_default_interface_and_subnet() -> tuple[str, str]:
    """Detect default active network interface name and IPv4 CIDR subnet (e.g. ('en0', '192.168.1.0/24'))."""
    try:
        gws = netifaces.gateways()
        default_gw = gws.get("default", {}).get(netifaces.AF_INET)
        if default_gw:
            iface = default_gw[1]
            ifaddrs = netifaces.ifaddresses(iface).get(netifaces.AF_INET)
            if ifaddrs:
                ip = ifaddrs[0]["addr"]
                netmask = ifaddrs[0]["netmask"]
                network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                return iface, str(network)
    except Exception:
        logger.debug("Failed to detect default gateway via netifaces", exc_info=True)

    # Fallback to local socket inspection
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        return "default", str(network)
    except Exception:
        logger.debug("Failed to detect local IP via socket fallback", exc_info=True)
        return "eth0", "192.168.1.0/24"


def parse_system_arp_table() -> dict[str, str]:
    """Parse local OS ARP table (`arp -a`) into a dictionary mapping IP -> MAC (uppercase)."""
    arp_map = {}
    try:
        output = subprocess.check_output(["arp", "-a"], stderr=subprocess.DEVNULL, text=True)
        # Patterns for macOS: ? (192.168.1.1) at 00:11:22:33:44:55 on en0 ifscope [ethernet]
        # macOS may also output short-form MACs like 0:0:5e:0:1:1
        # Patterns for Linux: hostname (192.168.1.1) at 00:11:22:33:44:55 [ether] on eth0
        pattern = re.compile(r"\((?P<ip>\d+\.\d+\.\d+\.\d+)\)\s+at\s+(?P<mac>[0-9a-fA-F:-]{5,17})")
        for line in output.splitlines():
            match = pattern.search(line)
            if match:
                ip = match.group("ip")
                raw_mac = match.group("mac").lower()
                # Standardize MAC format to XX:XX:XX:XX:XX:XX
                parts = raw_mac.replace("-", ":").split(":")
                if len(parts) == 6:
                    mac = ":".join(p.zfill(2).upper() for p in parts)
                    if mac != "FF:FF:FF:FF:FF:FF" and not mac.startswith("01:00:5E"):
                        arp_map[ip] = mac
    except FileNotFoundError:
        logger.error("'arp' command not found — ARP table parsing unavailable")
    except subprocess.SubprocessError:
        logger.debug("Failed to run 'arp -a'", exc_info=True)
    return arp_map


def ping_host(ip: str, timeout: float = 2.0) -> bool:
    """Send single ICMP echo ping packet to populate ARP cache and check reachability."""
    param = "-n" if sys.platform.lower() == "win32" else "-c"
    timeout_flag = (
        "-w"
        if sys.platform.lower() == "win32"
        else ("-W" if sys.platform.lower() == "darwin" else "-w")
    )
    # macOS -W is in milliseconds, Linux -w is in seconds
    timeout_val = "1000" if sys.platform.lower() == "darwin" else "1"

    cmd = ["ping", param, "1", timeout_flag, timeout_val, ip]
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
        return res.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except OSError:
        logger.debug("Failed to execute ping for %s", ip, exc_info=True)
        return False


def resolve_hostname(ip: str) -> str:
    """Attempt reverse DNS resolution for IP address."""
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except socket.herror:
        return ""
    except socket.gaierror:
        return ""
    except OSError:
        return ""


def check_open_ports(ip: str, ports: list[int] | None = None) -> list[int]:
    """Quickly check common open TCP ports for a given IP."""
    if ports is None:
        ports = COMMON_PORTS
    open_ports = []
    for port in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.15)
                if s.connect_ex((ip, port)) == 0:
                    open_ports.append(port)
        except OSError:
            pass
    return open_ports


class NetworkScanner:
    def __init__(self, subnet: str | None = None):
        if not subnet:
            self.iface, self.subnet = get_default_interface_and_subnet()
        else:
            self.iface = "custom"
            self.subnet = validate_subnet(subnet)

    def scan(self, progress_callback=None) -> list[dict[str, Any]]:
        """Run parallel fast ping sweep across subnet, parse ARP table, resolve hostnames and ports."""
        network = ipaddress.IPv4Network(self.subnet, strict=False)
        hosts = [str(ip) for ip in network.hosts()]
        total_hosts = len(hosts)

        if total_hosts == 0:
            return []

        # 1. Parallel Ping Sweep using ThreadPool
        ping_results = {}

        with ThreadPoolExecutor(max_workers=64) as executor:
            futures = {executor.submit(ping_host, ip): ip for ip in hosts}
            for completed, future in enumerate(as_completed(futures), start=1):
                ip = futures[future]
                try:
                    is_up = future.result()
                    ping_results[ip] = is_up
                except Exception:
                    logger.debug("Ping future failed for %s", ip, exc_info=True)
                    ping_results[ip] = False
                if progress_callback and total_hosts > 0:
                    progress_callback(
                        completed,
                        total_hosts,
                        f"Sweeping IPs ({completed}/{total_hosts})...",
                    )

        # 2. Parse system ARP table
        arp_map = parse_system_arp_table()

        # Gather active hosts (either responded to ping or present in ARP map)
        active_ips = set()
        for ip, is_up in ping_results.items():
            if is_up or ip in arp_map:
                active_ips.add(ip)

        # 3. Resolve metadata (Hostnames, Ports, Vendor) for active IPs
        discovered_devices = []
        with ThreadPoolExecutor(max_workers=32) as executor:

            def collect_device_info(ip: str) -> dict[str, Any] | None:
                mac = arp_map.get(ip)
                if not mac:
                    return None

                hostname = resolve_hostname(ip)
                vendor = lookup_oui(mac)
                open_ports = check_open_ports(ip)
                ports_str = ",".join(str(p) for p in open_ports)

                return {
                    "ip": ip,
                    "mac": mac,
                    "hostname": hostname,
                    "vendor": vendor,
                    "open_ports": ports_str,
                }

            meta_futures = [
                executor.submit(collect_device_info, ip)
                for ip in sorted(active_ips, key=lambda x: [int(octet) for octet in x.split(".")])
            ]
            for f in meta_futures:
                info = f.result()
                if info:
                    discovered_devices.append(info)

        return discovered_devices
