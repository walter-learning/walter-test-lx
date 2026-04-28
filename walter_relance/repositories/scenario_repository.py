from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from walter_relance.models import Scenario


class ScenarioRepository(ABC):
    """Contrat permettant de brancher un store distant ( DynamoDB , Git, Postgres ) derrière."""

    @abstractmethod
    def get(self, scenario_id: str, version: int | None = None) -> Scenario:
        """Retourne le scénario validé."""

        raise NotImplementedError


class YamlScenarioRepository(ScenarioRepository):
    """
    Lecture depuis des fichiers YAML versionnés.

    Pour ce test technique, les fichiers sont fournis sous ``config/*.yaml``.
    En production le métier édite via une UI séparée : le store physique et les chemins de
    déploiement font l'objet de la discussion d'architecture (debriefer).
    """

    def __init__(self, config_dir: Path) -> None:
        self._dir = config_dir.resolve()

    def filename_for(self, scenario_id: str) -> str:
        slug = scenario_id.replace("-", "_")
        return f"{slug}.yaml"

    def get(self, scenario_id: str, version: int | None = None) -> Scenario:
        path = self._dir / self.filename_for(scenario_id)
        if not path.is_file():
            raise FileNotFoundError(f"Aucun scénario YAML pour {scenario_id} ({path})")
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return Scenario.model_validate(raw)
