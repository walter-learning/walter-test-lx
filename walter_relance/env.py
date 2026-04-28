"""Charge le fichier `.env` à la racine du dépôt."""

from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent


def load_repo_dotenv() -> None:
    """Lit `.env` à la racine du repo. Ne remplace pas les variables déjà définies dans l'environnement."""
    _ = load_dotenv(_REPO_ROOT / ".env")
