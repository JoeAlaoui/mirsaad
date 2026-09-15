"""
KPI et indicateurs de pilotage, calculés dynamiquement à partir de services.json.
Ne calcule que des indicateurs fiables au vu des données disponibles (cf. diagnostic V0.1).
"""
from collections import Counter


def _count_by(services, path):
    counter = Counter()
    for svc in services:
        v = svc
        for key in path:
            v = v.get(key) if isinstance(v, dict) else None
        if v:
            counter[v] += 1
    return dict(counter.most_common())


def compute_kpis(services):
    total = len(services)
    if total == 0:
        return {"total": 0}

    par_statut_portfolio = _count_by(services, ("identification", "statut_portfolio"))
    par_criticite = _count_by(services, ("meta", "criticite"))
    par_mode_dev = _count_by(services, ("identification", "mode_developpement"))
    par_hebergement = _count_by(services, ("identification", "hebergement"))
    par_categorie = _count_by(services, ("identification", "categorie"))
    par_direction = _count_by(services, ("identification", "direction_beneficiaire"))
    par_prestataire = _count_by(services, ("identification", "prestataire"))
    par_proprietaire = _count_by(services, ("identification", "proprietaire"))

    avec_proprietaire = sum(1 for s in services if s["identification"].get("proprietaire"))
    avec_direction = sum(1 for s in services if s["identification"].get("direction_beneficiaire"))
    avec_rto_rpo = sum(
        1 for s in services
        if s["performance_sla"].get("rto") and s["performance_sla"].get("rpo")
    )
    avec_prestataire = sum(1 for s in services if s["identification"].get("prestataire"))
    completude_moyenne = round(sum(s["meta"].get("completude_pct", 0) for s in services) / total)

    return {
        "total": total,
        "par_statut_portfolio": par_statut_portfolio,
        "par_criticite": par_criticite,
        "par_mode_developpement": par_mode_dev,
        "par_hebergement": par_hebergement,
        "par_categorie": par_categorie,
        "par_direction_beneficiaire": par_direction,
        "par_prestataire": par_prestataire,
        "par_proprietaire": par_proprietaire,
        "couverture_gouvernance_pct": round(100 * avec_proprietaire / total),
        "couverture_direction_pct": round(100 * avec_direction / total),
        "couverture_continuite_pct": round(100 * avec_rto_rpo / total),
        "taux_dependance_prestataire_pct": round(100 * avec_prestataire / total),
        "completude_moyenne_pct": completude_moyenne,
    }
