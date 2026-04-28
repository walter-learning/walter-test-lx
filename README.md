# Test technique — Moteur de relance apprenants (~1 h)

Contexte : une plateforme pédagogique suit des formations LMS et doit **relancer** les personnes qui décrochent, sur trois canaux au même niveau fonctionnel : **email**, **SMS** et **appel**. Ici le canal « appel » est traité comme n’importe quel autre envoi : aucune logique d’agents, de file téléphonique ni de prédictif de dialing dans ce dépôt.

## Ce que vous devez livrer

1. **`evaluate(...)` dans `engine.py`** — fonction **pure**, sans appel réseau ni fichier, qui renvoie une liste de `PlannedAction` selon les règles décrites ci-dessous.
2. **`process_student(student_id, scenario_id)` dans `orchestrator.py`** — assemblage qui interroge le LMS mock en HTTP, charge le scénario métier YAML, puis envoie les actions prévues via **`POST /channels/<email|sms|call>`** avec le header **`Idempotency-Key`**.

Les règles de calcul (ratio de retard, checkpoints, fenêtres de dédoublonnage par canal, cas limit temporels) sont détaillées dans [`config/CONTRACT.md`](config/CONTRACT.md).

Un exemple de scénario produit : [`config/cpf_standard.yaml`](config/cpf_standard.yaml).

---

## Prérequis

- **Python ≥ 3.11** (voir [`pyproject.toml`](pyproject.toml)).
- Une **URL de base** vers l’API mock fournie avec l’exercice (variable d’environnement ci-dessous). Si vous développez hors ligne, adaptez le pointage ou mock les appels pour les parties qui vous en ont besoin.

Dupliquez `.env.example` vers `.env` et renseignez :

```dotenv
MOCK_API_BASE_URL=https://votre-endpoint-de-mock.example.com
```

---

## Installation et tests

### Avec `uv`

```bash
uv sync --extra dev
cp .env.example .env && $EDITOR .env
uv run pytest
```

### Avec un venv classique

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env && $EDITOR .env
pytest
```

`pytest` applique automatiquement le `pythonpath` défini dans le projet : les imports sous `src/walter_relance` sont disponibles depuis la racine.

Au départ, **plusieurs tests échouent** tant que `evaluate` et `process_student` ne sont pas implémentés — c’est attendu : les faire passer fait partie du travail.

---

## Mock HTTP — références utiles

| Méthode + chemin | Rôle |
|------------------|------|
| `GET /lms/students/{id}` | Données apprenant côté LMS |
| `GET /lms/students/{id}/progress` | Progression (temps visionné, validation, …) |
| `GET /lms/sessions/{id}` | Fenêtre temporelle de session et durée prévue |
| `GET /lms/students/{id}/preferences` | Opt-out par canal, fuseau, … |
| `POST /channels/email` | Envoi templatisé avec `Idempotency-Key` |
| `POST /channels/sms` | Idem |
| `POST /channels/call` | Idem (même modèle générique) |
| `GET /channels/deliveries?student_id=…` | Journalisation côté mock des envois enregistrés |

En option pour stresser vos client HTTP ou simuler du bruit : **`?fail_rate=0.xx`** et **`?latency_ms=NNN`** peuvent être ajoutés en query-string sur ces routes selon les capacités exposées par le mock dont vous disposez.

Corps commun attendu pour les trois `POST` :

```json
{
  "to": "<identifiant_visé>",
  "template_id": "...",
  "params": {},
  "scheduled_at": null
}
```

---

## Arborescence

```
config/
  CONTRACT.md                 # À lire en premier pour implémenter evaluate
  cpf_standard.yaml           # Jeu exemple CPF — cohérent avec ScenarioRepository
src/walter_relance/
  models.py                   # Modèles fixes — évitez d’en modifier les signatures tant que l’exercice utilise ces types
  engine.py                   # À compléter — cœur métier pur
  orchestrator.py             # À compléter — glue HTTP + repos
  clients/lms.py              # Client LMS (httpx), fourni
  clients/channels.py         # Emails/SMS/Appels sous un même pattern, fourni
  repositories/
    scenario_repository.py    # Lecture YAML depuis config/
    action_log_repository.py  # Implémentation mémoire locale des logs d’actions
tests/
  test_engine.py              # Assertions sur evaluate
  test_orchestrator.py        # Chaîne LMS → canaux
```

Les modules **`lms`** et **`channels`** visent une utilisation contre le mock ci-dessus ; ils comportent timeouts et retries volontairement rudimentaires si vous souhaitez les renforcer ensuite.

---

## Hors périmètre du dépôt

Pas de Dockerfile, pas d’infra asynchrone réelle type SQS / Dynamo « prod  », pas d’UI métier : l’enjeu est un code compact et vérifiable en local sous la contrainte de temps.

Une bonne découpe : garder **`evaluate`** entièrement testable hors réseau, et limiter **`process_student`** à la lecture LMS, au chargement de scénario et aux appels canal.
