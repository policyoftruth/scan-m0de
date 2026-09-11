# ⚡ scan-m0de

> A slick TUI network scanner & device cataloger for your home/office LAN.
> Built with Python, Textual, and SQLite. No bloat, no subscriptions, no cloud. Just your network, your data, your terminal.

`scan-m0de` scans your local subnet, identifies device manufacturers via a hybrid OUI database (40k+ vendors), keeps a local SQLite catalog of all your hardware, lets you attach custom labels & notes, and tracks network diffs over time — flagging new devices, logging when things go offline, and catching IP changes between scans.

---

## ✨ Features

- **🚀 Fast Subnet Discovery** — Multi-threaded ping sweep (64 workers) with system ARP table parsing. Scans a /24 in ~10 seconds.
- **🔍 Pure-Python Service Discovery (Zero Root)** — Parallel multicast mDNS/Bonjour (`_googlecast`, `_airplay`, `_printer`, `_spotify-connect`), UPnP/SSDP device XML scraping, and lightweight HTTP title detection resolve exact hardware models and friendly names (*"Kitchen Nest Hub"*, *"Brother MFC-J1170DW"*).
- **🏷️ Custom Cataloging & Smart Categorization** — Automatically infers device categories (Printers, Smart Home, Gaming, Network, Server) while letting you set friendly custom labels (*"Living Room Apple TV"*, *"Unraid Server"*), manual categories, and notes.
- **⚡ Diffing & Audit Log** — Automatically flags **NEW** devices never seen before, logs online/offline transitions, and records IP address changes across scans.
- **📡 Hybrid MAC Vendor Lookup** — Curated friendly-name database (Apple, Sonos, Ubiquiti, Raspberry Pi, ESP32, etc.) layered over the full IEEE OUI registry (~40k entries). Auto-downloads and caches locally — zero API keys, zero cloud calls.
- **📊 Interactive TUI Dashboard** — Powered by [Textual](https://textual.textualize.io) with real-time stats, live search filtering, status filtering (Online/Offline/New), keyboard navigation, and modal editors.
- **💾 Single-File SQLite Database** — Your entire device catalog lives in one portable `devices.db` file with owner-only permissions (`0600`), stored centrally at `~/.local/share/scan-m0de/devices.db`.
- **🤖 Headless & Export Modes** — Run scans from cron (`--scan-only`), stream or save catalog data to JSON or CSV (with `-` for stdout), and update the OUI database on demand.
- **🔒 Privacy First** — Everything runs locally. Zero telemetry, zero root/sudo required, and no external network calls except the optional IEEE OUI database download.

---

## 🛠️ Installation

### Option 1: Standalone CLI Tool (Recommended — Available Everywhere)

Using `uv` (or `pipx`), install `scan-m0de` globally so it is always available on your `$PATH` without ever needing to activate a virtual environment:

```bash
git clone https://github.com/policyoftruth/scan-m0de.git
cd scan-m0de

# Install globally in editable mode (so git pulls / edits take effect immediately)
uv tool install --editable .
# or with pipx:
# pipx install --editable .

# Download the full IEEE vendor database (optional but recommended)
scan-m0de --update-oui
```

### Option 2: Standard Virtualenv

```bash
git clone https://github.com/policyoftruth/scan-m0de.git
cd scan-m0de

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
scan-m0de --update-oui
```

---

## 🎮 Usage

### Launch the TUI

From **any directory in any terminal**, simply run:

```bash
scan-m0de
```

Your database is stored centrally and persistently at `~/.local/share/scan-m0de/devices.db`.

To specify a custom database file or target subnet:
```bash
scan-m0de --db ~/my_network.db --subnet 192.168.1.0/24
```

### Headless Scan (cron / scripting)
```bash
scan-m0de --scan-only
```

### Export Device Catalog
```bash
# Save to file
scan-m0de --export-json catalog.json
scan-m0de --export-csv catalog.csv

# Or stream directly to stdout for piping (e.g. into jq)
scan-m0de --export-json - | jq '.[].ip'
scan-m0de --export-csv -
```

### OUI Vendor Database Management
```bash
# Download / refresh the IEEE OUI database (~4MB, cached locally)
scan-m0de --update-oui

# Check database stats and cache age
scan-m0de --oui-stats
```

---

## ⌨️ TUI Navigation & Shortcuts

Navigate rows with **`↑` / `↓` Arrow Keys** or **Mouse Clicks**.

| Key | Action |
|-----|--------|
| `s` | Scan Network |
| `Enter` | Edit selected device (label, category, notes) |
| `e` | Edit selected device (alternate) |
| `d` | View Audit Log & Diff History |
| `c` | Change Target Subnet (e.g. `/24`, `/16`) |
| `f` | Focus Search Filter Bar |
| `r` | Refresh Table View |
| `q` | Quit Application |

*Tip: You can also **double-click** any device row to open the editor directly.*

---

## 📡 How Device & Service Identification Works

scan-m0de combines MAC-layer lookups with zero-root active discovery to identify devices with high accuracy:

1. **Curated Friendly Names** (~370 entries) — Maps MAC prefixes to recognizable consumer brands. For example, a MAC registered to *"Flextronics Computing(Suzhou)Co.,Ltd."* (an Apple contract manufacturer) shows up as simply **"Apple"**.
2. **IEEE MA-L Registry** (~40,000 entries) — The full public OUI database from [IEEE](https://standards-oui.ieee.org/oui/oui.csv), downloaded and cached locally at `~/.local/share/scan-m0de/`. Auto-refreshes every 30 days, or on demand with `--update-oui`.
3. **Private MAC Detection** — Devices using iOS/Android MAC randomization (locally-administered bit set) are flagged as **"Private/Randomized MAC"** instead of "Unknown".
4. **Multicast mDNS/Bonjour** — Concurrently probes `224.0.0.251:5353` for `_googlecast`, `_airplay`, `_spotify-connect`, `_ipp`, `_printer`, `_http`, `_companion-link`, and `_device-info`. Extracts friendly model and room names directly from DNS PTR, SRV, and TXT records without third-party libraries.
5. **UPnP/SSDP Discovery** — Sends `M-SEARCH` queries across `239.255.255.250:1900` and parses XML device descriptions to extract exact router models, media renderers, and printer hardware info.
6. **Lightweight HTTP Title Scraping** — Grabs HTML `<title>` tags on web ports (80, 443, 8080) with self-signed SSL support for web management consoles.
7. **Rule-Based Categorization** — Automatically assigns categories (*Network*, *Printer*, *Smart Home*, *Gaming*, *Server*, *Workstation*, *Mobile*) while strictly respecting your manual overrides and custom labels.

No API keys. No cloud lookups. No third-party network libraries or root privileges required.

---

## 🔒 Requirements & Permissions

- **Python 3.9+**
- **macOS or Linux** — Windows is not supported and has no plans to be. If you're scanning networks from Windows, we respect your life choices but can't help you here. 🪟❌
- System `ping` and `arp` binaries (pre-installed on macOS; on Linux install `net-tools` if `arp` is missing)
- On macOS, your terminal may request **Local Network** permission on first run

---

## 📁 Project Structure

```
scan-m0de/
├── scan_m0de/
│   ├── app.py        # Textual TUI application
│   ├── cli.py        # CLI entry point & arg parsing
│   ├── db.py         # SQLite database manager
│   ├── discovery.py  # mDNS, UPnP/SSDP & HTTP title discovery
│   ├── modals.py     # TUI modal dialogs (edit, diff, subnet)
│   ├── oui.py        # Hybrid MAC vendor lookup (curated + IEEE)
│   └── scanner.py    # Network discovery engine
├── pyproject.toml
└── README.md
```

---

*Built with Python, [Textual](https://textual.textualize.io), and SQLite.*
