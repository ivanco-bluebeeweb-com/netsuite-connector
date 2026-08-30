# NetSuite Connector — PREPARATION

Follows `NEW_APP_TASK_STANDARD.md`. Task #2686. Discovery is DONE
(CONNECTOR_DISCOVERY.md — Oracle docs verified live 2026-08-30).

## Layout

- `app.py` — Extension decl (`netsuite-connector`), `chat` ChatExtension,
  secret `netsuite_connections`, health check.
- `main.py` — sys.path setup, module-cache purge, imports ext/chat + handlers + panels.
- `netsuite_client.py` — TBA (OAuth 1.0a HMAC-SHA256) signer + request()
  against `{account_id}.suitetalk.api.netsuite.com/services/rest`, typed
  `NetsuiteError`, bounded 429/5xx retry with jitter.
- `schemas.py` — Pydantic params + result models for every tool.
- `handlers_connection.py` — connect (verify via metadata-catalog of
  `customer`), list_connections, disconnect_netsuite, resolve helpers.
- `handlers_records.py` — list_records, get_record, create_record,
  update_record (PATCH), delete_record, get_record_schema — generic over
  record/v1 (any record type; follows QuickBooks/Sage/FreshBooks generic
  passthrough pattern already shipped in this portfolio).
- `handlers_query.py` — run_suiteql (POST query/v1/suiteql, limit/offset).
- `handlers_reports.py` — get_account_overview_report (core record counts +
  token liveness), get_open_sales_orders_report (SuiteQL, sales orders not
  yet fully billed/closed with totals).
- `panels.py` (left sidebar connect form + connections), `panels_settings.py`
  (center slot, disconnect only here), unique `icon.svg` (NetSuite "N" block
  motif, red/orange Oracle gradient — NOT the shared 677-byte icon).
- `imperal.json` via `imperal build`; `tool-prices.json` BEFORE deploy;
  `requirements.txt`, `.gitignore`.

## Tool inventory (13 functions)

Connection: connect_netsuite, list_connections, disconnect_netsuite
Records: list_records, get_record, create_record, update_record,
  delete_record, get_record_schema
Query: run_suiteql
Reports: get_account_overview_report, get_open_sales_orders_report

## Pricing plan (before deploy — standing rule)

0: connect/list_connections/disconnect · 8: list_records/get_record/
get_record_schema · 16: create_record/update_record/run_suiteql ·
24: delete_record + open-sales report · 40: account overview report

## Sequencing

1. Discovery ✅ → PREPARATION ✅ → IDEAL_ONBOARDING → UI_COMPONENT_PLAN
2. Client → schemas → app/main → handlers → panels → icon
3. Validate (0 errors) → build → tool-prices.json → git push (no secrets,
   no __pycache__) → create_app → deploy → save_pricing (verify) →
   submit_for_review → comment + complete #2686
