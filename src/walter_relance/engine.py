from datetime import datetime

from walter_relance.models import ActionLog, PlannedAction, Preferences, Progress, Scenario, Session, Student


def evaluate(
    student: Student,
    progress: Progress,
    session: Session,
    preferences: Preferences,
    scenario: Scenario,
    last_actions: list[ActionLog],
    now: datetime,
) -> list[PlannedAction]:
    """
    Fonction pure — aucun I/O.

    Retourne la liste des actions à planifier pour cet instant (scheduled_at >= now
    sauf règles métier — quiet hours, dédup, opt-out).
    """
    raise NotImplementedError(
        "À implémenter pendant le test : "
        "voir config/CONTRACT.md pour le calcul de ratio, les checkpoints et la dédup par canal."
    )
