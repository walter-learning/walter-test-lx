# Contrat des scénarios de relance

Ce document fixe le **contrat** entre le métier (qui édite la donnée) et le moteur (qui l’exécute).  
Le stockage est fourni en **YAML** pour le test technique ; en production un autre applicatif (UI, GitOps, etc.) alimente généralement le même schéma.

## Schéma

- Défini implicitement par les modèles Pydantic (`Scenario`, `Checkpoint`, `Profile`, `GlobalRules`… dans `walter_relance/models.py`).
- `extra=forbid` : toute clé inconnue est rejetée à la désérialisation.
- `schema_version` (racine du document) : incrémente quand **la forme du schéma** change (nouveaux champs obligatoires, renommage).
- `version` + `scenario_id` : version **du contenu** d’un même scénario logique (`cpf-standard` v3 puis v4, etc.).

## Identifiants stables

| ID | Signification |
|----|----------------|
| `scenario_id` | Clé fonctionnelle (ex: `cpf-standard`). Ne change pas quand `version` augmente pour le même produit métier ; utiliser une nouvelle valeur si rupture (« nouveau produit »). |
| `checkpoint_id` | Marque une étape temporelle (ex: `cp_25`). Une fois publié, éviter de recycler le même nom pour une autre sémantique. |
| `profile_id` | Segment d’audience sous un checkpoint (ex: `profile_inactive`). Idem stabilité. |
| `template_id` | Référence un template managé hors scénario (Brevo, etc.) ; le fichier YAML ne transporte pas le HTML. |

## Versionnement

1. Publication d’une nouvelle **`version`** de scénario = snapshot lisible audit (qui, quand, quoi).
2. Le moteur embarque la version qu’il exécute (à discuter en architecture : payload SQS, en-tête, table de jointure).
3. **Rollback** = republier une version antérieure valide après validation.

Le métier utilise un autre outil pour éditer—ton job ici est de **consommer** ce schéma proprement, pas de simuler cette UI.

## Calcul du métier (pour `evaluate`)

### Progression temporelle de session

- **`d_ecoules`** : nombre de jours civils entre `session.starting_date` (inclus) et `now.date()` (comparaison sur des **dates** simples pour le test).
- **`duree_calendaire`** : `(session.ending_date - session.starting_date).days` (fenêtre de session en jours).
- **`session_progress`** entre 0 et 1 :

```text
session_progress = min(1, max(0, d_ecoules / duree_calendaire))
```

### Checkpoint courant

On sélectionne le checkpoint dont le champ **`at_session_progress`** est le **plus grand** tout en restant **atteint ou dépassé** par `session_progress` (en pratique : prendre le dernier checkpoint tel que `session_progress >= at_session_progress - eps`, avec `eps` très petit, ex. `1e-9`).  
Sans checkpoint éligible, liste d’actions vide.

### Ratio de retard (niveau LMS vs attente sous ce checkpoint)

**Durée totale** de formation prévue en secondes :

```text
T_total = session.product_duration_h * 3600
```

**Fraction du parcours réellement suivie** (plafonnée à 1) :

```text
f_reel = min(1, progress.session_time_sec / T_total)
```

Sous un checkpoint avec seuil **`alpha`** = `at_session_progress` du checkpoint courant, le **ratio de retard** utilisé pour les profils `when_progress_ratio` est :

```text
si alpha = 0      -> r = 0
sinon             -> r = f_reel / alpha
```

Un profil défini par `(range_start, range_end)` sur `when_progress_ratio` **matche** si `range_start < r <= range_end`. Si `range_start` est **`null`**, il n’y a pas de limite basse (tout `r` assez petit est accepté côté bas) ; si `range_end` est **`null`**, pas de limite haute — même idée que des bornes « ouvertes à l’infini » sans utiliser de symboles mathématiques dans le code.

### Opt-out

Si `preferences.opt_out_per_channel[channel]` est vrai, **aucune** `PlannedAction` pour ce canal (peu importe le template).

### Déduplication

Pour chaque canal, regarder `last_actions` dans la fenêtre `dedupe_window_days_per_channel[channel]` **en jours calendaires** avant `now`.  
Si une action identique (même `scenario_id`, `checkpoint_id`, `channel`, `template_id`) existe déjà, ne pas replanifier.

### Clé d’idempotence HTTP (orchestrateur)

Proposition de convention (à respecter pour que les tests d’intégration passent) :

```
{scenario_id}|v{version}|{checkpoint_id}|{channel}|{template_id}|{student_id}|{scheduled_at_bucket}
```

`scheduled_at_bucket` peut être la date ISO du jour planifié si relance journalière.

## Dimanche

Si le jour de `scheduled_at` est un dimanche et le canal est listé dans `no_sunday_for_channels`, reporter au lundi suivant (même heure), sauf règle métier plus fine discutée au debrief.
