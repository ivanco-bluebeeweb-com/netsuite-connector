# NetSuite Connector — IDEAL_ONBOARDING

The user's first 5 minutes, judged step by step.

## What the user has

A NetSuite account id (e.g. `1234567`, or `1234567_SB1` for sandbox) and a
TBA credential set created inside NetSuite itself: consumer key/secret
(Integration record) + token key/secret (Access Token). Four values the
user already knows how to get — the app explains the exact NetSuite menu
path in the help modal.

## Happy path

1. User opens the app → left sidebar shows a connect form: Label, Account ID,
   Consumer Key, Consumer Secret, Token Key, Token Secret.
2. "How do I set this up?" → modal: Setup > Integration > Manage Integrations
   > New (enable Token-Based Authentication, copy consumer pair) → Setup >
   Users/Roles > Access Tokens > New (pick the integration + a user + a role,
   copy token pair). Explains that role permissions decide what reads/writes
   succeed later.
3. Pastes the five values, submits → we verify LIVE: sign a request to
   `metadata-catalog/customer` with their TBA credentials before saving
   anything. Bad signature/permissions = clear error, nothing stored.
4. Saved connection appears with masked keys.
5. From chat: "list NetSuite customers" / "get sales order 1042" /
   "run SuiteQL SELECT id, trandate, total FROM transaction" → works
   immediately.

## Failure handling

- Wrong consumer/token pair → `NS_AUTH_FAILED` at verify time, nothing saved,
  message says which pair to re-check.
- Valid signature but role lacks a permission on an action → `NS_FORBIDDEN`
  with NetSuite's own message — never fabricated data.
- No connection saved → every tool answers `NS_NO_CONNECTION` and names
  connect_netsuite as the next step.

## Trust rules

- The four secrets live only in the app's secret slot (`netsuite_connections`);
  panels show masked forms, never values.
- Signatures are computed per-request in-process; nothing is persisted beyond
  the stored credentials.
- Disconnect deletes only the saved record in Imperal; the TBA token can be
  revoked in NetSuite (Setup > Users/Roles > Access Tokens) anytime.
