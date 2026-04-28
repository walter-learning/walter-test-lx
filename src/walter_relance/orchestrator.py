from __future__ import annotations

import os

from walter_relance.models import ProcessResult
from walter_relance.repositories.action_log_repository import (
    InMemoryActionLogRepository,
)

# Import par défaut pour éviter un constructeur verbeux pendant le live coding.
# Les tests peuvent appeler `reset_action_log_store()` entre cas.
_default_action_log_repository = InMemoryActionLogRepository()


def reset_action_log_store() -> None:
    """Utilitaire pour les tests uniquement."""
    global _default_action_log_repository  # noqa: PLW0603
    _default_action_log_repository = InMemoryActionLogRepository()


def process_student(student_id: str, scenario_id: str) -> ProcessResult:
    """
    1. Fetch student, progress, session, preferences from LMS client
    2. Load scenario from ScenarioRepository
    3. Fetch last_actions from ActionLogRepository
    4. Call engine.evaluate(...)
    5. For each PlannedAction, call channels client with Idempotency-Key
    6. Append successful actions to ActionLogRepository
    """
    raise NotImplementedError(
        "À implémenter pendant le test. Base URL du mock : env MOCK_API_BASE_URL "
        "(voir README.md et clients fournis)."
    )


def _base_url() -> str:
    """Utilisable quand le candidat implémente `process_student`."""
    url = os.getenv("MOCK_API_BASE_URL")
    if not url:
        raise RuntimeError("MOCK_API_BASE_URL non défini (voir .env.example)")
    return url.rstrip("/")
