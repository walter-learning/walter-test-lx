# Contrat des scénarios de relance

Ce document fixe le **contrat** entre le métier (qui édite la donnée) et le moteur (qui l’exécute).  
Le stockage est fourni en **YAML** pour le test technique ; en production un autre applicatif (UI, GitOps, etc.) alimente généralement le même schéma.

## Schéma

- Défini implicitement par les modèles Pydantic (`Scenario`, `Checkpoint`, `Profile`, `GlobalRules`… dans `src/walter_relance/models.py`).
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

\[
\text{session\_progress} =
\max\left(0, \min\left(1,\ \frac{d_\text{{écoulés}}}{(date_\text{{fin}} - date_\text{{début}}).days}\right)\right)\right).
\]

Où \(d_\text{{écoulés}}\) est le nombre de jours civils entre `starting_date` (inclus) et `now.date()` (référence date simple pour le test).

### Checkpoint courant

On sélectionne le checkpoint **`at_session_progress`** le plus élevé tel que **`session_progress >= at_session_progress - eps`** avec `eps` très petit (ex: `1e-9`).  
Sans checkpoint éligible, liste d’actions vide.

### Ratio de retard / niveau \( \text{Niveau}(\text{LMS}) vs attente sous ce checkpoint \)

Nombre total de secondes de formation attendue pour terminer :

\[
T_\text{total} = \texttt{product\_duration\_h} \times 3600
.\]

Fraction réellement suivie :

\[
f_\text{réel} = \min\left(1,\ \frac{\texttt{session\_time\_sec}}{T_\text{total}}\right).
\]

Sous un checkpoint \(c\) avec seuil \(\alpha = `at_session_progress`\):

\[
r = 
\begin{cases}
0 & \text{si } \alpha = 0 \\[4pt]
\dfrac{f_\text{réel}}{\alpha} & \text{sinon}
\end{cases}
\]

Un profil \((a,b)\) sur `when_progress_ratio` matche si \((a < r \le b)\) en interprétant `null` comme \(-\infty\) / \(+\infty\) pour les bornes ouvertes — aligné sur la logique « range_start < ratio <= range_end ».

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

## Quiet hours (rappel pour le 6e test — révélé en live)

Entre `global.quiet_hours.from` et `global.quiet_hours.to` (fuseau `tz`), **reporter** `scheduled_at` au prochain créneau autorisé — **pour les trois canaux** de la même façon.

## Dimanche

Si le jour de `scheduled_at` est un dimanche et le canal est listé dans `no_sunday_for_channels`, reporter au lundi suivant (même heure), sauf règle métier plus fine discutée au debrief.
