"""App settings panel (center slot): connection management -- disconnect lives
here ONLY (never in the sidebar), plus a read-only view of saved connection
metadata (never secret values). DUI-correct: ui.Form submit_label/defaults."""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers_connection as h


@ext.panel("netsuite_settings", title="NetSuite settings", slot="center")
async def netsuite_settings(ctx) -> ui.UINode:
    conns = await h._load_connections(ctx)
    if not conns:
        return ui.Stack(direction="v", gap=3, children=[
            ui.Text("No NetSuite connections saved yet.", variant="body"),
            ui.Text("Use the left panel to connect an account first.", variant="caption"),
        ])

    children: list[ui.UINode] = [
        ui.Text("Saved connections", variant="heading"),
        ui.Text("Secret values are never shown here.", variant="caption"),
    ]
    for c in conns:
        label = c.get("label") or "NetSuite"
        children.append(ui.Divider())
        children.append(ui.Stack(direction="v", gap=1, children=[
            ui.Text(label, variant="body"),
            ui.Text(f"account {c.get('account_id', '')} · consumer {h._mask(c.get('consumer_key', ''))}", variant="caption"),
        ]))
        children.append(ui.Form(
            action="__tool__disconnect_netsuite",
            submit_label="Disconnect this account",
            defaults={"connection_id": c.get("id", "")},
            children=[
                ui.Text("This removes the saved TBA credentials from Imperal only.", variant="caption"),
            ],
        ))
    return ui.Stack(direction="v", gap=3, children=children)


@ext.panel("netsuite_secrets", title="NetSuite secrets", slot="right")
async def netsuite_secrets(ctx) -> ui.UINode:
    conns = await h._load_connections(ctx)
    return ui.Stack(direction="v", gap=2, children=[
        ui.Text("Secret storage", variant="heading"),
        ui.Text(f"{len(conns)} saved connection(s) in slot 'netsuite_connections'.", variant="caption"),
        ui.Text("Consumer/token secrets are stored encrypted and never displayed.", variant="caption"),
    ])
