"""
Import de portefeuille (V0.7) : JSON natif MIRSAAD ou Excel (modèle simplifié à plat).
Ne modifie jamais services.json directement — construit un aperçu (preview) que
l'utilisateur doit confirmer explicitement (aucun écrasement silencieux).
"""
import json
import openpyxl

from services.service_manager import ServiceManager
from services.quality import compute_completude_pct

# Colonnes du modèle Excel d'import/export simplifié (une ligne = un service).
EXCEL_COLUMNS = [
    ("ID", ("id",)),
    ("Nom", ("identification", "nom")),
    ("Categorie", ("identification", "categorie")),
    ("Proprietaire", ("identification", "proprietaire")),
    ("Direction_Beneficiaire", ("identification", "direction_beneficiaire")),
    ("Date_Creation", ("identification", "date_creation")),
    ("Statut_Portfolio", ("identification", "statut_portfolio")),
    ("Hebergement", ("identification", "hebergement")),
    ("Mode_Developpement", ("identification", "mode_developpement")),
    ("Prestataire", ("identification", "prestataire")),
    ("Statut", ("meta", "statut")),
    ("Criticite", ("meta", "criticite")),
    ("Stack_Technologique", ("architecture", "stack_technologique")),
    ("Donnees_Traitees", ("architecture", "donnees_traitees")),
    ("RTO", ("performance_sla", "rto")),
    ("RPO", ("performance_sla", "rpo")),
    ("Disponibilite_Cible", ("performance_sla", "disponibilite_cible")),
]


class ImportError_(Exception):
    pass


def _set_path(d, path, value):
    for key in path[:-1]:
        d = d.setdefault(key, {})
    d[path[-1]] = value


def _clean(v):
    if v is None:
        return None
    if isinstance(v, str) and not v.strip():
        return None
    if isinstance(v, str):
        return v.strip()
    return v


def parse_json(file_bytes):
    """Parse un fichier JSON au format natif MIRSAAD ({"services": [...]})."""
    try:
        payload = json.loads(file_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ImportError_(f"Fichier JSON invalide : {e}")

    services = payload.get("services")
    if services is None:
        raise ImportError_("Le fichier JSON ne contient pas de clé « services ».")

    parsed, errors = [], []
    for i, raw in enumerate(services):
        nom = (raw.get("identification", {}) or {}).get("nom")
        if not nom:
            errors.append({"ligne": i + 1, "message": "Nom manquant — service ignoré."})
            continue
        svc = ServiceManager.empty_skeleton()
        ServiceManager._deep_merge(svc, raw)
        svc["id"] = raw.get("id") or None
        svc["meta"]["completude_pct"] = compute_completude_pct(svc)
        parsed.append(svc)

    return parsed, errors


def parse_excel(file_bytes):
    """Parse un fichier Excel au format simplifié à plat (voir EXCEL_COLUMNS)."""
    import io

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    except Exception as e:
        raise ImportError_(f"Fichier Excel invalide ou corrompu : {e}")

    ws = wb["Inventaire"] if "Inventaire" in wb.sheetnames else wb.worksheets[0]
    header = [c.value for c in ws[1]]
    col_index = {name: i for i, name in enumerate(header)}

    missing = [name for name, _ in EXCEL_COLUMNS if name not in col_index]
    if "Nom" in missing:
        raise ImportError_("La colonne obligatoire « Nom » est absente du fichier.")

    parsed, errors = [], []
    for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if row is None or all(v is None for v in row):
            continue

        nom = _clean(row[col_index["Nom"]]) if "Nom" in col_index else None
        if not nom:
            errors.append({"ligne": row_num, "message": "Nom manquant — ligne ignorée."})
            continue

        svc = ServiceManager.empty_skeleton()
        for name, path in EXCEL_COLUMNS:
            if name not in col_index:
                continue
            value = _clean(row[col_index[name]])
            if path == ("id",):
                continue
            _set_path(svc, path, value)

        raw_id = _clean(row[col_index["ID"]]) if "ID" in col_index else None
        svc["id"] = raw_id
        svc["meta"]["completude_pct"] = compute_completude_pct(svc)
        parsed.append(svc)

    return parsed, errors


def build_preview(existing_services, imported_services, parse_errors):
    """Catégorise les services importés par rapport à l'existant, sans rien modifier."""
    existing_by_id = {s["id"]: s for s in existing_services}
    seen_ids_in_file = {}

    nouveaux, modifies, inchanges, doublons_fichier = [], [], [], []

    for svc in imported_services:
        sid = svc.get("id")

        if sid and sid in seen_ids_in_file:
            doublons_fichier.append({"id": sid, "nom": svc["identification"]["nom"]})
            continue
        if sid:
            seen_ids_in_file[sid] = True

        if not sid or sid not in existing_by_id:
            nouveaux.append(svc)
        else:
            existing = existing_by_id[sid]
            # Comparaison superficielle : les deux enregistrements sérialisés sont-ils identiques ?
            comparable_existing = {k: v for k, v in existing.items() if k != "meta"}
            comparable_new = {k: v for k, v in svc.items() if k != "meta"}
            if comparable_existing == comparable_new:
                inchanges.append(svc)
            else:
                modifies.append(svc)

    return {
        "nouveaux": nouveaux,
        "modifies": modifies,
        "inchanges": inchanges,
        "doublons_fichier": doublons_fichier,
        "erreurs": parse_errors,
        "resume": {
            "nouveaux": len(nouveaux),
            "modifies": len(modifies),
            "inchanges": len(inchanges),
            "doublons_fichier": len(doublons_fichier),
            "erreurs": len(parse_errors),
        },
    }


def apply_import(existing_services, imported_services, strategy):
    """
    Applique la stratégie choisie et renvoie la nouvelle liste de services.
    - remplacer : écrase entièrement le portefeuille par le fichier importé.
    - ajouter : n'ajoute que les services dont l'ID n'existe pas déjà (les doublons sont ignorés).
    - maj : met à jour les services existants par ID, ajoute les nouveaux (upsert).
    """
    if strategy == "remplacer":
        result = []
        manager_stub = ServiceManager(None)
        for svc in imported_services:
            if not svc.get("id"):
                svc["id"] = manager_stub._generate_id(result)
            result.append(svc)
        return result

    existing_by_id = {s["id"]: s for s in existing_services}
    result = list(existing_services)
    manager_stub = ServiceManager(None)

    if strategy == "ajouter":
        for svc in imported_services:
            sid = svc.get("id")
            if sid and sid in existing_by_id:
                continue  # ignoré : déjà présent
            if not sid:
                sid = manager_stub._generate_id(result)
            svc["id"] = sid
            result.append(svc)
            existing_by_id[sid] = svc
        return result

    if strategy == "maj":
        for svc in imported_services:
            sid = svc.get("id")
            if not sid:
                sid = manager_stub._generate_id(result)
                svc["id"] = sid
                result.append(svc)
                existing_by_id[sid] = svc
            elif sid in existing_by_id:
                idx = next(i for i, s in enumerate(result) if s["id"] == sid)
                result[idx] = svc
            else:
                result.append(svc)
                existing_by_id[sid] = svc
        return result

    raise ImportError_(f"Stratégie d'import inconnue : {strategy}")
