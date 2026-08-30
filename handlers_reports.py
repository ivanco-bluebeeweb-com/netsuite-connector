"""Value-add reports: account overview (core record counts + credential
liveness) and open sales orders (SuiteQL-driven), in single calls."""
from __future__ import annotations

from imperal_sdk import ActionResult

import netsuite_client as nc
from app import chat
from handlers_connection import resolve_or_error
from schemas import AccountOverviewReport, OpenSalesOrdersReport, ReportParams

_CORE_TYPES = ("customer", "vendor", "salesorder", "invoice", "item")


@chat.function(
    "get_account_overview_report",
    "Value-add report: one-glance NetSuite account snapshot -- record counts for customers, vendors, sales "
    "orders, invoices and items, plus credential liveness, in a single call.",
    action_type="read", chain_callable=True, data_model=AccountOverviewReport,
)
async def get_account_overview_report(ctx, params: ReportParams) -> ActionResult:
    """Scan core record types and count what's reachable."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    counts: dict[str, int] = {}
    notes: list[str] = []
    for rtype in _CORE_TYPES:
        try:
            data = await nc.request(
                conn, "GET", f"/record/v1/{rtype}", params={"limit": 1},
            )
            total = data.get("totalResults") if isinstance(data, dict) else None
            counts[rtype] = int(total) if isinstance(total, int) else len(data.get("items", []))
        except nc.NetsuiteError as exc:
            counts[rtype] = 0
            notes.append(f"{rtype}: not readable with this role ({exc.code}).")
    if notes:
        notes.append("Zero counts may reflect TBA role permissions, not empty data.")
    return ActionResult.success(AccountOverviewReport(
        label=conn.get("label", "NetSuite"),
        account_id=conn.get("account_id", ""),
        counts=counts,
        notes=notes,
    ))


@chat.function(
    "get_open_sales_orders_report",
    "Value-add report: sales orders not yet fully billed or closed -- id, date, entity, amount, status -- "
    "so fulfillment/billing follow-up is one call away.",
    action_type="read", chain_callable=True, data_model=OpenSalesOrdersReport,
)
async def get_open_sales_orders_report(ctx, params: ReportParams) -> ActionResult:
    """SuiteQL scan of transactions flagged as open sales orders."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    query = (
        "SELECT t.id, t.trandate, e.companyname AS customer, t.total, "
        "s.status AS status FROM transaction t "
        "JOIN entity e ON e.id = t.entity "
        "JOIN transactionstatus s ON s.id = t.status "
        "WHERE t.type = 'SalesOrd' AND s.status IN ('A','B','C','D','E') "
        "ORDER BY t.trandate DESC"
    )
    try:
        data = await nc.request(
            conn, "POST", "/query/v1/suiteql",
            params={"limit": params.scan_limit, "offset": 0},
            body={"q": query},
        )
    except nc.NetsuiteError as exc:
        return ActionResult.error(exc.code, exc.message)
    rows = data.get("items") if isinstance(data, dict) else None
    rows = rows if isinstance(rows, list) else []
    orders = [
        {
            "id": r.get("id"),
            "date": r.get("trandate"),
            "customer": r.get("customer"),
            "total": r.get("total"),
            "status": r.get("status"),
        }
        for r in rows
    ]
    notes = [] if orders else ["No open sales orders found in the scanned window."]
    return ActionResult.success(OpenSalesOrdersReport(
        label=conn.get("label", "NetSuite"),
        scanned=len(rows),
        open_count=len(orders),
        orders=orders,
        notes=notes,
    ))
