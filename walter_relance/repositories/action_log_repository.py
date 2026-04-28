from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from walter_relance.models import ActionLog


class ActionLogRepository(ABC):
    @abstractmethod
    def find_for_student(self, student_id: str, since: datetime) -> list[ActionLog]:
        raise NotImplementedError

    @abstractmethod
    def append(self, log: ActionLog) -> None:
        raise NotImplementedError


class InMemoryActionLogRepository(ActionLogRepository):
    """Implémentation simple pour le live coding — non persistante."""

    def __init__(self) -> None:
        self._items: list[ActionLog] = []

    def find_for_student(self, student_id: str, since: datetime) -> list[ActionLog]:
        return [a for a in self._items if a.student_id == student_id and a.sent_at >= since]

    def append(self, log: ActionLog) -> None:
        self._items.append(log)

    def clear(self) -> None:
        self._items.clear()
