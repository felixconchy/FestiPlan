# Note d'architecture — refactorisation de FestiPlan

## 1. Défauts de l'architecture initiale

Le détail est dans [01-diagnostic.md](01-diagnostic.md). En résumé :

- **Règles métier dispersées** : R1 codée à trois endroits ; R2/R3/R5/R6 seulement à la création ; R7 et R8 absentes ; R10 dans un contrôleur HTTP ; R9 uniquement dans Pydantic.
- **Cœur dépendant de la technique** : les services recevaient une `Session` SQLAlchemy, manipulaient les modèles ORM et instanciaient eux‑mêmes repositories et notifications. Des contrôleurs exécutaient des requêtes SQL.
- **Effet secondaire couplé à l'opération** : notification envoyée après le `commit`, son exception transformée en HTTP 500 alors que la modification était enregistrée.
- **Testabilité faible** : impossible de tester une règle sans SQLite ni FastAPI ; les tests ne couvraient que la validation Pydantic.

## 2. Responsabilités des couches

| Couche | Dossier | Responsabilité | Dépend de |
|---|---|---|---|
| Domaine | `app/domain` | concepts, invariants, transitions d'état, événements | rien (Python standard) |
| Application | `app/application` | cas d'utilisation : charger via les ports, appeler le domaine, sauvegarder, déclencher les effets secondaires ; définition des ports | domaine |
| Adaptateurs entrants | `app/adapters/http` | HTTP : routage, format des requêtes (Pydantic), commande → cas d'utilisation, erreurs → codes HTTP | application, domaine (lecture) |
| Adaptateurs sortants | `app/adapters/persistence`, `app/adapters/notifications` | implémenter les ports avec SQLAlchemy / l'envoi simulé ; traduction ORM ↔ domaine | ports, domaine |
| Composition | `app/bootstrap.py`, `app/main.py` | créer les adaptateurs concrets et les injecter (`Container`) | tout |

Règle de dépendance : vérifiable par `grep -r "sqlalchemy\|fastapi" app/domain app/application` → aucun résultat.

## 3. Ports et adaptateurs

| Port | Utilité | Adaptateur de production | Double de test |
|---|---|---|---|
| `FestivalRepository` | charger/sauver l'agrégat festival + concerts **en une transaction** ; retrouver le festival d'un concert | `SqlFestivalRepository` | `InMemoryFestivalRepository` (copies profondes, comme une vraie base) |
| `StageRepository`, `ArtistRepository`, `IncidentRepository` | accès aux autres agrégats | `Sql…Repository` | `InMemory…Repository` |
| `Notifier` | envoyer une notification à partir d'un événement de domaine | `EmailNotifier` (simulé, panne configurable) | `FakeNotifier(fail=…)` |

Ports entrants : les cas d'utilisation eux‑mêmes (`execute(command)`), appelés par les contrôleurs. Les cas d'utilisation ne créent jamais leurs dépendances : elles sont injectées par `Container`.

On n'a pas créé de port « Unit of Work » ni de bus d'événements : un seul agrégat est modifié par opération, la sauvegarde de cet agrégat suffit comme frontière transactionnelle.

## 4. Modèle de domaine

Détail et justification dans [02-modele-domaine.md](02-modele-domaine.md).

- **Entités** : `Festival`, `Concert`, `Stage`, `Artist`, `Incident`.
- **Objets‑valeurs** immuables : `TimeSlot` (R1, chevauchement), `FestivalPeriod` (R6), `Equipment` (R5).
- **Agrégats** : `Festival` est la racine de l'agrégat *planning* contenant ses `Concert` (R2, R3, R7, R8 portent sur l'ensemble des concerts) ; `Stage`, `Artist`, `Incident` sont des agrégats séparés référencés par identifiant.
- **Invariants** : R1/R5/R6 dans les objets‑valeurs, R9/R10 (description) dans les entités, R2/R3/R4/R7/R8 dans l'agrégat `Festival`, existence des références (R4, R10) dans les cas d'utilisation.
- **Événements** : `ConcertRescheduled`, `PublishedConcertRescheduled`, `SchedulePublished` — enregistrés par l'agrégat, transmis seulement après la sauvegarde.

## 5. Correction des trois défauts

### Défaut 1 — chevauchements
Toutes les opérations de programmation (créer, déplacer, déplacer après publication, publier) passent par `Festival._check`, qui applique R4, R5, R6, R2 et R3. La vérification est faite sur une **copie** du concert avec le nouveau créneau : en cas de refus, l'agrégat n'est pas modifié. Conflit → `SchedulingConflict` → **409**.

### Défaut 2 — notification en échec
Décision : **la notification est un effet secondaire ; l'opération métier réussit indépendamment**.
1. L'agrégat est sauvegardé (commit) ;
2. `EventDispatcher` transmet les événements au `Notifier` ; toute exception est interceptée et journalisée ;
3. la réponse est **200** avec `notification_status` = `sent` | `failed` | `none`.

Le client sait donc que la modification est faite et que la notification n'est pas partie. Solution proportionnée : synchrone, sans file d'attente (voir limites).

### Défaut 3 — planning publié
L'état du planning est un `ScheduleStatus` (`preparation` → `published`). Transitions :
- `publish()` n'est autorisée qu'en préparation et seulement si tous les concerts respectent les règles (R8) ; une seconde publication → 409 ;
- en état publié, les opérations ordinaires (programmer, déplacer, annuler) lèvent `ScheduleLocked` → **409** ;
- la **procédure explicite** `POST /concerts/{id}/published-reschedule` exige un **motif**, revérifie toutes les règles, conserve l'état publié et émet `PublishedConcertRescheduled` (notification du public). Elle est refusée sur un planning en préparation.

## 6. Stratégie de tests (79 tests, `pytest`)

| Niveau | Dossier | Contenu | Technique |
|---|---|---|---|
| Domaine (30) | `tests/domain` | créneaux invalides, chevauchements, R4–R10, transitions d'état, événements | Python pur : ni FastAPI ni SQLite (imports techniques uniquement dans les fixtures) |
| Cas d'utilisation (20) | `tests/application` | programmation, déplacement, publication, procédure publiée, incidents, erreurs, appels au notificateur, rien n'est sauvé en cas de refus | repositories en mémoire + `FakeNotifier` |
| Adaptateurs (23) | `tests/adapters` | routes HTTP et codes de statut, aller‑retour domaine ↔ SQLAlchemy, formatage et panne du notificateur | `TestClient` + SQLite temporaire |
| Non‑régression (6) | `tests/regression` | les 3 défauts, par l'API | écrits **avant** la correction en `xfail(strict=True)` (voir historique git), puis débloqués |

## 7. Limites et compromis

- **Notification synchrone sans relance** : une notification échouée est journalisée et signalée, mais pas renvoyée automatiquement. Une *outbox* persistée (événements écrits dans la même transaction, envoyés par un worker) serait l'étape suivante.
- **R3 limitée au festival** : un artiste n'est vérifié que contre les concerts du même festival (frontière de l'agrégat). Vérifier tous les festivals demanderait une requête transverse.
- **Concurrence** : pas de verrou optimiste ; deux déplacements simultanés pourraient chacun passer la vérification. Un numéro de version sur le festival réglerait le problème.
- **Agrégat chargé entièrement** : toutes les opérations chargent tous les concerts du festival ; acceptable pour quelques centaines de concerts.
- **Encapsulation par convention** : Python n'a pas d'attributs privés ; `Concert.slot` ou `Festival.concerts` restent techniquement modifiables depuis l'extérieur. Le code applicatif ne modifie un concert que via les méthodes de `Festival` ; rendre `Concert` immuable compliquerait le mapping ORM sans gain réel ici.
- **Annulation après publication** refusée : seule la procédure de déplacement a été prévue ; une procédure d'annulation publiée serait à ajouter sur le même modèle.
- **Codes HTTP modifiés** : conflits 400 → 409, référence inconnue à la création d'un concert ou d'une scène 400 → 404, planning d'un festival inconnu → 404.
- `alembic.ini` pointe vers un dossier `migrations` absent (déjà le cas initialement) ; le schéma est créé par `create_all` et n'a pas changé.
