"""CLI entry point for scan-m0de: TUI launcher, headless scanner, and exporter."""

import argparse
import json
import sys
from pathlib import Path
from scan_m0de.db import Database
from scan_m0de.scanner import NetworkScanner, validate_subnet
from scan_m0de.app import run_app


def main():
    parser = argparse.ArgumentParser(description="scan-m0de: Local network scanner, cataloger, and TUI device manager.")
    parser.add_argument("--db", type=Path, default=Path("devices.db"), help="Path to SQLite database file (default: devices.db)")
    parser.add_argument("--subnet", type=str, help="Target IPv4 subnet CIDR (e.g. 192.168.1.0/24)")
    parser.add_argument("--scan-only", action="store_true", help="Run scan headlessly in background without launching TUI")
    parser.add_argument("--export-json", type=Path, help="Export device catalog to JSON file and exit")
    parser.add_argument("--export-csv", type=Path, help="Export device catalog to CSV file and exit")

    args = parser.parse_args()

    # Validate subnet early if provided
    if args.subnet:
        try:
            args.subnet = validate_subnet(args.subnet)
        except ValueError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)

    db = Database(args.db)

    if args.export_json:
        devices = db.get_all_devices()
        with open(args.export_json, "w") as f:
            json.dump(devices, f, indent=2)
        print(f"✅ Exported {len(devices)} cataloged devices to {args.export_json}")
        sys.exit(0)

    if args.export_csv:
        import csv
        devices = db.get_all_devices()
        if devices:
            fieldnames = list(devices[0].keys())
            with open(args.export_csv, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(devices)
            print(f"✅ Exported {len(devices)} cataloged devices to {args.export_csv}")
        sys.exit(0)

    if args.scan_only:
        print(f"⚡ Running headless network scan...")
        scanner = NetworkScanner(args.subnet)
        devices = scanner.scan()
        summary = db.sync_scan_results(devices, scanner.subnet)
        print(f"✅ Headless scan complete! Found {summary['total_found']} devices ({summary['new_count']} NEW, {summary['diff_count']} diff events).")
        sys.exit(0)

    # Launch Textual TUI
    run_app(db_path=args.db, subnet=args.subnet)


if __name__ == "__main__":
    main()
