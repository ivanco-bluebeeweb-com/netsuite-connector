"""Panel UI -- connect form + connection list, per ~/UI_INTERFACE_STANDARD.md:
every Input has its own visible label + contextual placeholder, the form
stretches full sidebar width with its content stretched inside, and the
"How do I set this up?" text lives ONLY in the help modal (never duplicated
as static sidebar text). The "App settings" button is always LAST.
DUI-correct kwargs: ui.Form submit_label/defaults only (Pipedream lesson)."""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers_connection as h


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", full_width=True,
        icon="settings", on_click=ui.Call("__panel__netsuite_settings"),
    )


def _help_modal() -> ui.UINode:
    return ui.Modal(
        trigger=ui.Button("How do I set this up?", variant="ghost", size="sm", full_width=True),
        title="Connecting NetSuite",
        children=[
            ui.Text(
                "1. In NetSuite: Setup > Integration > Manage Integrations > New. Enable Token-Based "
                "Authentication, save, and copy the CONSUMER key/secret it shows once.",
                variant="body",
            ),
            ui.Text(
                "2. Then: Setup > Users/Roles > Access Tokens > New -- pick that integration, a user and a "
                "role; save and copy the TOKEN key/secret it shows once.",
                variant="body",
            ),
            ui.Text(
                "3. Your account id is the number in your NetSuite URL (e.g. 1234567, or 1234567_SB1 for "
                "sandbox). Paste everything here -- we verify it live before saving. Role permissions decide "
                "which records read/write later.",
                variant="body",
            ),
        ],
    )


def _connect_form() -> ui.UINode:
    return ui.Form(
        action="__tool__connect_netsuite",
        submit_label="Connect NetSuite",
        children=[
            ui.Input(name="label", label="Label", placeholder="e.g. Acme production ERP", required=False),
            ui.Input(name="account_id", label="Account ID", placeholder="e.g. 1234567 or 1234567_SB1", required=True),
            ui.Input(name="consumer_key", label="Consumer Key", placeholder="From the Integration record", required=True, sensitive=True),
            ui.Input(name="consumer_secret", label="Consumer Secret", placeholder="From the same Integration record", required=True, sensitive=True),
            ui.Input(name="token_key", label="Token Key", placeholder="From the Access Token page", required=True, sensitive=True),
            ui.Input(name="token_secret", label="Token Secret", placeholder="From the same Access Token page", required=True, sensitive=True),
        ],
    )


def _connection_rows(conns: list[dict]) -> list[ui.UINode]:
    rows: list[ui.UINode] = [ui.Text("Connected accounts", variant="heading")]
    for c in conns:
        label = c.get("label") or "NetSuite"
        rows.append(ui.Divider())
        rows.append(ui.Stack(direction="v", gap=1, children=[
            ui.Text(label, variant="body"),
            ui.Text(f"account {c.get('account_id', '')} · consumer {h._mask(c.get('consumer_key', ''))}", variant="caption"),
        ]))
    return rows


@ext.panel("netsuite_connect", title="NetSuite", slot="left")
async def netsuite_connect(ctx) -> ui.UINode:
    conns = await h._load_connections(ctx)
    children: list[ui.UINode] = []
    if conns:
        children.extend(_connection_rows(conns))
    else:
        children.append(_connect_form())
        children.append(_help_modal())
    children.append(_settings_button())
    return ui.Stack(direction="v", gap=3, children=children)
