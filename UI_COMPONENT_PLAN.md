# NetSuite Connector — UI_COMPONENT_PLAN

Per `~/UI_INTERFACE_STANDARD.md` + `concepts/panels.md`. Written BEFORE
panels.py (per NEW_APP_TASK_STANDARD).

## Left sidebar (`panels.py`, slot left, entry `netsuite_connect`)

- Connect form (only when nothing is connected yet):
  - Label input — label "Label", placeholder "e.g. Acme production ERP".
  - Account ID input — label "Account ID", placeholder "e.g. 1234567 or 1234567_SB1".
  - Consumer Key / Consumer Secret / Token Key / Token Secret inputs —
    each with its own visible label and contextual placeholder
    ("From the Integration record" / "From the Access Token page").
  - Form stretched full sidebar width; content stretched inside it.
  - Submit via `submit_label` (DUI-correct).
- "How do I set this up?" ghost button → Modal with the two-step NetSuite
  TBA setup (Integration record → Access Token) + role-permission note.
  Instructions live ONLY in the modal.
- Connected state: list of saved connections (label + account id + masked
  consumer key), separated by dividers.
- "App settings" secondary button, ALWAYS the last element.

## Center slot (`panels_settings.py`, entry `netsuite_settings`)

- Saved connections with masked metadata.
- Disconnect per connection — HERE ONLY, via ui.Form
  `defaults={"connection_id": ...}` (DUI-correct).

## Secrets panel

- Standard `netsuite_secrets` panel (right slot) — values never echoed.

## Icon

- Unique `icon.svg`: rounded-square, Oracle red→orange gradient, bold "N"
  built from two diagonal blocks with a small data-grid accent. NOT the
  shared 677-byte icon.
