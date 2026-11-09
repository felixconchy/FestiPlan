# FestiPlan — dépôt initial (legacy)

API pédagogique FastAPI de gestion d'un festival metal fictif. Le dépôt est volontairement imparfait : règles métier dispersées, dépendances techniques accessibles depuis plusieurs couches, et effets secondaires couplés aux opérations métier. Il ne doit pas être utilisé en production.

## Fonctionnalités
- Festivals, artistes, scènes et concerts
- Consultation du planning, déplacement et annulation de concerts
- Publication d'un festival et déclaration d'incidents
- Notifications simulées, avec échec configurable

## Installation (Python 3.11+)
```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1 ; macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```
Documentation : http://127.0.0.1:8000/docs
Tests : `pytest`

Par défaut, SQLite crée `festiplan.db` dans le dossier courant. Copier `.env.example` vers `.env` si nécessaire.

## Données
Festival fictif **Hellforge Open Air**, du 18 au 20 juin 2027. Scènes : Mainstage, Warzone, Valley et Temple. Les groupes, horaires et capacités sont inventés ; seule l'ambiance générale est inspirée des festivals metal multi-scènes.

## Scénarios à explorer
1. Déplacer un concert sur un créneau occupé sur la même scène : la validation est incomplète dans le parcours de déplacement.
2. Définir `FESTIPLAN_FAIL_NOTIFICATIONS=true`, déplacer un concert, puis consulter son créneau : l'API peut répondre 500 alors que le déplacement est déjà enregistré.
3. Publier le festival puis déplacer un concert par l'endpoint ordinaire : le statut publié n'est pas protégé.

Le dépôt contient des tests volontairement sommaires de validation. Les scénarios métier ci-dessus ne sont pas couverts complètement au départ : ils sont à investiguer et à sécuriser pendant la refactorisation.
