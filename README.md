# ⚡ scan-m0de

> A slick TUI network scanner & device cataloger for your home/office LAN.
> Built with Python, Textual, and SQLite. No bloat, no subscriptions, no cloud. Just your network, your data, your terminal.

`scan-m0de` scans your local subnet, identifies device manufacturers via a hybrid OUI database (40k+ vendors), keeps a local SQLite catalog of all your hardware, lets you attach custom labels & notes, and tracks network diffs over time — flagging new devices, logging when things go offline, and catching IP changes between scans.

---

## ✨ Features

- **🚀 Fast Subnet Discovery** — Multi-threaded ping sweep (64 workers) with system ARP table parsing. Scans a /24 in ~10 seconds.
- **🏷️ Custom Cataloging & Nicknames** — Label your devices with friendly names (*"Living Room Apple TV"*, *"Unraid Server"*), assign categories, and add notes.
- **⚡ Diffing & Audit Log** — Automatically flags **NEW** devices never seen before, logs online/offline transitions, and records IP address changes across scans.
- **📡 Hybrid MAC Vendor Lookup** — Curated friendly-name database (Apple, Sonos, Ubiquiti, Raspberry Pi, ESP32, etc.) layered over the full IEEE OUI registry (~40k entries). Auto-downloads and caches locally — zero API keys, zero cloud calls.
- **📊 Interactive TUI Dashboard** — Powered by [Textual](https://textual.textualize.io) with live stats, sortable device table, search filtering, keyboard navigation, and modal editors.
- **💾 Single-File SQLite Database** — Your entire device catalog lives in one portable `devices.db` file with owner-only permissions (`0600`).
- **🤖 Headless & Export Modes** — Run scans from cron (`--scan-only`), export your catalog to JSON or CSV, update the OUI database on demand.
- **🔒 Privacy First** — Everything runs locally. No telemetry, no network calls except the optional IEEE OUI database download.

---

## 🛠️ Installation

```bash
git clone https://github.com/policyoftruth/scan-m0de.git
cd scan-m0de

python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Download the full IEEE vendor database (optional but recommended)
scan-m0de --update-oui
```

---

## 🎮 Usage

### Launch the TUI
```bash
scan-m0de
```

Custom database path or target subnet:
```bash
scan-m0de --db ~/my_network.db --subnet 192.168.1.0/24
```

### Headless Scan (cron / scripting)
```bash
scan-m0de --scan-only
```

### Export Device Catalog
```bash
scan-m0de --export-json catalog.json
scan-m0de --export-csv catalog.csv
```

### OUI Vendor Database Management
```bash
# Download / refresh the IEEE OUI database (~4MB, cached locally)
scan-m0de --update-oui

# Check database stats and cache age
scan-m0de --oui-stats
```

---

## ⌨️ TUI Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `s` | Scan Network |
| `Enter` | Edit selected device (label, category, notes) |
| `e` | Edit selected device (alternate) |
| `d` | View Audit Log & Diff History |
| `c` | Change Target Subnet |
| `f` | Focus Search Filter |
| `r` | Refresh Table |
| `q` | Quit |

---

## 📡 How Vendor Identification Works

scan-m0de uses a **hybrid two-tier lookup** to identify device manufacturers:

1. **Curated friendly names** (~370 entries) — Maps MAC prefixes to recognizable consumer brands. For example, a MAC registered to *"Flextronics Computing(Suzhou)Co.,Ltd."* (an Apple contract manufacturer) shows up as simply **"Apple"**.

2. **IEEE MA-L registry** (~40,000 entries) — The full public OUI database from [IEEE](https://standards-oui.ieee.org/oui/oui.csv), downloaded and cached locally at `~/.local/share/scan-m0de/`. Auto-refreshes every 30 days, or on demand with `--update-oui`.

3. **Private MAC detection** — Devices using iOS/Android MAC randomization (locally-administered bit set) are flagged as **"Private/Randomized MAC"** instead of "Unknown".

No API keys. No cloud lookups. No dependencies beyond the standard library.

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
│   ├── modals.py     # TUI modal dialogs (edit, diff, subnet)
│   ├── oui.py        # Hybrid MAC vendor lookup (curated + IEEE)
│   └── scanner.py    # Network discovery engine
├── pyproject.toml
└── README.md
```

---

*Built with Python, [Textual](https://textual.textualize.io), and SQLite.*
