"""En-têtes communs pour les appels vers l'API mock (ex. lambda test_technique)."""
from __future__ import annotations

import os


def mock_request_headers() -> dict[str, str]:
    """Si une clé est définie, renvoie l'en-tête `x-api-key` (aligné avec la Lambda quand son env `X_API_KEY` est posé).

    Ordre : ``MOCK_X_API_KEY``, puis ``X_API_KEY`` (même valeur que pour le déploiement AWS).
    """
    key = (os.getenv("MOCK_X_API_KEY") or os.getenv("X_API_KEY") or "").strip()
    if not key:
        return {}
    return {"x-api-key": key}
