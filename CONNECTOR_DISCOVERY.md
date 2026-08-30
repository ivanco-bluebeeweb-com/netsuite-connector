# NetSuite Connector — CONNECTOR_DISCOVERY

Researched 2026-08-30 against Oracle's public documentation at
docs.oracle.com/en/cloud/saas/netsuite/ns-online-help (verified live this
session: SuiteTalk REST Web Services API Guide book_1559132836, Overview
chapter_1540391670, OAuth 2.0 for REST Web Services section_157780312610,
REST URL Schema section_1546938065, OpenAPI 3.0 metadata section_1545126526,
Sales Order section_159665260887). Task #2686.

## Confirmed public surface

API host (account-scoped, per the official URL schema doc):
`https://{account_id}.suitetalk.api.netsuite.com/services/rest`

- `record/v1/{recordType}/{id}` — CRUD on ANY NetSuite record type
  (customer, vendor, salesorder, invoice, cashsale, item, employee, contact,
  purchaseorder, ... hundreds of types; one generic passthrough covers all).
- `query/v1/suiteql` — POST SuiteQL SELECT queries (SQL-92-like read path,
  the most powerful read surface; supports joins, paging via limit/offset).
- `record/v1/metadata-catalog/{recordType}` — field-level schema of a record
  type (which fields exist, types, required) — read before writing records.

## Authentication (two documented paths)

1. **TBA — Token-Based Authentication (OAuth 1.0a HMAC-SHA256)** — the
   standard BYOK path for SuiteTalk REST. User creates an Integration record
   (Setup > Integration > Manage Integrations) → consumer key/secret, then a
   TBA Access Token (Setup > Users/Roles > Access Tokens) → token key/secret.
   Four values + account id (realm). Long-lived, revocable per-token. **This
   connector implements TBA** — signed requests with oauth_nonce/oauth_timestamp/
   oauth_signature (HMAC-SHA256, base string per RFC 5849), realm = account id.
2. OAuth 2.0 Client Credentials (certificate-based M2M, requires uploading a
   public certificate into NetSuite) — documented but heavier to onboard;
   explicitly deferred as a v0.2 candidate.

Account id format: numeric, e.g. `1234567`; sandbox accounts end in `_SB1`.
The connector normalizes it (lowercase for realm, keeps case for the host).

## Rate limits / errors

NetSuite enforces per-account concurrency (429 with retry guidance) and
standard 4xx shapes: 401 invalid signature/token (NS_AUTH_FAILED),
403 insufficient permission (NS_FORBIDDEN), 404 unknown record
(NS_NOT_FOUND), 400 validation (NS_VALIDATION), 429 (NS_RATE_LIMITED),
5xx (NS_UPSTREAM). Bounded retry with jitter on 429/5xx only.

## Known limitations (stated honestly)

- Write operations depend on the user's role permissions in NetSuite — a 403
  means the TBA role lacks the permission, not that the endpoint is wrong.
- SuiteQL is read-only (SELECT); writes go through record/v1.
- Some record types are script-only (no REST exposure); metadata-catalog
  answers 404 for those — surfaced as NS_NOT_FOUND with a clear message.
