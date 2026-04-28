from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlencode

import httpx

from .mock_headers import mock_request_headers
from walter_relance.exceptions import ChannelError, IdempotencyConflict, RateLimitError
from walter_relance.models import Channel


@dataclass(frozen=True)
class Delivery:
    delivery_id: str
    status: str


class ChannelsClient:
    """Trois canaux (email, sms, call) sous le même contrat HTTP."""

    def __init__(
        self,
        base_url: str,
        timeout_s: float = 5.0,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout_s
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=timeout_s)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> ChannelsClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _channel_path(self, channel: Channel) -> str:
        return f"/channels/{channel}"

    def dispatch(
        self,
        channel: Channel,
        to: str,
        template_id: str,
        params: dict,
        idempotency_key: str,
        scheduled_at: datetime | None = None,
        *,
        chaos: dict[str, str] | None = None,
    ) -> Delivery:
        path = self._channel_path(channel)
        q = chaos or {}
        qs = ("?" + urlencode(q)) if q else ""
        url = f"{self._base}{path}{qs}"
        body = {
            "to": to,
            "template_id": template_id,
            "params": params,
            "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
        }
        headers = {"Idempotency-Key": idempotency_key, **mock_request_headers()}
        r = self._client.post(url, json=body, headers=headers, timeout=self._timeout)
        if r.status_code == 429:
            raise RateLimitError(r.text)
        if r.status_code == 409:
            raise IdempotencyConflict(r.text)
        if r.status_code >= 500:
            raise ChannelError(r.text)
        if r.status_code >= 400:
            raise ChannelError(f"{r.status_code}: {r.text}")
        data = r.json()
        return Delivery(delivery_id=str(data.get("delivery_id", "")), status=str(data.get("status", "")))

    def send_email(
        self,
        to: str,
        template_id: str,
        params: dict,
        idempotency_key: str,
        scheduled_at: datetime | None = None,
    ) -> Delivery:
        return self.dispatch("email", to, template_id, params, idempotency_key, scheduled_at)

    def send_sms(
        self,
        to: str,
        template_id: str,
        params: dict,
        idempotency_key: str,
        scheduled_at: datetime | None = None,
    ) -> Delivery:
        return self.dispatch("sms", to, template_id, params, idempotency_key, scheduled_at)

    def send_call(
        self,
        to: str,
        template_id: str,
        params: dict,
        idempotency_key: str,
        scheduled_at: datetime | None = None,
    ) -> Delivery:
        return self.dispatch("call", to, template_id, params, idempotency_key, scheduled_at)
