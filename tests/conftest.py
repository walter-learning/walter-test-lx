from pathlib import Path

import pytest

from walter_relance.repositories.scenario_repository import YamlScenarioRepository


@pytest.fixture
def scenario_repo() -> YamlScenarioRepository:
    root = Path(__file__).resolve().parent.parent
    return YamlScenarioRepository(root / "config")


@pytest.fixture
def scenario_cpf(scenario_repo: YamlScenarioRepository):
    return scenario_repo.get("cpf-standard")

