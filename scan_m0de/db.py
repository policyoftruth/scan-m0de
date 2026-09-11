"""SQLite Database storage manager for device cataloging and diff tracking."""

from __future__ import annotations

import sqlite3
import stat
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_DIR = Path.home() / ".local" / "share" / "scan-m0de"
DEFAULT_DB_PATH = DATA_DIR / "devices.db"


def resolve_db_path(custom_path: Path | None = None) -> Path:
    """Resolve database path: explicit arg -> existing local DB -> persistent global storage."""
    if custom_path:
        return Path(custom_path).expanduser().resolve()

    local_db = Path("devices.db")
    global_db = DEFAULT_DB_PATH

    # If global DB doesn't exist yet, but local devices.db exists in current directory,
    # seamlessly copy it to global storage so existing scans and labels are preserved.
    if not global_db.exists() and local_db.exists() and local_db.is_file():
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            import shutil

            shutil.copy2(local_db, global_db)
            global_db.chmod(0o600)
        except OSError:
            return local_db.resolve()

    return global_db


class Database:
    def __init__(self, db_path: Path | None = None):
        self.db_path = resolve_db_path(db_path)
        self._ensure_secure_file()
        self._init_db()

    def _ensure_secure_file(self):
        """Create the database file with restrictive permissions (owner-only) if it doesn't exist."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        if not db_file.exists():
            db_file.touch(mode=0o600)
        else:
            # Tighten permissions on existing files
            try:
                current = db_file.stat().st_mode
                if current & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH):
                    db_file.chmod(0o600)
            except OSError:
                pass

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Devices catalog table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    mac TEXT PRIMARY KEY,
                    ip TEXT NOT NULL,
                    hostname TEXT,
                    custom_label TEXT DEFAULT '',
                    category TEXT DEFAULT 'Uncategorized',
                    vendor TEXT DEFAULT 'Unknown',
                    notes TEXT DEFAULT '',
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    is_online INTEGER DEFAULT 1,
                    is_new INTEGER DEFAULT 0,
                    open_ports TEXT DEFAULT ''
                )
            """)

            # Scan history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    subnet TEXT NOT NULL,
                    devices_found INTEGER DEFAULT 0,
                    new_devices_count INTEGER DEFAULT 0
                )
            """)

            # Scan diffs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scan_diffs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    mac TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(scan_id) REFERENCES scans(id)
                )
            """)
            conn.commit()

    def sync_scan_results(
        self, discovered_devices: list[dict[str, Any]], subnet: str
    ) -> dict[str, Any]:
        """
        Synchronize scan results with catalog database.
        Calculates diffs: NEW devices, JOINED (went offline->online), LEFT (went online->offline), IP changes.
        """
        now = datetime.now().astimezone().isoformat(timespec="seconds")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create scan record
            cursor.execute(
                "INSERT INTO scans (timestamp, subnet, devices_found, new_devices_count) VALUES (?, ?, ?, 0)",
                (now, subnet, len(discovered_devices)),
            )
            scan_id = cursor.lastrowid

            # Get current catalog state
            cursor.execute(
                "SELECT mac, ip, hostname, custom_label, category, vendor, is_online, first_seen FROM devices"
            )
            catalog = {row["mac"]: dict(row) for row in cursor.fetchall()}

            discovered_macs = {dev["mac"].upper(): dev for dev in discovered_devices}

            new_devices = []
            diffs = []

            # Mark all existing devices as offline initially for this sync pass
            cursor.execute("UPDATE devices SET is_online = 0, is_new = 0")

            # Process discovered devices
            for mac, dev in discovered_macs.items():
                ip = dev.get("ip", "")
                hostname = dev.get("hostname", "")
                category = dev.get("category", "Uncategorized")
                vendor = dev.get("vendor", "Unknown")
                open_ports = dev.get("open_ports", "")

                if mac not in catalog:
                    # New Device!
                    cursor.execute(
                        """
                        INSERT INTO devices (
                            mac, ip, hostname, custom_label, category, vendor, notes,
                            first_seen, last_seen, is_online, is_new, open_ports
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?)
                    """,
                        (
                            mac,
                            ip,
                            hostname,
                            "",
                            category,
                            vendor,
                            "",
                            now,
                            now,
                            open_ports,
                        ),
                    )

                    new_devices.append(mac)
                    diffs.append(
                        (
                            scan_id,
                            mac,
                            "NEW",
                            f"Discovered new device at {ip} ({vendor})",
                            now,
                        )
                    )
                else:
                    prev = catalog[mac]
                    custom_label = prev.get("custom_label", "")
                    existing_vendor = prev.get("vendor", "Unknown")
                    existing_category = prev.get("category", "Uncategorized")

                    # If device has no manual custom label, allow auto-detected vendor & category updates
                    if not custom_label:
                        updated_vendor = (
                            vendor
                            if vendor not in ("Unknown", "Unknown Vendor")
                            else existing_vendor
                        )
                        updated_category = (
                            category if category != "Uncategorized" else existing_category
                        )
                    else:
                        updated_vendor = existing_vendor
                        updated_category = existing_category

                    # Update hostname if previously empty or if a better name was discovered
                    existing_hostname = prev.get("hostname", "")
                    updated_hostname = hostname if hostname else existing_hostname

                    # Update existing device
                    cursor.execute(
                        """
                        UPDATE devices
                        SET ip = ?, hostname = ?, category = ?, vendor = ?, last_seen = ?, is_online = 1, is_new = 0, open_ports = ?
                        WHERE mac = ?
                    """,
                        (
                            ip,
                            updated_hostname,
                            updated_category,
                            updated_vendor,
                            now,
                            open_ports,
                            mac,
                        ),
                    )

                    # Check for diffs
                    if prev["is_online"] == 0:
                        diffs.append(
                            (
                                scan_id,
                                mac,
                                "JOINED",
                                f"Device re-appeared online at {ip}",
                                now,
                            )
                        )
                    if prev["ip"] != ip:
                        diffs.append(
                            (
                                scan_id,
                                mac,
                                "IP_CHANGE",
                                f"IP changed from {prev['ip']} to {ip}",
                                now,
                            )
                        )

            # Check devices that went offline
            for mac, prev in catalog.items():
                if mac not in discovered_macs and prev["is_online"] == 1:
                    diffs.append(
                        (
                            scan_id,
                            mac,
                            "LEFT",
                            f"Device offline (was at {prev['ip']})",
                            now,
                        )
                    )

            # Insert scan diffs
            if diffs:
                cursor.executemany(
                    "INSERT INTO scan_diffs (scan_id, mac, change_type, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                    diffs,
                )

            # Update scan record with new count
            cursor.execute(
                "UPDATE scans SET new_devices_count = ? WHERE id = ?",
                (len(new_devices), scan_id),
            )

            conn.commit()

        return {
            "scan_id": scan_id,
            "total_found": len(discovered_devices),
            "new_count": len(new_devices),
            "diff_count": len(diffs),
        }

    def update_device_label(self, mac: str, label: str, category: str, notes: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE devices
                SET custom_label = ?, category = ?, notes = ?
                WHERE mac = ?
            """,
                (label, category, notes, mac.upper()),
            )
            conn.commit()

    def get_device_by_mac(self, mac: str) -> dict[str, Any] | None:
        """Fetch a single device by MAC address."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM devices WHERE mac = ?", (mac.upper(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_devices(self) -> list[dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM devices ORDER BY is_online DESC, custom_label ASC, ip ASC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_scan_diffs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT d.*, dev.custom_label, dev.hostname, dev.vendor
                FROM scan_diffs d
                LEFT JOIN devices dev ON d.mac = dev.mac
                ORDER BY d.id DESC LIMIT ?
            """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> dict[str, int]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM devices")
            total = cursor.fetchone()["total"]
            cursor.execute("SELECT COUNT(*) as online FROM devices WHERE is_online = 1")
            online = cursor.fetchone()["online"]
            cursor.execute("SELECT COUNT(*) as new_dev FROM devices WHERE is_new = 1")
            new_dev = cursor.fetchone()["new_dev"]
            return {
                "total": total,
                "online": online,
                "offline": total - online,
                "new": new_dev,
            }
