"""Hooks HTTP pour journaliser les requêtes et réponses (ex. mock Lambda)."""

from __future__ import annotations

import json
import logging

import httpx

_SENSITIVE_HEADERS = frozenset({"authorization", "x-api-key"})


def _redact_headers(headers: httpx.Headers) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in headers.items():
        if k.lower() in _SENSITIVE_HEADERS:
            out[k] = "***"
        else:
            out[k] = v
    return out


def _preview_body(raw: bytes | None, *, max_len: int) -> str:
    if not raw:
        return ""
    text = raw.decode("utf-8", errors="replace")
    if len(text) > max_len:
        return text[:max_len] + f"... (+{len(text) - max_len} car.)"
    return text


def build_http_event_hooks(
    logger: logging.Logger | None = None,
    *,
    preview_max_chars: int = 4000,
) -> dict[str, list]:
    """Construit les ``event_hooks`` à passer à ``httpx.Client`` pour tracer appels/réponses."""
    log = logger or logging.getLogger(__name__)

    def on_request(request: httpx.Request) -> None:
        hdrs = _redact_headers(request.headers)
        body_preview = ""
        try:
            content = request.content
            if content:
                body_preview = _preview_body(content, max_len=min(1200, preview_max_chars))
        except Exception as exc:  # noqa: BLE001
            body_preview = f"<lecture corps impossible: {exc}>"
        log.info(
            "HTTP → %s %s\n  headers=%s%s",
            request.method,
            request.url,
            json.dumps(hdrs, ensure_ascii=False),
            f"\n  body={body_preview}" if body_preview else "",
        )

    def on_response(response: httpx.Response) -> None:
        try:
            response.read()
        except Exception as exc:  # noqa: BLE001
            log.info(
                "HTTP ← %s %s (erreur lecture réponse: %s)",
                response.status_code,
                response.url,
                exc,
            )
            return
        text = ""
        try:
            text = response.text
        except Exception as exc:  # noqa: BLE001
            text = f"<texte inaccessible: {exc}>"
        if len(text) > preview_max_chars:
            text = text[:preview_max_chars] + f"... (tronqué, {len(response.text)} car. au total)"
        log.info("HTTP ← %s %s\n%s", response.status_code, response.url, text)

    return {"request": [on_request], "response": [on_response]}
