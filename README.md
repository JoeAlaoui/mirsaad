# MIRSAAD — مرصاد

Plateforme de pilotage et de visibilité du portefeuille des services SI.

Statut actuel : **V0.3** — SPA, design modernisé avec graphiques, organisation entièrement configurable.

## Nouveautés V0.7

- **Import** (`/#/importer`) : JSON natif MIRSAAD (fidélité totale) ou Excel simplifié à plat
  (`services/import_export.py` — colonnes `EXCEL_COLUMNS`). Aperçu obligatoire avant toute
  écriture : nouveaux / modifiés / inchangés / doublons dans le fichier / erreurs. Trois
  stratégies au choix : **remplacer** (écrase tout), **ajouter** (ignore les ID déjà présents),
  **mise à jour par ID** (upsert, recommandé). Aucun écrasement silencieux — confirmation
  explicite requise, backup automatique créé avant l'écriture.
- **Export** (`/#/exporter`) : fichier Excel professionnel (feuille Synthèse + Inventaire,
  en-têtes stylés, volets figés, filtres automatiques), réimportable tel quel.
- Le fichier `donnees_portefeuille.json` livré en V0.3 peut maintenant être importé
  **directement depuis l'interface**, sans copier manuellement de fichier.

## Nouveautés V0.4

- **CRUD complet** : ajout, modification, suppression de services depuis l'interface
  (`/#/portefeuille/nouveau`, `/#/portefeuille/<id>/modifier`, bouton Supprimer sur la fiche).
- **Formulaire piloté par schéma** (`static/js/service-form.js`) : les 32 champs/9 sections sont
  déclarés une seule fois (`FORM_SCHEMA`) et réutilisés pour la création et l'édition — ajouter un
  champ ne demande qu'une ligne, pas de duplication de code.
- **Validation serveur systématique** (`services/validation.py`) : nom obligatoire, ID/nom en
  doublon rejetés, valeurs hors référentiel rejetées (ex. criticité inconnue).
- **Notifications** : toasts de succès/erreur, confirmation avant suppression, complétude
  recalculée automatiquement à chaque création/modification.
- Chaque écriture (création, modification, suppression) crée un **backup automatique**.

## Nouveautés V0.3

- **Design modernisé** : animations d'entrée, cartes KPI avec effet de survol, chargement en
  "skeleton", barres de complétude animées.
- **Graphiques** (Chart.js, chargé via CDN) : répartitions par criticité, hébergement, mode de
  développement sur le dashboard ; page **Analyses** complète (criticité, statut, hébergement,
  catégorie, mode de développement, direction bénéficiaire, concentration prestataire).
- **Aucune donnée métier codée en dur** : `data/services.json` est livré vide. Les données réelles
  d'un portefeuille (ex. celui de de votre SI) sont fournies à part, au format JSON natif MIRSAAD, prêtes
  à être importées (voir plus bas).
- **Page Paramètres fonctionnelle** : nom de l'organisation, nom complet/officiel, nom de
  l'application (FR/AR), seuil de complétude — tout est configurable, plus aucun "Votre Organisation" codé en
  dur nulle part dans le code ou l'interface.

## Architecture

```
mirsaad/
├── app.py                     # Flask : API JSON + shell SPA (static/index.html)
├── config.py                  # chemins de fichiers uniquement — aucune identité codée en dur
├── data/
│   ├── services.json          # VIDE à la livraison — voir "Importer des données" ci-dessous
│   ├── settings.json          # identité de l'organisation + réglages (modifiable via /parametres)
│   ├── references.json        # référentiels (statuts, criticités, hébergements...)
│   └── backups/                # backups horodatés créés avant toute écriture
├── routes/                    # API REST
│   ├── api_dashboard.py        # GET /api/dashboard
│   ├── api_services.py         # GET /api/services, /api/services/<id>, /api/references
│   ├── api_quality.py          # GET /api/quality
│   └── api_settings.py         # GET/PUT /api/settings
├── services/                  # logique métier (indépendante de toute donnée réelle)
│   ├── json_repository.py      # I/O JSON atomique + backup
│   ├── service_manager.py      # recherche, filtres, CRUD complet (create/update/delete)
│   ├── validation.py           # doublons ID/nom, champs obligatoires, valeurs hors référentiel
│   ├── statistics.py           # KPI de pilotage
│   ├── quality.py              # complétude (seuil configurable) et anomalies
│   └── settings_manager.py     # validation des paramètres (nom d'organisation, etc.)
├── static/
│   ├── index.html              # shell unique de la SPA
│   ├── css/style.css           # design (animations, thème, composants graphiques, formulaires)
│   └── js/
│       ├── api.js               # client fetch vers /api/* (dont CRUD services)
│       ├── render.js            # helpers DOM, branding dynamique, toasts, confirmations
│       ├── charts.js            # wrapper Chart.js (cycle de vie adapté à une SPA)
│       ├── service-form.js      # schéma déclaratif du formulaire service (génération + collecte)
│       ├── views.js             # une fonction de rendu par écran
│       ├── router.js            # routage hash sans dépendance
│       └── app.js               # bootstrap (charge les paramètres avant tout rendu)
└── tests/
    ├── fixtures/sample_services.json   # données synthétiques génériques pour les tests
    ├── test_v02.py                      # couche services/ (11 tests)
    ├── test_api.py                      # endpoints API, SPA, paramètres, CRUD (26 tests)
    └── test_crud.py                     # couche service_manager — CRUD et validations (15 tests)
```

## Prérequis

- Python 3.10+
- Connexion internet pour charger Chart.js depuis le CDN (`cdn.jsdelivr.net`) — à héberger en
  local si l'environnement de déploiement n'a pas accès à internet.

## Installation

```bash
cd mirsaad
pip install -r requirements.txt
```

## Lancement

```bash
python3 app.py
```

Application sur **http://127.0.0.1:5000**.

## Importer des données (portefeuille réel)

L'application est livrée **sans aucune donnée de service**. Un fichier séparé
`donnees_portefeuille_VotreOrg.json` (13 services réels de l'VotreOrg, extraits du fichier Excel
d'origine) est fourni en complément, au format JSON natif de MIRSAAD — c'est le format le plus
fiable pour un import futur car il correspond exactement au modèle interne de l'application (les
formats Excel/CSV impliqueraient un aplatissement des 32 champs/9 sections et une perte de
fidélité).

**Pour l'instant** (le module Importer graphique est prévu en V0.7), l'import se fait en copiant
le fichier :

```bash
cp donnees_portefeuille_VotreOrg.json mirsaad/data/services.json
```

puis en relançant l'application. La complétude, les KPI, les graphiques et le module Qualité se
recalculent automatiquement.

## Configurer l'organisation

Menu **Paramètres** (`/#/parametres`) : nom de l'organisation, nom complet/officiel, nom de
l'application (FR/AR), seuil de complétude d'une fiche "complète". Chaque enregistrement crée un
backup automatique dans `data/backups/`.

Via l'API :
```bash
curl -X PUT http://127.0.0.1:5000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"organisation_name": "Nom de votre agence"}'
```

## API disponible (V0.4)

| Endpoint | Description |
|---|---|
| `GET /api/dashboard` | KPI + points d'attention + métadonnées |
| `GET /api/services?q=&criticite=&hebergement=&...` | Liste filtrée/recherchée |
| `GET /api/services/<id>` | Fiche détaillée d'un service (404 JSON si absent) |
| `POST /api/services` | Crée un service (validation, ID auto-généré si omis) |
| `PUT /api/services/<id>` | Modifie un service (fusion partielle, revalidation) |
| `DELETE /api/services/<id>` | Supprime un service (backup automatique) |
| `POST /api/import/preview` | Analyse un fichier (JSON/Excel), retourne un aperçu + token |
| `POST /api/import/confirm` | Applique l'import (`{token, strategy}`), backup automatique |
| `GET /api/export/excel` | Télécharge le portefeuille au format Excel |
| `GET /api/quality?anomalie=<label>` | Rapport qualité, avec drill-down optionnel |
| `GET/PUT /api/references` | Référentiels (valeurs de filtres/formulaires) |
| `GET/PUT /api/settings` | Paramètres (nom d'organisation, seuils...) |

## Tests

```bash
python3 -m pytest tests/ -v
```

68 tests : couche services (11) + endpoints API/SPA/paramètres/CRUD (26) + couche
service_manager CRUD et validations (15) + import/export, parsing et stratégies (16). Utilisent
un **fixture générique** (`tests/fixtures/sample_services.json`) et jamais de donnée métier réelle.

## Maintenance

- Nouveau paramètre configurable : l'ajouter à `ALLOWED_KEYS` dans `settings_manager.py`, à
  `data/settings.json` (valeur par défaut), et au formulaire dans `views.js` (`Views.settings`).
- Nouveau graphique : ajouter une méthode dans `charts.js`, l'appeler depuis la vue concernée
  après `Render.setApp(...)`.
- Nouvel endpoint : créer/étendre un module `routes/api_*.py`, l'enregistrer dans `app.py`.
