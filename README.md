# MIRSAAD — مرصاد

Plateforme de pilotage et de visibilité du portefeuille des services SI.

Statut actuel : **V0.9** — application complète (analyse, socle SPA, CRUD, dashboard, qualité,
import/export, rapports PDF, finition UX/sécurité).

## Nouveautés V0.9 — Finition

- **Responsive** : media queries pour mobile/tablette (navigation, grilles KPI, formulaires,
  tableaux à défilement horizontal, toasts adaptés).
- **Cohérence visuelle renforcée** : icônes de navigation, cartes KPI à accent coloré alignées
  sur le style du rapport PDF.
- **Sécurité** :
  - Extensions de fichier importées strictement contrôlées via la configuration
    (`ALLOWED_IMPORT_EXTENSIONS`).
  - Taille maximale d'upload appliquée (`MAX_CONTENT_LENGTH`), avec réponse JSON propre en cas
    de dépassement (413).
  - Gestionnaire d'erreur 500 générique : aucune trace technique (traceback) n'est jamais
    renvoyée au client, y compris hors mode debug.
  - Avertissement au démarrage si la clé secrète par défaut est utilisée en dehors du mode debug.

## Nouveautés V0.8

- **Rapports PDF** (WeasyPrint) : rapport complet (couverture, synthèse à cartes KPI +
  graphiques matplotlib, une page par service) et fiche PDF individuelle. Design à base de
  cartes, bandeau coloré selon la criticité, cohérent avec l'identité MIRSAAD.

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
  déclarés une seule fois (`FORM_SCHEMA`) et réutilisés pour la création et l'édition.
- **Validation serveur systématique** (`services/validation.py`) : nom obligatoire, ID/nom en
  doublon rejetés, valeurs hors référentiel rejetées (ex. criticité inconnue).
- Chaque écriture (création, modification, suppression) crée un **backup automatique**.

## Nouveautés V0.3

- **Design modernisé** : animations d'entrée, cartes KPI avec effet de survol, chargement en
  "skeleton", barres de complétude animées.
- **Graphiques** (Chart.js, chargé via CDN) : répartitions par criticité, hébergement, mode de
  développement sur le dashboard ; page **Analyses** complète (criticité, statut, hébergement,
  catégorie, mode de développement, direction bénéficiaire, concentration prestataire).
- **Aucune donnée métier codée en dur** : `data/services.json` est livré vide. Les données réelles
  d'un portefeuille (ex. celui de votre SI) sont fournies à part, au format JSON natif MIRSAAD, prêtes
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
│   ├── api_services.py         # CRUD /api/services
│   ├── api_quality.py          # GET /api/quality
│   ├── api_settings.py         # GET/PUT /api/settings
│   ├── api_import.py           # POST /api/import/preview, /api/import/confirm
│   ├── api_export.py           # GET /api/export/excel
│   └── api_reports.py          # GET /api/reports/pdf, /api/reports/pdf/<id>
├── services/                  # logique métier (indépendante de toute donnée réelle)
│   ├── json_repository.py      # I/O JSON atomique + backup
│   ├── service_manager.py      # recherche, filtres, CRUD complet
│   ├── validation.py           # doublons ID/nom, champs obligatoires, valeurs hors référentiel
│   ├── statistics.py           # KPI de pilotage
│   ├── quality.py              # complétude (seuil configurable) et anomalies
│   ├── settings_manager.py     # validation des paramètres
│   ├── import_export.py        # parsing JSON/Excel, preview, stratégies d'import
│   ├── excel_export.py         # génération de l'export Excel
│   └── pdf_service.py          # génération des rapports PDF (WeasyPrint)
├── static/
│   ├── index.html              # shell unique de la SPA
│   ├── css/style.css           # design (animations, thème, responsive, composants)
│   └── js/
│       ├── api.js               # client fetch vers /api/*
│       ├── render.js            # helpers DOM, branding dynamique, toasts, confirmations
│       ├── charts.js            # wrapper Chart.js (cycle de vie adapté à une SPA)
│       ├── service-form.js      # schéma déclaratif du formulaire service
│       ├── views.js             # une fonction de rendu par écran
│       ├── router.js            # routage hash sans dépendance
│       └── app.js               # bootstrap (charge les paramètres avant tout rendu)
└── tests/                      # 79 tests pytest (voir "Tests" ci-dessous)
```

## Prérequis

- **Python 3.10 à 3.13 recommandé.** Une version Python très récente (ex. 3.14 tout juste
  sortie) peut ne pas encore disposer de paquets binaires (« wheels ») pour certaines
  dépendances scientifiques comme `matplotlib`, ce qui force une compilation locale et échoue
  en l'absence de compilateur C installé (voir Dépannage Windows plus bas).
- Connexion internet pour charger Chart.js depuis le CDN (`cdn.jsdelivr.net`) — à héberger en
  local si l'environnement de déploiement n'a pas accès à internet.
- **Windows uniquement** : WeasyPrint nécessite les bibliothèques GTK (Pango/Cairo/GObject).
  La façon la plus simple de les obtenir est d'installer **[MSYS2](https://www.msys2.org/)**
  (dans `C:\msys64` par défaut), puis dans un terminal MSYS2 UCRT64 :
  ```
  pacman -S mingw-w64-ucrt-x86_64-pango
  ```
  `app.py` configure automatiquement `WEASYPRINT_DLL_DIRECTORIES` vers
  `C:\msys64\ucrt64\bin` au démarrage sous Windows. Si MSYS2 est installé ailleurs, définissez
  vous-même la variable d'environnement `WEASYPRINT_DLL_DIRECTORIES` avec le bon chemin avant de
  lancer l'application. Sans cette bibliothèque, la génération de rapport PDF échoue avec une
  erreur mentionnant `libgobject` ou `cairo`.

## Installation

```bash
cd mirsaad
python -m pip install -r requirements.txt
```

**Important (Windows) :** utilisez `python -m pip install ...` plutôt que `pip install ...`.
Sur beaucoup d'installations Windows, la commande `pip` seule n'est pas reconnue ou pointe vers
un autre interpréteur Python que celui utilisé pour lancer l'application ; passer par
`python -m pip` garantit que le paquet est installé pour le bon interpréteur.

## Lancement

```bash
python app.py
```

(Sur Linux/macOS avec plusieurs versions de Python installées, utilisez `python3 app.py` si
`python` ne pointe pas vers Python 3.)

Application sur **http://127.0.0.1:5000**.

## Dépannage — Windows

### « Failed to build 'matplotlib' » / erreur numpy/meson à l'installation

Cette erreur survient quand pip ne trouve pas de paquet binaire précompilé pour votre version de
Python et tente de compiler `matplotlib`/`numpy` depuis les sources, ce qui nécessite un
compilateur C (Visual Studio Build Tools) absent par défaut sur Windows.

Deux solutions, dans l'ordre de préférence :

1. **Mettre à jour pip puis réessayer** : `python -m pip install --upgrade pip`, puis relancer
   `python -m pip install -r requirements.txt`. Une version de pip trop ancienne peut mal
   détecter les paquets binaires disponibles.
2. **Utiliser une version de Python plus établie** (3.11 ou 3.12) si le problème persiste : les
   versions Python très récentes n'ont pas toujours de paquets précompilés disponibles pour
   toutes les dépendances immédiatement après leur sortie.

### Génération de rapport PDF en échec

Voir la note WeasyPrint/GTK dans la section Prérequis ci-dessus.

## Importer des données (portefeuille réel)

L'application est livrée **sans aucune donnée de service**. Un fichier séparé
`donnees_portefeuille_VotreOrg.json` (13 services réels de VotreOrg, extraits du fichier Excel
d'origine) est fourni en complément, au format JSON natif de MIRSAAD — c'est le format le plus
fiable pour un import car il correspond exactement au modèle interne de l'application (les
formats Excel/CSV impliqueraient un aplatissement des 32 champs/9 sections et une perte de
fidélité).

Depuis l'interface : menu **Importer** → sélectionner le fichier → analyser l'aperçu (nouveaux /
modifiés / inchangés / erreurs) → choisir une stratégie → confirmer.

Si l'interface graphique d'import n'est pas disponible, copier manuellement le fichier puis relancer :

```bash
cp donnees_portefeuille_VotreOrg.json mirsaad/data/services.json
```

La complétude, les KPI, les graphiques et le module Qualité se recalculent automatiquement.

## Configurer l'organisation

Menu **Paramètres** (`/#/parametres`) : nom de l'organisation, nom complet/officiel, nom de
l'application (FR/AR), seuil de complétude d'une fiche "complète". Chaque enregistrement crée un
backup automatique dans `data/backups/`.

Via l'API :
```bash
curl -X PUT http://127.0.0.1:5000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"organisation_name": "Nom de votre organisation"}'
```

## API disponible

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
| `GET /api/reports/pdf` | Télécharge le rapport PDF complet |
| `GET /api/reports/pdf/<id>` | Télécharge la fiche PDF d'un service |
| `GET /api/quality?anomalie=<label>` | Rapport qualité, avec drill-down optionnel |
| `GET/PUT /api/references` | Référentiels (valeurs de filtres/formulaires) |
| `GET/PUT /api/settings` | Paramètres (nom d'organisation, seuils...) |

## Tests

```bash
python -m pytest tests/ -v
```

79 tests couvrant : couche services, endpoints API/SPA/paramètres/CRUD, import/export
(parsing et stratégies), génération PDF. Utilisent un **fixture générique**
(`tests/fixtures/sample_services.json`) et jamais de donnée métier réelle.

## Maintenance

- Nouveau paramètre configurable : l'ajouter à `ALLOWED_KEYS` dans `settings_manager.py`, à
  `data/settings.json` (valeur par défaut), et au formulaire dans `views.js` (`Views.settings`).
- Nouveau graphique (web) : ajouter une méthode dans `charts.js`, l'appeler depuis la vue
  concernée après `Render.setApp(...)`.
- Nouveau graphique (PDF) : ajouter une fonction dans `pdf_service.py` (voir `_chart_png`).
- Nouvel endpoint : créer/étendre un module `routes/api_*.py`, l'enregistrer dans `app.py`.
