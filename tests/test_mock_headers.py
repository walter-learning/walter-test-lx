"""Vérifie que les en-têtes mock lisent MOCK_X_API_KEY ou X_API_KEY."""

import pytest

from walter_relance.clients.mock_headers import mock_request_headers


@pytest.fixture
def clear_api_key_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MOCK_X_API_KEY", raising=False)
    monkeypatch.delenv("X_API_KEY", raising=False)


def test_no_key_returns_empty_headers(clear_api_key_env: None) -> None:
    assert mock_request_headers() == {}


def test_mock_x_api_key_sets_header(clear_api_key_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK_X_API_KEY", "secret-a")
    assert mock_request_headers() == {"x-api-key": "secret-a"}


def test_x_api_key_fallback_when_mock_unset(clear_api_key_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_API_KEY", "secret-b")
    assert mock_request_headers() == {"x-api-key": "secret-b"}


def test_mock_x_api_key_takes_precedence(clear_api_key_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK_X_API_KEY", "preferred")
    monkeypatch.setenv("X_API_KEY", "ignored")
    assert mock_request_headers() == {"x-api-key": "preferred"}
