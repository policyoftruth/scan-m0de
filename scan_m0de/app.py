"""Main Textual TUI Application for scan-m0de."""

from typing import Dict, Any, List, Optional
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ProgressBar,
    Select,
    Static,
    Rule,
)

from scan_m0de.db import Database
from scan_m0de.scanner import NetworkScanner, get_default_interface_and_subnet
from scan_m0de.modals import EditDeviceModal, DiffHistoryModal, SubnetModal


APP_CSS = """
Screen {
    background: $surface;
    color: $text;
}

#header_bar {
    dock: top;
    height: 3;
    content-align: center middle;
    background: $accent;
    color: $text;
    text-style: bold;
}

#stats_bar {
    height: 4;
    margin: 1 1 0 1;
    align: center middle;
}

.stat_box {
    width: 1fr;
    height: 100%;
    content-align: center middle;
    border: solid $accent-lighten-2;
    background: $panel;
    margin: 0 1;
}

.stat_number {
    text-style: bold;
    color: $success;
}

.stat_number_new {
    text-style: bold;
    color: $warning;
}

#control_bar {
    height: 3;
    margin: 1 1;
}

#search_input {
    width: 2fr;
    margin-right: 1;
}

#status_filter {
    width: 1fr;
    margin-right: 1;
}

#scan_btn {
    width: 15;
    margin-right: 1;
}

#diff_btn {
    width: 15;
}

#table_container {
    height: 1fr;
    margin: 0 1 1 1;
}

#device_table {
    height: 1fr;
}

#progress_bar {
    display: none;
    margin: 0 1;
}

#modal_dialog, #diff_dialog, #subnet_dialog {
    padding: 1 2;
    background: $panel;
    border: thick $accent;
    width: 70;
    height: auto;
}

#diff_dialog {
    width: 95;
    height: 30;
}

#modal_buttons {
    margin-top: 1;
    align: right middle;
}

#modal_buttons Button {
    margin-left: 1;
}

Label {
    margin-top: 1;
}
"""


FILTER_OPTIONS = [
    ("All Devices", "ALL"),
    ("Online Only 🟢", "ONLINE"),
    ("Offline Only 🔴", "OFFLINE"),
    ("New Devices Only ⚡", "NEW"),
]


class ScanModeApp(App):
    CSS = APP_CSS
    TITLE = "scan-m0de // Local Network Device Cataloger"
    SUB_TITLE = "Catalog, label, & diff devices on your local network"

    BINDINGS = [
        Binding("s", "trigger_scan", "Scan Network", show=True),
        Binding("enter", "edit_selected", "Edit Label", show=True),
        Binding("e", "edit_selected", "Edit Label", show=False),
        Binding("d", "view_diffs", "Audit / Diffs Log", show=True),
        Binding("c", "change_subnet", "Change Subnet", show=True),
        Binding("f", "focus_search", "Search Filter", show=True),
        Binding("r", "refresh_data", "Refresh", show=False),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, db_path: Optional[Path] = None, subnet: Optional[str] = None):
        super().__init__()
        self.db = Database(db_path)
        self.iface, detected_subnet = get_default_interface_and_subnet()
        self.subnet = subnet or detected_subnet
        self.is_scanning = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        yield Horizontal(
            Vertical(
                Static("TOTAL DEVICES", classes="stat_title"),
                Static("0", id="stat_total", classes="stat_number"),
                classes="stat_box"
            ),
            Vertical(
                Static("ONLINE NOW", classes="stat_title"),
                Static("0", id="stat_online", classes="stat_number"),
                classes="stat_box"
            ),
            Vertical(
                Static("OFFLINE", classes="stat_title"),
                Static("0", id="stat_offline", classes="stat_number"),
                classes="stat_box"
            ),
            Vertical(
                Static("NEW DISCOVERIES", classes="stat_title"),
                Static("0", id="stat_new", classes="stat_number_new"),
                classes="stat_box"
            ),
            id="stats_bar"
        )

        yield Horizontal(
            Input(placeholder="🔍 Search custom label, IP, MAC, vendor, hostname...", id="search_input"),
            Select(options=FILTER_OPTIONS, value="ALL", id="status_filter"),
            Button("⚡ Scan Now", variant="primary", id="scan_btn"),
            Button("📜 Audit Diffs", variant="default", id="diff_btn"),
            id="control_bar"
        )

        yield ProgressBar(id="progress_bar", total=100, show_percentage=True, show_eta=False)

        yield Container(
            DataTable(id="device_table", cursor_type="row"),
            id="table_container"
        )

        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#device_table", DataTable)
        table.add_columns(
            "Status",
            "Custom Label / Nickname",
            "IP Address",
            "MAC Address",
            "Vendor / Hardware",
            "Hostname",
            "Category",
            "Ports",
            "Last Seen"
        )
        self.refresh_table()

    def refresh_table(self) -> None:
        """Reload device catalog from SQLite database and render table rows."""
        stats = self.db.get_stats()
        self.query_one("#stat_total", Static).update(str(stats["total"]))
        self.query_one("#stat_online", Static).update(str(stats["online"]))
        self.query_one("#stat_offline", Static).update(str(stats["offline"]))
        self.query_one("#stat_new", Static).update(str(stats["new"]))

        search_query = self.query_one("#search_input", Input).value.lower().strip()
        status_filter = self.query_one("#status_filter", Select).value

        devices = self.db.get_all_devices()

        table = self.query_one("#device_table", DataTable)
        table.clear()

        for dev in devices:
            # Apply filters
            if status_filter == "ONLINE" and not dev["is_online"]:
                continue
            if status_filter == "OFFLINE" and dev["is_online"]:
                continue
            if status_filter == "NEW" and not dev["is_new"]:
                continue

            if search_query:
                combined = f"{dev.get('custom_label', '')} {dev.get('ip', '')} {dev.get('mac', '')} {dev.get('vendor', '')} {dev.get('hostname', '')} {dev.get('category', '')} {dev.get('notes', '')}".lower()
                if search_query not in combined:
                    continue

            # Format status badge
            if dev["is_new"]:
                status_badge = "[bold yellow]⚡ NEW[/bold yellow]"
            elif dev["is_online"]:
                status_badge = "[bold green]🟢 Online[/bold green]"
            else:
                status_badge = "[dim red]🔴 Offline[/dim red]"

            label_display = dev["custom_label"] if dev["custom_label"] else "[dim]— Set Label (Enter) —[/dim]"
            vendor_display = dev["vendor"] if dev["vendor"] else "Unknown"
            hostname_display = dev["hostname"] if dev["hostname"] else "—"
            ports_display = dev["open_ports"] if dev["open_ports"] else "—"

            table.add_row(
                status_badge,
                label_display,
                dev["ip"],
                dev["mac"],
                vendor_display,
                hostname_display,
                dev["category"],
                ports_display,
                dev["last_seen"],
                key=dev["mac"]
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search_input":
            self.refresh_table()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "status_filter":
            self.refresh_table()

    def action_focus_search(self) -> None:
        self.query_one("#search_input", Input).focus()

    def action_refresh_data(self) -> None:
        self.refresh_table()

    def action_trigger_scan(self) -> None:
        if not self.is_scanning:
            self.is_scanning = True  # Set flag on main thread before dispatching worker
            self.run_worker(self.perform_network_scan, thread=True, exclusive=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "scan_btn":
            self.action_trigger_scan()
        elif event.button.id == "diff_btn":
            self.action_view_diffs()

    def perform_network_scan(self) -> None:
        """Background worker performing network discovery sweep in a separate thread."""
        try:
            scan_btn = self.query_one("#scan_btn", Button)
            progress = self.query_one("#progress_bar", ProgressBar)
            
            self.call_from_thread(setattr, scan_btn, "disabled", True)
            self.call_from_thread(setattr, scan_btn, "label", "Scanning...")
            self.call_from_thread(setattr, progress.styles, "display", "block")
            self.call_from_thread(setattr, progress, "progress", 0)

            def progress_cb(current, total, msg):
                if total > 0:
                    pct = int((current / total) * 100)
                    self.call_from_thread(setattr, progress, "progress", pct)

            scanner = NetworkScanner(self.subnet)
            self.call_from_thread(self.notify, f"Initiating scan on subnet {self.subnet} ({self.iface})...", title="Scan Started")

            results = scanner.scan(progress_callback=progress_cb)

            # Sync results to SQLite
            summary = self.db.sync_scan_results(results, self.subnet)

            self.call_from_thread(setattr, scan_btn, "disabled", False)
            self.call_from_thread(setattr, scan_btn, "label", "⚡ Scan Now")
            self.call_from_thread(setattr, progress.styles, "display", "none")

            self.call_from_thread(self.refresh_table)
            
            msg = f"Scan finished! Found {summary['total_found']} devices ({summary['new_count']} NEW)."
            self.call_from_thread(self.notify, msg, title="Scan Complete", severity="information" if summary['new_count'] == 0 else "warning")
        finally:
            self.is_scanning = False

    def action_edit_selected(self) -> None:
        """Open device editor modal for currently selected table row."""
        table = self.query_one("#device_table", DataTable)
        if table.row_count == 0 or table.cursor_row is None:
            return

        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        mac = str(row_key.value)

        # Fetch only the selected device from DB
        device = self.db.get_device_by_mac(mac)
        if device:
            def handle_edit(result: Optional[Dict[str, str]]) -> None:
                if result:
                    self.db.update_device_label(
                        result["mac"],
                        result["custom_label"],
                        result["category"],
                        result["notes"]
                    )
                    self.refresh_table()
                    self.notify(f"Updated label for {result['mac']}", title="Catalog Saved")

            self.push_screen(EditDeviceModal(device), handle_edit)

    def action_view_diffs(self) -> None:
        diffs = self.db.get_scan_diffs()
        if not diffs:
            self.notify("No diff history logged yet. Run scans to track network changes!", title="Audit Log Empty")
            return
        self.push_screen(DiffHistoryModal(diffs))

    def action_change_subnet(self) -> None:
        def handle_subnet(new_subnet: Optional[str]) -> None:
            if new_subnet:
                self.subnet = new_subnet
                self.notify(f"Active subnet updated to {self.subnet}", title="Subnet Changed")

        self.push_screen(SubnetModal(self.subnet), handle_subnet)


def run_app(db_path: Optional[Path] = None, subnet: Optional[str] = None):
    app = ScanModeApp(db_path=db_path, subnet=subnet)
    app.run()
