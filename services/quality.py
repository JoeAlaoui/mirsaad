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


def completeness_report(services):
    total = len(services)
    if total == 0:
        return {"total": 0, "completes": 0, "incompletes": 0, "taux_completude_pct": 0}

    completes = [s for s in services if s["meta"].get("completude_pct", 0) >= SEUIL_COMPLET_PCT]
    incompletes = [s for s in services if s not in completes]
    taux = round(sum(s["meta"].get("completude_pct", 0) for s in services) / total)

    return {
        "total": total,
        "completes": len(completes),
        "incompletes": len(incompletes),
        "taux_completude_pct": taux,
        "seuil_pct": SEUIL_COMPLET_PCT,
    }


def quality_report(services):
    return {
        "completude": completeness_report(services),
        "anomalies": anomalies_by_category(services),
        "nb_anomalies_total": sum(len(v) for v in anomalies_by_category(services).values()),
    }
