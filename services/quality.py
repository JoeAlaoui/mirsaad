"""
Module Qualité des données — indépendant des KPI de pilotage (statistics.py).
Détecte les anomalies identifiées dans le diagnostic V0.1 et calcule la complétude.
"""

# Champs jugés obligatoires pour qu'une fiche soit considérée "complète" au sens gouvernance.
CHAMPS_CRITIQUES = [
    ("identification", "proprietaire", "Propriétaire manquant"),
    ("identification", "direction_beneficiaire", "Direction bénéficiaire manquante"),
    ("meta", "statut", "Statut manquant"),
    ("meta", "criticite", "Criticité manquante"),
    ("performance_sla", "rto", "RTO manquant"),
    ("performance_sla", "rpo", "RPO manquant"),
]

SEUIL_COMPLET_PCT = 70  # fiche jugée "complète" si complétude >= 70%

# Sections/champs comptabilisés dans le calcul de complétude (hors id, meta, notes).
COMPLETENESS_SECTIONS = [
    "identification", "proposition_valeur", "description",
    "architecture", "securite", "performance_sla", "risques", "cycle_vie",
]


def compute_completude_pct(svc):
    """Pourcentage de champs renseignés (non null/vide) parmi les sections comptabilisées."""
    fields = []
    for section in COMPLETENESS_SECTIONS:
        content = svc.get(section) or {}
        fields.extend(content.values())
    filled = sum(1 for f in fields if f not in (None, ""))
    return round(100 * filled / len(fields)) if fields else 0


def _get(svc, section, field):
    return svc.get(section, {}).get(field)


def anomalies_by_category(services):
    """Retourne {libellé_anomalie: [liste d'IDs de services concernés]}."""
    result = {}
    for section, field, label in CHAMPS_CRITIQUES:
        ids = [s["id"] for s in services if not _get(s, section, field)]
        if ids:
            result[label] = ids
    return result


def completeness_report(services, seuil_pct=SEUIL_COMPLET_PCT):
    total = len(services)
    if total == 0:
        return {"total": 0, "completes": 0, "incompletes": 0, "taux_completude_pct": 0, "seuil_pct": seuil_pct}

    completes = [s for s in services if s["meta"].get("completude_pct", 0) >= seuil_pct]
    incompletes = [s for s in services if s not in completes]
    taux = round(sum(s["meta"].get("completude_pct", 0) for s in services) / total)

    return {
        "total": total,
        "completes": len(completes),
        "incompletes": len(incompletes),
        "taux_completude_pct": taux,
        "seuil_pct": seuil_pct,
    }


def quality_report(services, seuil_pct=SEUIL_COMPLET_PCT):
    anomalies = anomalies_by_category(services)
    return {
        "completude": completeness_report(services, seuil_pct=seuil_pct),
        "anomalies": anomalies,
        "nb_anomalies_total": sum(len(v) for v in anomalies.values()),
    }
