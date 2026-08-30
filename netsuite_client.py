"""NetSuite SuiteTalk REST client: TBA (OAuth 1.0a HMAC-SHA256) signing against
{account_id}.suitetalk.api.netsuite.com/services/rest, typed errors, bounded
429/5xx retry with jitter (same retry pattern as the session's other connectors)."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import random
import time
import urllib.parse
import uuid
from typing import Any

import httpx

# App-declared structured error codes (V32)
NS_AUTH_FAILED = "NS_AUTH_FAILED"
NS_FORBIDDEN = "NS_FORBIDDEN"
NS_NOT_FOUND = "NS_NOT_FOUND"
NS_RATE_LIMITED = "NS_RATE_LIMITED"
NS_UPSTREAM = "NS_UPSTREAM"
NS_VALIDATION = "NS_VALIDATION"
NS_NO_CONNECTION = "NS_NO_CONNECTION"
NS_UNEXPECTED = "NS_UNEXPECTED"

_MAX_ATTEMPTS = 4
_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class NetsuiteError(Exception):
    """Typed upstream failure; handlers convert it to ActionResult.error."""

    def __init__(self, code: str, message: str, status: int = 0) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _err(code: str, message: str, status: int = 0) -> NetsuiteError:
    return NetsuiteError(code, message, status)


def _code_for(status: int) -> str:
    if status == 401:
        return NS_AUTH_FAILED
    if status == 403:
        return NS_FORBIDDEN
    if status == 404:
        return NS_NOT_FOUND
    if status == 429:
        return NS_RATE_LIMITED
    if status >= 500:
        return NS_UPSTREAM
    return NS_VALIDATION


def _message_from(body: Any, status: int) -> str:
    if isinstance(body, dict):
        details = body.get("o:errorDetails")
        if isinstance(details, list) and details:
            msgs = [d.get("message") or d.get("detail") for d in details if isinstance(d, dict)]
            msgs = [m for m in msgs if m]
            if msgs:
                return "; ".join(msgs)[:400]
        for key in ("message", "detail", "error", "title"):
            val = body.get(key)
            if isinstance(val, str) and val.strip():
                return val[:400]
    return f"NetSuite API error (HTTP {status})"


def _base_url(conn: dict) -> str:
    account = (conn.get("account_id") or "").strip().replace("_", "-").lower()
    return f"https://{account}.suitetalk.api.netsuite.com/services/rest"


def _pct(value: str) -> str:
    return urllib.parse.quote(value, safe="~-._")


def _auth_header(conn: dict, method: str, url: str, query: dict) -> str:
    """Build the OAuth 1.0a Authorization header (HMAC-SHA256, TBA-style)."""
    oauth = {
        "oauth_consumer_key": conn["consumer_key"],
        "oauth_token": conn["token_key"],
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_timestamp": str(int(time.time())),
        "oauth_signature_method": "HMAC-SHA256",
        "oauth_version": "1.0",
    }
    # Signature base string params = oauth params + query string params.
    all_params = {**{k: str(v) for k, v in (query or {}).items()}, **oauth}
    param_str = "&".join(f"{_pct(k)}={_pct(all_params[k])}" for k in sorted(all_params))
    base_string = "&".join([method.upper(), _pct(url), _pct(param_str)])
    signing_key = f"{_pct(conn['consumer_secret'])}&{_pct(conn['token_secret'])}"
    digest = hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha256).digest()
    oauth["oauth_signature"] = base64.b64encode(digest).decode()

    realm = (conn.get("account_id") or "").strip().upper()
    pairs = ", ".join(f'{k}="{_pct(v)}"' for k, v in sorted(oauth.items()))
    return f'OAuth realm="{_pct(realm)}", {pairs}'


async def request(
    conn: dict,
    method: str,
    path: str,
    *,
    params: dict | None = None,
    body: dict | None = None,
) -> Any:
    """Signed request with bounded retry on 429/5xx; raises NetsuiteError."""
    base = _base_url(conn)
    url = f"{base}{path}"
    query = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    headers_base = {"Accept": "application/json"}
    if body is not None:
        headers_base["Content-Type"] = "application/json"

    for attempt in range(_MAX_ATTEMPTS):
        headers = {**headers_base, "Authorization": _auth_header(conn, method, url, query)}
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.request(method, url, params=query, json=body, headers=headers)
        except httpx.TimeoutException:
            if attempt == _MAX_ATTEMPTS - 1:
                raise _err(NS_UPSTREAM, "NetSuite API timed out")
        except httpx.HTTPError as exc:
            raise _err(NS_UNEXPECTED, f"HTTP transport error: {exc}")
        else:
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < _MAX_ATTEMPTS - 1:
                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else min(2 ** attempt, 8)
                await asyncio.sleep(delay + random.uniform(0, 0.4))
                continue
            if resp.status_code == 204:
                return {}
            try:
                data = resp.json()
            except ValueError:
                data = {"raw": resp.text[:2000]}
            if resp.status_code >= 400:
                raise _err(_code_for(resp.status_code), _message_from(data, resp.status_code), resp.status_code)
            return data
    raise _err(NS_UPSTREAM, "NetSuite API failed after retries")
