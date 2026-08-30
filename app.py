"""Extension declaration, secrets, lifecycle hooks.

WHY BYOK: the user's own NetSuite account data (customers, orders, invoices,
items — any record type) is accessed with their own TBA credentials created
inside NetSuite (Integration record consumer pair + Access Token pair).
Nothing is hosted or proxied by Imperal beyond the signed request itself.

WHY TBA (OAuth 1.0a HMAC-SHA256), CONFIRMED against Oracle's public
SuiteTalk REST Web Services API Guide (book_1559132836) and "OAuth 2.0 for
REST Web Services" (section_157780312610), re-verified live 2026-08-30:
SuiteTalk REST lives at https://{account_id}.suitetalk.api.netsuite.com/
services/rest (record/v1 CRUD on any record type, query/v1/suiteql for
SQL-like reads, record/v1/metadata-catalog for field schemas). TBA is the
standard BYOK path; OAuth 2.0 client-credentials (certificate-based) is
documented as a future v0.2 option.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "netsuite-connector",
    version="0.1.0",
    display_name="NetSuite",
    icon="icon.svg",
    capabilities=["netsuite:read", "netsuite:write"],
    description=(
        "Connect your own Oracle NetSuite account via Token-Based Authentication (consumer + token pairs) "
        "-- CRUD on any record type (customers, sales orders, invoices, items, vendors), SuiteQL queries, "
        "record field schemas, plus ERP health reports."
    ),
)

chat = ChatExtension(ext, tool_name="netsuite")

ext.secret(
    "netsuite_connections", "JSON array of saved NetSuite connections (label + account id + TBA consumer/token pairs).",
    required=False, write_mode="extension", max_bytes=65536, rotation_hint_days=365,
)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report connector health: how many saved connections exist."""
    try:
        import handlers_connection as h
        conns = await h._load_connections(ctx)
        return {"status": "ok", "connections": len(conns)}
    except Exception as exc:  # pragma: no cover
        return {"status": "error", "detail": str(exc)}
