# ⚡ scan-m0de

> A slick, modern TUI & local device cataloger for your home/office network built in Python + Textual + SQLite.

`scan-m0de` scans your local subnet, resolves hostnames & MAC vendor manufacturers offline, keeps a local database of all your hardware, lets you attach custom labels & notes, and tracks network diffs over time (new devices joining, devices leaving, IP changes).

---

## ✨ Features

- **🚀 Fast Subnet Discovery**: Multi-threaded L2/L3 ping sweep with system ARP table lookup.
- **🏷️ Custom Cataloging & Nicknames**: Assign custom device names (e.g. *"Living Room Apple TV"*, *"Unraid Storage Server"*), categories, and notes.
- **⚡ Diffing & Audit Logs**: Automatically flags **NEW** devices never seen before and logs online/offline events.
- **📡 Offline MAC Vendor Lookup**: Identifies device manufacturer (Apple, Espressif ESP32/8266, Raspberry Pi, Samsung, Ubiquiti, Synology, Sonos, Google, Amazon, etc.) without requiring external APIs or internet connection.
- **📊 Interactive TUI Dashboard**: Powered by **Textual** with real-time stats, interactive DataTable, search filtering, dark mode, keyboard navigation, and detail editing modals.
- **💾 Flat-file SQLite Database**: Catalog stored cleanly in a single `devices.db` file.
- **🤖 Headless & Export Mode**: Supports headless background scanning (`--scan-only`) for cron jobs, and JSON/CSV data exporting (`--export-json`, `--export-csv`).

---

## 🛠️ Installation

```bash
# Clone or navigate to directory
git clone https://github.com/your-user/scan-m0de.git
cd scan-m0de

# Create virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## 🎮 Usage

### Launch Interactive TUI
```bash
scan-m0de
```

Specify a custom database path or target subnet CIDR:
```bash
scan-m0de --db ~/my_network.db --subnet 192.168.1.0/24
```

### Headless Network Scan (Cron / Background)
```bash
scan-m0de --scan-only
```

### Export Device Catalog
```bash
# Export to JSON
scan-m0de --export-json network_catalog.json

# Export to CSV
scan-m0de --export-csv network_catalog.csv
```

---

## ⌨️ TUI Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `s` or `Space` | Trigger Network Scan |
| `Enter` or `e` | Edit Selected Device Label / Category / Notes |
| `d` | View Audit Log & Diff History |
| `c` | Change Target Subnet CIDR |
| `f` | Focus Search Filter |
| `r` | Refresh Catalog View |
| `q` | Quit |

---

## 🔒 Requirements & Permissions

- **Python 3.9+**
- Standard system `ping` and `arp` binaries (pre-installed on macOS and standard Linux distros).
- On macOS, terminal app may request Local Network access permission on first run.

---

*Built with Python, Textual, and SQLite.*
