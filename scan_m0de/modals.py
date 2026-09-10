"""Textual Modal Dialogs for device editing, diff viewing, and configuration."""

import ipaddress
from typing import Dict, Any, Optional
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static, DataTable, Rule

from scan_m0de.scanner import MIN_PREFIX_LENGTH


CATEGORIES = [
    ("Uncategorized", "Uncategorized"),
    ("Smart Home (IoT)", "Smart Home"),
    ("Workstation / PC", "Workstation"),
    ("Laptop / Mobile", "Mobile"),
    ("Server / NAS", "Server"),
    ("Networking (Router/AP/Switch)", "Network"),
    ("Gaming / Entertainment", "Gaming"),
    ("Printer / Peripheral", "Printer"),
]


class EditDeviceModal(ModalScreen[Optional[Dict[str, str]]]):
    """Modal dialog to edit device custom label, category, and notes."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, device: Dict[str, Any]):
        super().__init__()
        self.device = device

    def action_cancel(self) -> None:
        self.dismiss(None)

    def compose(self) -> ComposeResult:
        mac = self.device.get("mac", "")
        ip = self.device.get("ip", "")
        vendor = self.device.get("vendor", "Unknown")
        label = self.device.get("custom_label", "")
        category = self.device.get("category", "Uncategorized")
        notes = self.device.get("notes", "")
        header_text = Text.assemble(
            ("Edit Device Catalog Entry\n", "bold cyan"),
            ("MAC: ", "dim"),
            (mac, "dim bold"),
            (" | IP: ", "dim"),
            (ip, "dim"),
            (" | Vendor: ", "dim"),
            (vendor, "dim"),
        )

        yield Vertical(
            Static(header_text, id="modal_header"),
            Rule(),
            Label("[bold]Custom Device Label / Nickname:[/bold]"),
            Input(value=label, placeholder="e.g. Living Room Apple TV, Unraid Server...", id="input_label"),
            Label("[bold]Device Category:[/bold]"),
            Select(options=CATEGORIES, value=category if category in dict(CATEGORIES) else "Uncategorized", id="select_category"),
            Label("[bold]Notes / Location / Info:[/bold]"),
            Input(value=notes, placeholder="e.g. Connected to Port 4 on Switch, Static IP...", id="input_notes"),
            Horizontal(
                Button("Save Catalog Entry", variant="primary", id="btn_save"),
                Button("Cancel", variant="default", id="btn_cancel"),
                id="modal_buttons"
            ),
            id="modal_dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_save":
            label_val = self.query_one("#input_label", Input).value.strip()
            category_val = self.query_one("#select_category", Select).value
            notes_val = self.query_one("#input_notes", Input).value.strip()
            self.dismiss({
                "mac": self.device["mac"],
                "custom_label": label_val,
                "category": str(category_val),
                "notes": notes_val
            })
        else:
            self.dismiss(None)


class DiffHistoryModal(ModalScreen[None]):
    """Modal dialog displaying network scan diff log and history."""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Close", show=True),
        Binding("q", "dismiss_modal", "Close", show=True),
        Binding("d", "dismiss_modal", "Close", show=False),
    ]

    def __init__(self, diffs: list):
        super().__init__()
        self.diffs = diffs

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                Static("[bold yellow]⚡ Network Scan Diffs & Audit Log[/bold yellow]\n[dim]Tracks newly joined devices, IP changes, and offline events.[/dim]", id="diff_title"),
                Button("✖ Close (Esc)", variant="default", id="btn_close_diff_top"),
                id="diff_header_bar"
            ),
            Rule(),
            DataTable(id="diff_table", cursor_type="row"),
            Horizontal(
                Static("[dim]Press [bold]Esc[/bold] or [bold]q[/bold] to return to device catalog[/dim]", id="diff_hint"),
                Button("Close Audit Log", variant="primary", id="btn_close_diff"),
                id="diff_footer"
            ),
            id="diff_dialog"
        )

    def on_mount(self) -> None:
        table = self.query_one("#diff_table", DataTable)
        table.add_columns("Timestamp", "Type", "MAC Address", "Details", "Label / Vendor")
        
        for d in self.diffs:
            change_type = d.get("change_type", "")
            if change_type == "NEW":
                badge = Text("⚡ NEW", style="bold green")
            elif change_type == "JOINED":
                badge = Text("🟢 JOINED", style="green")
            elif change_type == "LEFT":
                badge = Text("🔴 LEFT", style="red")
            else:
                badge = Text(f"🔄 {change_type}", style="yellow")

            label_vendor = d.get("custom_label") or d.get("vendor") or "—"
            table.add_row(
                Text(d.get("timestamp", "")),
                badge,
                Text(d.get("mac", "")),
                Text(d.get("details", "")),
                Text(label_vendor),
            )
        table.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


class SubnetModal(ModalScreen[Optional[str]]):
    """Modal dialog to select or enter subnet."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, current_subnet: str):
        super().__init__()
        self.current_subnet = current_subnet

    def action_cancel(self) -> None:
        self.dismiss(None)

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("[bold cyan]Target Subnet Configuration[/bold cyan]", id="subnet_header"),
            Rule(),
            Label(f"Current Subnet: [bold yellow]{self.current_subnet}[/bold yellow]"),
            Input(value=self.current_subnet, placeholder="e.g. 192.168.1.0/24 or 10.0.0.0/24", id="input_subnet"),
            Static("", id="subnet_error"),
            Horizontal(
                Button("Set Subnet", variant="primary", id="btn_set_subnet"),
                Button("Cancel", variant="default", id="btn_cancel_subnet"),
                id="modal_buttons"
            ),
            id="subnet_dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_set_subnet":
            subnet_val = self.query_one("#input_subnet", Input).value.strip()
            error_label = self.query_one("#subnet_error", Static)

            # Validate subnet before accepting
            try:
                network = ipaddress.IPv4Network(subnet_val, strict=False)
            except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError):
                error_label.update(f"[bold red]Invalid CIDR format. Example: 192.168.1.0/24[/bold red]")
                return

            if network.prefixlen < MIN_PREFIX_LENGTH:
                host_count = 2 ** (32 - network.prefixlen)
                error_label.update(
                    f"[bold red]/{network.prefixlen} is too large ({host_count:,} hosts). "
                    f"Use /{MIN_PREFIX_LENGTH} or smaller.[/bold red]"
                )
                return

            self.dismiss(str(network))
        else:
            self.dismiss(None)
