# Test technique — Moteur de relance apprenants (~1 h)

Dans le cadre de l'accompagnement des élèves, on souhaite mettre en place des relances automatiques (email, sms, appel) en fonction de l'avancement de nos élèves au sein de leur parcours de formation.

## Ce que vous devez livrer

1. **`evaluate(...)` dans `engine.py`** — fonction **pure**, sans appel réseau ni fichier, qui renvoie une liste de `PlannedAction` selon les règles décrites ci-dessous.
2. **`process_student(student_id, scenario_id)` dans `orchestrator.py`** — assemblage qui interroge le LMS mock en HTTP, charge le scénario métier YAML, puis envoie les actions prévues via **`POST /channels/<email|sms|call>`** avec le header **`Idempotency-Key`**.

Les règles de calcul (ratio de retard, checkpoints, fenêtres de dédoublonnage par canal, cas limites temporels) sont détaillées dans [`config/CONTRACT.md`](config/CONTRACT.md).

Un exemple de scénario produit : [`config/cpf_standard.yaml`](config/cpf_standard.yaml).

**Contraintes importantes :**

- Ne modifiez pas les signatures publiques ni la forme des modèles Pydantic dans `models.py` sans accord explicite (les tests s’appuient dessus).
- Le moteur (`evaluate`) reste **déterministe et testable** : pas d’I/O, pas d’horloge implicite — l’instant courant est passé en argument `now`.
- Pour l’orchestrateur, réutilisez les clients fournis (`clients/lms.py`, `clients/channels.py`) et les dépôs (`repositories/`) plutôt que de dupliquer la logique HTTP.

---

## Par où commencer (ordre suggéré)

1. Lire [`config/CONTRACT.md`](config/CONTRACT.md) et parcourir [`config/cpf_standard.yaml`](config/cpf_standard.yaml) pour comprendre checkpoints, profils et règles globales.
2. Parcourir [`walter_relance/models.py`](walter_relance/models.py) pour connaître les types (`Scenario`, `PlannedAction`, `ActionLog`, etc.).
3. Implémenter **`evaluate`** dans [`walter_relance/engine.py`](walter_relance/engine.py) jusqu’à ce que **`tests/test_engine.py`** soit entièrement vert.
4. Implémenter **`process_student`** dans [`walter_relance/orchestrator.py`](walter_relance/orchestrator.py) jusqu’à ce que **`tests/test_orchestrator.py`** passe (consultez ce fichier pour le comportement et les évolutions prévues, par ex. vérifications `respx`).
5. Vérifier manuellement contre le mock fourni (URL et clé dans votre `.env`) si besoin.

---

## Prérequis

- **Python ≥ 3.11** (voir [`pyproject.toml`](pyproject.toml)).
- Une **URL de base** vers l’API mock fournie avec l’exercice. Si le mock exige une authentification, renseignez aussi la clé (voir ci-dessous).

### Fichier d’environnement

Dupliquez `.env.example` vers `.env` et adaptez les valeurs :

```dotenv
MOCK_API_BASE_URL=https://votre-endpoint-de-mock.example.com
MOCK_X_API_KEY=
```

Le fichier **`.env` à la racine du dépôt** est chargé automatiquement au premier import du paquet `walter_relance` (`python-dotenv`, voir [`walter_relance/env.py`](walter_relance/env.py)). Les clients HTTP lisent ensuite ces variables via `os.environ`. Les variables **déjà définies dans le shell** (`export …`) restent prioritaires et ne sont pas écrasées.

---

## Installation

### Avec `uv`

```bash
cd /chemin/vers/walter-test-lx
uv sync --extra dev
cp .env.example .env
# éditer .env (URL du mock, clé si besoin)
```

### Avec un environnement virtuel classique

```bash
cd /chemin/vers/walter-test-lx
python3.11 -m venv .venv
source .venv/bin/activate   # sous Windows : .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
# éditer .env
```

---

## Commandes utiles

Remplacez `uv run` par l’activation du venv et l’appel direct (`pytest`, `ruff`) si vous n’utilisez pas `uv`.

| Action | Commande |
|--------|----------|
| Installer les dépendances (dev inclus) | `uv sync --extra dev` |
| Lancer **tous** les tests | `uv run pytest` |
| Lancer un fichier de tests | `uv run pytest tests/test_engine.py` |
| Lancer un test précis (nom ou ligne) | `uv run pytest tests/test_engine.py::test_on_track_student_gets_no_action` |
| Mode verbeux / arrêt au premier échec | `uv run pytest -v` ou `uv run pytest -x` |
| Afficher les prints | `uv run pytest -s` |
| Lint (optionnel) | `uv run ruff check walter_relance tests` |
| Formatter / fix auto (optionnel) | `uv run ruff check --fix walter_relance tests` |
| Appels HTTP **réels** vers le mock avec logs détaillés | `uv run walter-relance-live <student_id>` (voir ci-dessous) |

Variables d’environnement **pour une seule commande** (ex. clé API sans éditer `.env`) :

```bash
export MOCK_API_BASE_URL="https://…"
export MOCK_X_API_KEY="…"   # ou X_API_KEY
uv run pytest
```

`pytest` lit le `pythonpath` du projet (`pyproject.toml`) : le paquet `walter_relance` à la racine du dépôt est importable sans réglage supplémentaire.

### Exécution contre le mock (HTTP réel)

La console de commandes **`walter-relance-live`** enchaîne des **GET LMS** contre `MOCK_API_BASE_URL` (et lit `.env` comme le reste du paquet) et affiche dans la console chaque **requête** (méthode, URL, en-têtes avec `x-api-key` masqué, corps si présent) et chaque **réponse** (code, corps).

```bash
# .env doit contenir MOCK_API_BASE_URL (et MOCK_X_API_KEY / X_API_KEY si le mock l’exige)
uv sync --extra dev
uv run walter-relance-live student-test-validated
uv run walter-relance-live student-test-inactive-at-25
```

Ensuite un appel **`process_student`** est tenté (sauf avec `--skip-process`) : tant que l’orchestrateur reste squelette (`NotImplementedError`), seule la partie **smoke LMS** produit du trafic HTTP détaillé. Une fois `process_student` implémenté avec `LmsClient` / `ChannelsClient` utilisant vos propres instances `httpx.Client`, vos appels suivis devront passer un client configuré comme dans [`walter_relance/http_logging.py`](walter_relance/http_logging.py) + [`walter_relance/run_live.py`](walter_relance/run_live.py) pour conserver ces logs également sur POST `/channels/*`.

### État initial des tests

- `tests/test_mock_headers.py` vérifie les en-têtes HTTP du mock (clé optionnelle) — il peut déjà passer sans implémenter le moteur.
- Les tests de **`test_engine.py`** et **`test_orchestrator.py`** appellent votre code ; ils **échouent** jusqu’à ce que `evaluate` et `process_student` soient implémentés — c’est normal.

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

En option pour stresser vos clients HTTP ou simuler du bruit : **`?fail_rate=0.xx`** et **`?latency_ms=NNN`** peuvent être ajoutés en query-string sur ces routes selon les capacités exposées par le mock dont vous disposez.

**Vérification rapide** (avec `curl`), une fois l’URL et la clé connues :

```bash
curl -sS -H "x-api-key: VOTRE_CLE" "${MOCK_API_BASE_URL}/lms/students/un-id-apprenant"
```

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
walter_relance/
  models.py                   # Modèles fixes — évitez d’en modifier les signatures tant que l’exercice utilise ces types
  engine.py                   # À compléter — cœur métier pur
  orchestrator.py             # À compléter — glue HTTP + repos
  run_live.py                 # CLI ``walter-relance-live`` : smoke HTTP réel contre le mock (logs détaillés)
  env.py                      # Chargement du ``.env`` à la racine
  http_logging.py             # Hooks httpx pour journaliser requêtes/réponses
  clients/lms.py              # Client LMS (httpx), fourni — client HTTP injectable pour les logs live
  clients/channels.py         # Idem pour les POST canaux
  repositories/
    scenario_repository.py    # Lecture YAML depuis config/
    action_log_repository.py  # Implémentation mémoire locale des logs d’actions
tests/
  test_engine.py              # Assertions sur evaluate
  test_orchestrator.py        # Chaîne LMS → canaux
  test_mock_headers.py        # En-têtes x-api-key (mock)
```

Les modules **`lms`** et **`channels`** visent une utilisation contre le mock ci-dessus ; ils comportent timeouts et retries volontairement rudimentaires si vous souhaitez les renforcer ensuite.
