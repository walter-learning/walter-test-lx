from __future__ import annotations

import time
from urllib.parse import quote

import httpx

from walter_relance.exceptions import LmsError
from walter_relance.models import Preferences, Progress, Session, Student


class LmsClient:
    """
    Client LMS volontairement minimal (timeout, retry naïf).
    Point de discussion au debrief : politique de retry, idempotence lecture, cache.
    """

    def __init__(self, base_url: str, timeout_s: float = 3.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout_s

    def _get(self, path: str) -> dict:
        url = f"{self._base}{path}"
        last_err: Exception | None = None
        for attempt in range(2):
            try:
                r = httpx.get(url, timeout=self._timeout)
                if r.status_code >= 500 and attempt == 0:
                    time.sleep(0.05)
                    continue
                if r.status_code >= 400:
                    raise LmsError(f"LMS {path} -> {r.status_code}: {r.text}")
                return r.json()
            except (httpx.TransportError, httpx.TimeoutException, httpx.HTTPError) as e:
                last_err = e
                if attempt == 0:
                    time.sleep(0.05)
                    continue
                raise LmsError(str(e)) from e
        raise LmsError(str(last_err) if last_err else "LMS unreachable")

    def get_student(self, student_id: str) -> Student:
        sid = quote(student_id, safe="")
        return Student.model_validate(self._get(f"/lms/students/{sid}"))

    def get_progress(self, student_id: str) -> Progress:
        sid = quote(student_id, safe="")
        return Progress.model_validate(self._get(f"/lms/students/{sid}/progress"))

    def get_session(self, session_id: str) -> Session:
        se = quote(session_id, safe="")
        return Session.model_validate(self._get(f"/lms/sessions/{se}"))

    def get_preferences(self, student_id: str) -> Preferences:
        sid = quote(student_id, safe="")
        return Preferences.model_validate(self._get(f"/lms/students/{sid}/preferences"))
