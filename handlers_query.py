"""SuiteQL tool: read-only SQL-92-like queries via POST query/v1/suiteql."""
from __future__ import annotations

from imperal_sdk import ActionResult

import netsuite_client as nc
from app import chat
from handlers_connection import resolve_or_error
from schemas import RunSuiteqlParams, SuiteqlResult


@chat.function(
    "run_suiteql",
    "Run a SuiteQL SELECT query against NetSuite (query/v1/suiteql) -- the most powerful read path: joins, "
    "filters, aggregates. Read-only; writes go through create_record/update_record. Limit 1-1000 rows.",
    action_type="write", chain_callable=True, data_model=SuiteqlResult,
)
async def run_suiteql(ctx, params: RunSuiteqlParams) -> ActionResult:
    """POST /query/v1/suiteql {q, limit, offset}."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    query = params.query.strip()
    if not query.lower().startswith("select"):
        return ActionResult.error(
            nc.NS_VALIDATION,
            "SuiteQL is read-only: the query must start with SELECT.",
        )
    try:
        data = await nc.request(
            conn, "POST", "/query/v1/suiteql",
            params={"limit": params.limit, "offset": params.offset},
            body={"q": query},
        )
    except nc.NetsuiteError as exc:
        return ActionResult.error(exc.code, exc.message)
    rows = data.get("items") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        rows = []
    total = data.get("totalResults") if isinstance(data, dict) else None
    has_more = bool(isinstance(data, dict) and data.get("hasMore"))
    return ActionResult.success(SuiteqlResult(rows=rows, total=total, has_more=has_more), summary="Suiteql run requested.")
