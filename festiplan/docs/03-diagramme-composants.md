# Diagramme de composants (architecture réelle)

Les flèches représentent les dépendances de code (`import`). Toutes pointent vers le cœur : le domaine ne dépend de rien, l'application ne dépend que du domaine et de ses propres ports.

```mermaid
flowchart TB
    client([Client HTTP / Swagger])

    subgraph IN["Adaptateurs entrants"]
        http["«component»<br/>API HTTP FastAPI<br/>app/adapters/http<br/>contrôleurs · schémas Pydantic · errors.py"]
    end

    boot["«component»<br/>Composition<br/>app/bootstrap.py : Container"]

    subgraph CORE["Hexagone : cœur applicatif"]
        uc(("Cas d'utilisation<br/>execute(commande)"))
        app["«component»<br/>Application<br/>app/application<br/>use_cases · EventDispatcher · ports.py"]
        dom["«component»<br/>Domaine<br/>app/domain<br/>agrégat Festival+Concert · Stage · Artist · Incident<br/>TimeSlot · FestivalPeriod · Equipment · événements"]
        pF(("FestivalRepository"))
        pS(("StageRepository"))
        pA(("ArtistRepository"))
        pI(("IncidentRepository"))
        pN(("Notifier"))
    end

    subgraph OUT["Adaptateurs sortants"]
        sql["«component»<br/>Persistance SQLAlchemy<br/>app/adapters/persistence<br/>SqlFestival/Stage/Artist/IncidentRepository<br/>orm.py · database.py"]
        mail["«component»<br/>Notification<br/>app/adapters/notifications<br/>EmailNotifier (simulé)"]
    end

    db[(SQLite)]

    client -->|HTTP / JSON| http
    http -->|requiert| uc
    app -.->|fournit| uc
    http -->|get_container| boot
    boot -->|instancie et injecte| app
    boot -->|instancie| sql
    boot -->|instancie| mail
    app -->|utilise| dom
    app -->|requiert| pF
    app -->|requiert| pS
    app -->|requiert| pA
    app -->|requiert| pI
    app -->|requiert| pN
    sql -.->|réalise| pF
    sql -.->|réalise| pS
    sql -.->|réalise| pA
    sql -.->|réalise| pI
    mail -.->|réalise| pN
    sql -->|mappe ORM / domaine| dom
    sql --> db
```

Légende (notation UML) : rectangle `«component»` = composant ; cercle = interface (port) ; flèche pleine « requiert » = interface requise ; flèche pointillée « réalise » = interface fournie / implémentée. Toutes les dépendances pointent vers l'hexagone : `app/domain` et `app/application` n'importent ni FastAPI ni SQLAlchemy.

| Port (contrat, côté cœur) | Adaptateur (implémentation, côté infrastructure) |
|---|---|
| `FestivalRepository` | `SqlFestivalRepository` (charge / sauve l'agrégat festival + concerts en une transaction) |
| `StageRepository` | `SqlStageRepository` |
| `ArtistRepository` | `SqlArtistRepository` |
| `IncidentRepository` | `SqlIncidentRepository` |
| `Notifier` | `EmailNotifier` (envoi simulé, panne simulable par `FESTIPLAN_FAIL_NOTIFICATIONS`) |
| *(tests)* tous les ports | `tests/fakes.py` : implémentations en mémoire + `FakeNotifier` |

**Chemin d'une requête** : HTTP → contrôleur (validation Pydantic, construction d'une *commande*) → cas d'utilisation (obtenu du `Container`) → ports → agrégat du domaine → sauvegarde via le port → `EventDispatcher` → `Notifier` → réponse construite par le contrôleur. Les exceptions métier remontent jusqu'à `errors.py`, seul endroit qui connaît les codes HTTP.
