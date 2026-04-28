"""
Exécute des appels HTTP réels contre le mock (Lambda) avec logs console.

Usage (depuis la racine du repo)::

    uv run walter-relance-live student-integration

ou::

    uv run python -m walter_relance.run_live student-integration
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

import httpx

from walter_relance.clients.lms import LmsClient
from walter_relance.env import load_repo_dotenv
from walter_relance.http_logging import build_http_event_hooks
from walter_relance.orchestrator import process_student


def _configure_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
        force=True,
    )
    return logging.getLogger("walter_relance.live")


def _run_lms_smoke(logger: logging.Logger, base_url: str, student_id: str) -> None:
    hooks = build_http_event_hooks(logger)
    timeout = httpx.Timeout(15.0, connect=10.0)
    with httpx.Client(timeout=timeout, event_hooks=hooks) as http:
        lms = LmsClient(base_url, timeout_s=5.0, http_client=http)
        logger.info("--- Lecture LMS (student → progress → session → préférences) ---")
        student = lms.get_student(student_id)
        prog = lms.get_progress(student_id)
        session = lms.get_session(prog.session_id)
        prefs = lms.get_preferences(student_id)

    summary = {
        "student_id": student.id,
        "session_id_session": session.id,
        "progress_session_id": prog.session_id,
        "validated": prog.validated,
        "session_time_sec": prog.session_time_sec,
        "preferences_tz": prefs.tz,
    }
    logger.info("--- Résumé (JSON) ---\n%s", json.dumps(summary, ensure_ascii=False, indent=2))


def _maybe_process_student(logger: logging.Logger, student_id: str, scenario_id: str) -> None:
    msg = (
        "--- Tentative orchestrateur process_student(%r, %r) "
        "(les appels LMS/canaux après implémentation n’auront ces logs détaillés "
        "que si vous injectez un ``httpx.Client`` avec hooks dans vos clients.) ---"
    )
    logger.info(msg, student_id, scenario_id)
    try:
        result = process_student(student_id, scenario_id)
    except NotImplementedError as e:
        logger.info("Orchestrator : %s", e)
        return
    logger.info("process_student → %s", result)


def main() -> None:
    load_repo_dotenv()
    parser = argparse.ArgumentParser(
        description="Appelle le mock LMS en HTTP avec logs détaillés (requêtes/réponses).",
    )
    parser.add_argument(
        "student_id",
        help="Identifiant apprenant côté mock (ex. student-integration)",
    )
    parser.add_argument(
        "--scenario",
        default="cpf-standard",
        help="scenario_id YAML (défaut: cpf-standard), pour process_student lorsqu’implémenté",
    )
    parser.add_argument(
        "--skip-process",
        action="store_true",
        help="Ne pas appeler process_student à la fin (uniquement le smoke LMS).",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override de MOCK_API_BASE_URL (sinon .env)",
    )
    args = parser.parse_args()
    student_id: str = args.student_id
    scenario_arg: str = args.scenario
    skip_process: bool = args.skip_process
    base_arg: str | None = args.base_url
    logger = _configure_logging()

    base = base_arg
    if not base:
        import os

        base = os.getenv("MOCK_API_BASE_URL", "").strip()
    if not base:
        logger.error(
            "MOCK_API_BASE_URL manquant : définissez-le dans .env ou passez --base-url HTTPS://…",
        )
        sys.exit(1)

    base = base.rstrip("/")

    logger.info(
        "Base mock : %s (clé API masquée dans les journaux si présente)",
        base.split("?", 1)[0],
    )

    try:
        _run_lms_smoke(logger, base, student_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Échec du smoke LMS : %s", exc)
        sys.exit(2)

    if not skip_process:
        try:
            _maybe_process_student(logger, student_id, scenario_arg)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Erreur lors de process_student : %s", exc)
            sys.exit(3)


if __name__ == "__main__":
    main()
