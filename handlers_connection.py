"""Connection lifecycle: connect (TBA verify via metadata-catalog/customer),
list, disconnect, and shared connection resolution helpers."""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import netsuite_client as nc
from app import chat
from schemas import (
    ConnectNetsuiteParams, ConnectNetsuiteResult, ConnectionIdParams,
    ConnectionList, ConnectionRecord, DeleteResult,
)

_SECRET = "netsuite_connections"


def _mask(value: str) -> str:
    return value[:4] + "…" + value[-4:] if len(value) > 10 else "***"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, conns: list[dict]) -> None:
    await ctx.secrets.set(_SECRET, json.dumps(conns))


async def resolve_connection(ctx, connection_id: str = "") -> dict | None:
    conns = await _load_connections(ctx)
    if not conns:
        return None
    if connection_id:
        return next((c for c in conns if c.get("id") == connection_id), None)
    return conns[0]


async def resolve_or_error(ctx, connection_id: str = ""):
    conn = await resolve_connection(ctx, connection_id)
    if not conn:
        return None, ActionResult.error(
            nc.NS_NO_CONNECTION,
            "No NetSuite connection saved (or unknown connection_id) — run connect_netsuite first.",
        )
    return conn, None


@chat.function(
    "connect_netsuite",
    "Connect an Oracle NetSuite account by saving its account id plus TBA credentials (consumer key/secret "
    "from an Integration record, token key/secret from an Access Token), after verifying them live against "
    "the SuiteTalk REST metadata catalog.",
    action_type="write",
    chain_callable=True,
    data_model=ConnectNetsuiteResult,
    event="netsuite.connection.created",
)
async def connect_netsuite(ctx, params: ConnectNetsuiteParams) -> ActionResult:
    """Verify the TBA credential set, then persist it as a saved connection."""
    conn = {
        "account_id": params.account_id.strip(),
        "consumer_key": params.consumer_key.strip(),
        "consumer_secret": params.consumer_secret.strip(),
        "token_key": params.token_key.strip(),
        "token_secret": params.token_secret.strip(),
    }
    try:
        # Live verify: a signed metadata-catalog read proves the signature chain end-to-end.
        await nc.request(conn, "GET", "/record/v1/metadata-catalog/customer")
    except nc.NetsuiteError as exc:
        return ActionResult.error(
            exc.code,
            f"Could not verify these NetSuite credentials: {exc.message} "
            "(re-check account id, consumer pair and token pair)",
        )
    label = params.label.strip() or f"NetSuite {params.account_id.strip()}"
    conn["id"] = uuid.uuid4().hex[:12]
    conn["label"] = label
    conns = await _load_connections(ctx)
    conns.append(conn)
    await _save_connections(ctx, conns)
    return ActionResult.success(ConnectNetsuiteResult(
        connected=True,
        connection_id=conn["id"],
        label=label,
        message=f"Connected and verified against account {conn['account_id']}.",
    ), summary="Netsuite connected.")


@chat.function(
    "list_connections",
    "List the connected NetSuite accounts — label, account id, masked consumer key. Secret values are never shown.",
    action_type="read",
    chain_callable=True,
    data_model=ConnectionList,
)
async def list_connections(ctx, params: ConnectionIdParams) -> ActionResult:
    """List saved connections with masked credentials only."""
    conns = await _load_connections(ctx)
    items = [
        ConnectionRecord(
            id=c.get("id", ""),
            label=c.get("label", "NetSuite"),
            account_id=c.get("account_id", ""),
            masked_key=_mask(c.get("consumer_key", "")),
        )
        for c in conns
    ]
    return ActionResult.success(ConnectionList(items=items, total=len(items)), summary="Connections listed.")


@chat.function(
    "disconnect_netsuite",
    "Disconnect a NetSuite account: deletes the saved TBA credentials from Imperal. Nothing in NetSuite "
    "itself is changed; the Access Token can be revoked in NetSuite at any time.",
    action_type="destructive",
    chain_callable=True,
    data_model=DeleteResult,
    event="netsuite.connection.deleted",
)
async def disconnect_netsuite(ctx, params: ConnectionIdParams) -> ActionResult:
    """Delete one saved connection record (Imperal side only)."""
    conns = await _load_connections(ctx)
    if not conns:
        return ActionResult.error(nc.NS_NO_CONNECTION, "No NetSuite connections saved.")
    target = params.connection_id or conns[0].get("id", "")
    remaining = [c for c in conns if c.get("id") != target]
    if len(remaining) == len(conns):
        return ActionResult.error(nc.NS_NOT_FOUND, f"No saved connection with id '{target}'.")
    await _save_connections(ctx, remaining)
    return ActionResult.success(DeleteResult(deleted=True, message="Connection removed from Imperal."), summary="Netsuite disconnected.")
