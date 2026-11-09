# FestiPlan — version refactorisée (architecture hexagonale + DDD)

API FastAPI de gestion d'un festival metal fictif : festivals, scènes, artistes, programmation des concerts, publication du planning, incidents et notifications simulées.

## Installation (Python 3.11+)

Depuis le dossier `festiplan/` :

```bash
python -m venv .venv
# Windows PowerShell : .venv\Scripts\Activate.ps1
# macOS / Linux      : source .venv/bin/activate
pip install -r requirements.txt
```

Copier `.env.example` vers `.env` si besoin. Variables disponibles :

| Variable | Défaut | Rôle |
|---|---|---|
| `FESTIPLAN_DATABASE_URL` | `sqlite:///./festiplan.db` | base de données |
| `FESTIPLAN_FAIL_NOTIFICATIONS` | `false` | simule une panne du service de notification |

## Initialisation des données

```bash
python -m app.seed
```

⚠ Réinitialise la base configurée (festival fictif **Hellforge Open Air**, 18–20 juin 2027, 4 scènes, 12 artistes, 14 concerts). À utiliser uniquement en développement.

## Lancement

```bash
uvicorn app.main:app --reload
```

Documentation interactive : http://127.0.0.1:8000/docs

## Tests

```bash
pytest
```

| Dossier | Niveau |
|---|---|
| `tests/domain` | règles métier pures (sans FastAPI ni SQLite) |
| `tests/application` | cas d'utilisation avec repositories en mémoire |
| `tests/adapters` | routes HTTP et persistance SQLAlchemy |
| `tests/regression` | non‑régression des 3 défauts initiaux |

## Architecture

```
app/
├── domain/            entités, objets-valeurs, agrégat Festival, événements, erreurs métier
├── application/       ports + cas d'utilisation + EventDispatcher
├── adapters/
│   ├── http/          contrôleurs FastAPI, schémas Pydantic, traduction des erreurs
│   ├── persistence/   ORM, session, repositories SQLAlchemy
│   └── notifications/ EmailNotifier (simulé)
├── bootstrap.py       racine de composition (injection des dépendances)
├── main.py            application FastAPI
└── seed.py            données de démonstration
```

Documentation :
1. [Diagnostic de l'architecture initiale](docs/01-diagnostic.md)
2. [Modèle de domaine (DDD)](docs/02-modele-domaine.md)
3. [Diagramme de composants](docs/03-diagramme-composants.md)
4. [Diagramme de séquence — déplacer un concert](docs/04-diagramme-sequence.md)
5. [Note d'architecture](docs/05-note-architecture.md)

## Comportements métier notables

- **Conflits** (même scène ou même artiste sur des créneaux qui se chevauchent) : `409`.
- **Notification en échec** : l'opération reste réussie (`200`) et la réponse contient `"notification_status": "failed"` ; l'erreur est journalisée.
- **Planning publié** : `PATCH /concerts/{id}/reschedule`, la création et l'annulation renvoient `409`. Pour modifier un concert publié, utiliser la procédure explicite :

```http
POST /concerts/{id}/published-reschedule
{"start_time": "2027-06-18T21:00:00", "end_time": "2027-06-18T22:00:00", "reason": "Retard du groupe"}
```

- **Publication** : refusée (`409`/`400`) si un concert viole une règle de programmation ou si le planning est déjà publié.
