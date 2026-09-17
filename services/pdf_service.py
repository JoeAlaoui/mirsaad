"""
Génération de rapports PDF institutionnels (V0.8) via WeasyPrint.
- Rapport complet : couverture + synthèse (cartes KPI + graphiques) + une page par service.
- Fiche individuelle : même design qu'une page service du rapport complet.
Dépendance connue : WeasyPrint 62.3 nécessite pydyf==0.11.0 (voir requirements.txt).
"""
import base64
import io
from datetime import datetime
from html import escape as _esc

from weasyprint import HTML, CSS

CRITICITE_COLORS = {
    "Critique": "#b3261e",
    "Élevée": "#b06000",
    "Moyenne": "#8a6d00",
    "Faible": "#4b5568",
}

SECTION_ICONS = {
    "identification": "◆",
    "valeur": "★",
    "description": "▤",
    "securite": "◈",
    "risques": "▲",
    "cycle": "◷",
}


def _e(value):
    """Échappe une valeur pour insertion HTML ; None/vide -> tiret."""
    if value is None or value == "":
        return "—"
    return _esc(str(value))


def _bool_label(value):
    if value is None:
        return "—"
    return "Oui" if value else "Non"


def _badge(criticite):
    color = CRITICITE_COLORS.get(criticite, "#8592a6")
    label = criticite or "Non renseignée"
    return f'<span class="badge" style="background:{color}">{_e(label)}</span>'


def _chart_png(labels, values, colors, ylabel="Nombre de services"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(4.6, 2.5), dpi=160)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    bars = ax.bar(labels, values, color=colors, width=0.6)
    ax.set_ylabel(ylabel, fontsize=8, color="#4b5568")
    ax.tick_params(axis="both", labelsize=8, colors="#4b5568")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#dde3ec")
    ax.yaxis.grid(True, color="#eef1f6", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02, str(v),
                 ha="center", fontsize=8, color="#101a2e", fontweight="bold")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


BASE_CSS = """
@page {
    size: A4;
    margin: 0;
    @bottom-center {
        content: var(--footer-text);
        font-family: Arial, sans-serif;
        font-size: 8pt;
        color: #a0a8b5;
    }
}
* { box-sizing: border-box; }
body { font-family: Arial, sans-serif; color: #101a2e; font-size: 10pt; margin: 0; }
.page { page-break-after: always; padding: 1.6cm 1.7cm 1.4cm 1.7cm; position: relative; }
.page:last-child { page-break-after: auto; }

/* ---------- Couverture ---------- */
.cover {
    height: 29.7cm;
    padding: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    background: linear-gradient(160deg, #0a111f 0%, #101a2e 55%, #0f4c81 130%);
    color: white;
}
.cover .mark {
    width: 74pt; height: 74pt; border-radius: 16pt;
    background: linear-gradient(135deg, #1c8fa6, #0f4c81);
    display: flex; align-items: center; justify-content: center;
    font-size: 34pt; font-weight: bold; color: white;
    margin-bottom: 22pt;
}
.cover .app-name { font-size: 38pt; font-weight: bold; letter-spacing: 4pt; margin-bottom: 4pt; }
.cover .app-name-ar { font-size: 17pt; color: #8fb3d6; margin-bottom: 34pt; }
.cover .doc-title { font-size: 15pt; font-weight: bold; line-height: 1.4; margin: 0 0 20pt 0; width: 13cm; }
.cover .org-name { font-size: 12.5pt; color: #c3d3e8; margin: 0 0 46pt 0; width: 13cm; }
.cover .meta-pill {
    display: inline-block; padding: 7pt 18pt; border-radius: 20pt;
    background: rgba(255,255,255,0.10); border: 0.5pt solid rgba(255,255,255,0.22);
    font-size: 9pt; color: #dde3ec;
}
.cover .footer-brand { position: absolute; bottom: 26pt; font-size: 8pt; color: rgba(255,255,255,0.45); letter-spacing: 1pt; }

/* ---------- Titres ---------- */
h1.section-title {
    font-size: 16pt; font-weight: bold; color: #0a111f;
    margin: 0 0 4pt 0;
}
.section-subtitle { font-size: 9.5pt; color: #8592a6; margin-bottom: 18pt; }
h2.subsection-title {
    font-size: 9pt; font-weight: bold; color: #0f4c81; text-transform: uppercase;
    letter-spacing: 0.6pt; margin: 0 0 5pt 0; display: flex; align-items: center; gap: 6pt;
}
h2.subsection-title .icon {
    display: inline-block; width: 14pt; height: 14pt; border-radius: 4pt;
    background: #e7eef7; color: #0f4c81; font-size: 8pt; text-align: center; line-height: 14pt;
}

/* ---------- Cartes KPI (synthèse) ---------- */
.kpi-grid { display: flex; flex-wrap: wrap; gap: 8pt; margin-bottom: 16pt; }
.kpi-card {
    width: 22.5%; background: #f6f8fb; border: 0.5pt solid #dde3ec; border-left: 3pt solid #0f4c81;
    border-radius: 5pt; padding: 9pt 10pt;
}
.kpi-card .kpi-value { font-size: 17pt; font-weight: bold; color: #0a111f; line-height: 1.1; }
.kpi-card .kpi-label { font-size: 7.5pt; color: #4b5568; text-transform: uppercase; letter-spacing: 0.3pt; margin-top: 3pt; }
.kpi-card.accent-crit { border-left-color: #b3261e; }
.kpi-card.accent-ok { border-left-color: #1e7a4c; }
.kpi-card.accent-warn { border-left-color: #b06000; }

/* ---------- Cartes graphiques ---------- */
.chart-card-row { display: flex; gap: 10pt; margin-bottom: 16pt; }
.chart-card { flex: 1; background: white; border: 0.5pt solid #dde3ec; border-radius: 6pt; padding: 10pt; }
.chart-card .chart-title { font-size: 8.5pt; font-weight: bold; color: #4b5568; text-transform: uppercase; letter-spacing: 0.3pt; margin-bottom: 4pt; }
.chart-card img { width: 100%; display: block; }

/* ---------- Points d'attention ---------- */
.attention-grid { display: flex; flex-direction: column; gap: 6pt; }
.attention-item {
    display: flex; justify-content: space-between; align-items: center;
    background: #fbeceb; border-left: 3pt solid #b3261e; border-radius: 4pt;
    padding: 7pt 10pt; font-size: 9pt;
}
.attention-item .count {
    background: #b3261e; color: white; border-radius: 10pt; padding: 1pt 8pt; font-size: 8pt; font-weight: bold;
}
.attention-empty { color: #1e7a4c; font-size: 9.5pt; background: #e7f5ee; border-left: 3pt solid #1e7a4c; border-radius: 4pt; padding: 8pt 10pt; }

/* ---------- Page service ---------- */
.service-band {
    margin: -1.6cm -1.7cm 10pt -1.7cm; padding: 14pt 1.7cm 10pt 1.7cm;
    background: linear-gradient(120deg, #0a111f, #16213e);
    color: white;
}
.service-band .service-id { font-size: 8pt; color: #8fb3d6; letter-spacing: 0.5pt; margin-bottom: 2pt; }
.service-band .service-name { font-size: 16pt; font-weight: bold; margin-bottom: 6pt; }
.service-band .badge { margin-right: 6pt; }
.service-band .service-meta { font-size: 8.5pt; color: #c3d3e8; }

.card-grid { display: flex; flex-direction: column; gap: 6pt; }
.info-card { background: #f9fafc; border: 0.5pt solid #dde3ec; border-radius: 5pt; padding: 7pt 10pt; }
table.field-table { width: 100%; border-collapse: collapse; }
table.field-table td { padding: 2pt 4pt; vertical-align: top; font-size: 8.3pt; line-height: 1.25; }
table.field-table td.field-label { width: 34%; color: #7c8698; }
table.field-table td.field-value { color: #101a2e; }

.badge { display: inline-block; padding: 2.5pt 9pt; border-radius: 9pt; color: white; font-size: 8pt; font-weight: bold; }
"""


def _footer_css(app_name, org_name):
    text = f'"{app_name} — {org_name}    Page " counter(page) " / " counter(pages)'
    return f"@page {{ @bottom-center {{ content: {text}; font-family: Arial, sans-serif; font-size: 8pt; color: #a0a8b5; }} }}"


def _render_cover(app_name, app_name_ar, org_name, nb_services):
    date_str = datetime.now().strftime("%d/%m/%Y")
    initial = (app_name or "M")[0].upper()
    return f"""
    <div class="page cover">
        <div class="mark">{_e(initial)}</div>
        <div class="app-name">{_e(app_name)}</div>
        <div class="app-name-ar">{_e(app_name_ar)}</div>
        <div class="doc-title">Portefeuille des Services SI</div>
        <div class="org-name">{_e(org_name)}</div>
        <div class="meta-pill">Généré le {date_str} · {nb_services} service{"s" if nb_services != 1 else ""}</div>
        <div class="footer-brand">{_e(app_name)} — PLATEFORME DE PILOTAGE DU PORTEFEUILLE SI</div>
    </div>
    """


def _kpi_card(value, label, accent=""):
    return f'<div class="kpi-card {accent}"><div class="kpi-value">{_e(value)}</div><div class="kpi-label">{_e(label)}</div></div>'


def _render_synthesis(kpis, quality, org_name):
    anomalies = quality.get("anomalies", {})
    if anomalies:
        attention_html = "".join(
            f'<div class="attention-item"><span>{_e(label)}</span><span class="count">{len(ids)}</span></div>'
            for label, ids in anomalies.items()
        )
    else:
        attention_html = '<div class="attention-empty">Aucune anomalie détectée.</div>'

    kpi_cards = "".join([
        _kpi_card(kpis.get("total", 0), "Total services"),
        _kpi_card(kpis.get("par_statut_portfolio", {}).get("Catalogue", 0), "En catalogue", "accent-ok"),
        _kpi_card(kpis.get("par_statut_portfolio", {}).get("Pipeline", 0), "En pipeline"),
        _kpi_card(kpis.get("par_criticite", {}).get("Critique", 0), "Criticité critique", "accent-crit"),
        _kpi_card(f"{kpis.get('couverture_gouvernance_pct', 0)}%", "Couverture gouvernance"),
        _kpi_card(f"{kpis.get('couverture_continuite_pct', 0)}%", "Couverture continuité", "accent-warn"),
        _kpi_card(f"{kpis.get('taux_dependance_prestataire_pct', 0)}%", "Dépendance prestataire"),
        _kpi_card(f"{kpis.get('completude_moyenne_pct', 0)}%", "Complétude moyenne", "accent-ok"),
    ])

    charts_html = ""
    if kpis.get("total", 0) > 0:
        try:
            par_crit = kpis.get("par_criticite", {})
            crit_png = _chart_png(list(par_crit.keys()), list(par_crit.values()),
                                    [CRITICITE_COLORS.get(l, "#8592a6") for l in par_crit.keys()])
            par_statut = kpis.get("par_statut_portfolio", {})
            statut_png = _chart_png(list(par_statut.keys()), list(par_statut.values()),
                                      ["#0f4c81"] * len(par_statut))
            charts_html = f"""
            <h2 class="subsection-title"><span class="icon">▦</span>Répartitions</h2>
            <div class="chart-card-row">
                <div class="chart-card"><div class="chart-title">Par criticité</div><img src="data:image/png;base64,{crit_png}"></div>
                <div class="chart-card"><div class="chart-title">Par statut portfolio</div><img src="data:image/png;base64,{statut_png}"></div>
            </div>
            """
        except Exception:
            charts_html = ""

    return f"""
    <div class="page">
        <h1 class="section-title">Synthèse du portefeuille</h1>
        <div class="section-subtitle">{_e(org_name)}</div>
        <div class="kpi-grid">{kpi_cards}</div>
        {charts_html}
        <h2 class="subsection-title"><span class="icon">!</span>Points d'attention</h2>
        <div class="attention-grid">{attention_html}</div>
    </div>
    """


def _field_row(label, value):
    return f'<tr><td class="field-label">{_e(label)}</td><td class="field-value">{_e(value)}</td></tr>'


def _info_card(icon, title, rows):
    trs = "".join(_field_row(l, v) for l, v in rows)
    return f"""
    <div class="info-card">
        <h2 class="subsection-title"><span class="icon">{icon}</span>{_e(title)}</h2>
        <table class="field-table">{trs}</table>
    </div>
    """


def _render_service_page(svc, last=False):
    ident = svc["identification"]
    prop = svc["proposition_valeur"]
    desc = svc["description"]
    archi = svc["architecture"]
    secu = svc["securite"]
    perf = svc["performance_sla"]
    risq = svc["risques"]
    cycle = svc["cycle_vie"]
    meta = svc["meta"]

    band = f"""
    <div class="service-band">
        <div class="service-id">{_e(svc.get("id"))}</div>
        <div class="service-name">{_e(ident.get("nom"))}</div>
        <div>
            {_badge(meta.get("criticite"))}
            <span class="service-meta">{_e(ident.get("statut_portfolio"))} · Complétude {meta.get("completude_pct", 0)}%</span>
        </div>
    </div>
    """

    cards = "".join([
        _info_card("◆", "Identification & Gouvernance", [
            ("Catégorie", ident.get("categorie")),
            ("Propriétaire", ident.get("proprietaire")),
            ("Direction bénéficiaire", ident.get("direction_beneficiaire")),
            ("Hébergement", ident.get("hebergement")),
            ("Mode de développement", ident.get("mode_developpement")),
            ("Prestataire", ident.get("prestataire")),
        ]),
        _info_card("★", "Proposition de valeur", [
            ("Objectif", prop.get("objectif")),
            ("Problème résolu", prop.get("probleme_resolu")),
            ("Bénéfices", prop.get("benefices")),
        ]),
        _info_card("▤", "Description & Architecture", [
            ("Description fonctionnelle", desc.get("fonctionnelle")),
            ("Utilisateurs", desc.get("utilisateurs")),
            ("Stack technologique", archi.get("stack_technologique")),
            ("Données traitées", archi.get("donnees_traitees")),
        ]),
        _info_card("◈", "Sécurité & Continuité", [
            ("Données sensibles", _bool_label(secu.get("donnees_sensibles"))),
            ("Réglementation", secu.get("reglementation")),
            ("Disponibilité cible", perf.get("disponibilite_cible")),
            ("RTO", perf.get("rto")),
            ("RPO", perf.get("rpo")),
        ]),
        _info_card("▲", "Risques", [
            ("Risques principaux", risq.get("risques_principaux")),
            ("Impact en cas d'arrêt", risq.get("impact_arret")),
            ("Plan de continuité", risq.get("pca")),
        ]),
        _info_card("◷", "Cycle de vie", [
            ("Conception", cycle.get("conception")),
            ("Déploiement", cycle.get("deploiement")),
            ("Exploitation", cycle.get("exploitation")),
        ]),
    ])

    return f'<div class="page">{band}<div class="card-grid">{cards}</div></div>'


def generate_full_report(services, kpis, quality, settings):
    app_name = settings.get("application_name", "MIRSAAD")
    app_name_ar = settings.get("application_name_ar", "")
    org_name = settings.get("organisation_name", "Votre Organisation")

    pages = [_render_cover(app_name, app_name_ar, org_name, len(services))]
    pages.append(_render_synthesis(kpis, quality, org_name))
    for i, svc in enumerate(services):
        pages.append(_render_service_page(svc, last=(i == len(services) - 1)))

    html = f"<html><head><meta charset='utf-8'></head><body>{''.join(pages)}</body></html>"
    css = CSS(string=BASE_CSS + _footer_css(app_name, org_name))
    return HTML(string=html).write_pdf(stylesheets=[css])


def generate_service_report(svc, settings):
    app_name = settings.get("application_name", "MIRSAAD")
    org_name = settings.get("organisation_name", "Votre Organisation")

    html = f"<html><head><meta charset='utf-8'></head><body>{_render_service_page(svc, last=True)}</body></html>"
    css = CSS(string=BASE_CSS + _footer_css(app_name, org_name))
    return HTML(string=html).write_pdf(stylesheets=[css])
