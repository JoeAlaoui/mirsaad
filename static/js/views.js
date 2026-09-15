/**
 * Vues MIRSAAD. Chaque fonction reçoit les paramètres de route (params) et
 * une query object (query), fetch les données via Api, puis injecte le HTML.
 */
const Views = {};

// ---------- Dashboard ----------
Views.dashboard = async function () {
    Render.loading();
    try {
        const { metadata, kpis, quality } = await Api.getDashboard();

        const anomaliesHtml = Object.keys(quality.anomalies).length
            ? `<ul class="alert-list">${Object.entries(quality.anomalies)
                  .map(
                      ([label, ids]) => `
                <li>
                    <a href="#/qualite?anomalie=${encodeURIComponent(label)}">${Render.escape(label)}</a>
                    <span class="alert-count">${ids.length} service${ids.length > 1 ? "s" : ""}</span>
                </li>`
                  )
                  .join("")}</ul>`
            : `<p class="empty-state">Aucune anomalie détectée.</p>`;

        const listRepartition = (obj) =>
            `<ul class="alert-list">${Object.entries(obj)
                .map(([k, v]) => `<li><span>${Render.escape(k)}</span><span>${v}</span></li>`)
                .join("")}</ul>`;

        Render.setApp(`
            <div class="page-header">
                <h1>Tableau de bord</h1>
                <p>Vue consolidée du portefeuille — ${metadata.total_services} services · dernière mise à jour ${Render.escape(metadata.last_updated)}</p>
            </div>

            <div class="kpi-grid">
                <div class="kpi-card"><div class="kpi-value">${kpis.total}</div><div class="kpi-label">Total services</div></div>
                <div class="kpi-card"><div class="kpi-value">${kpis.par_statut_portfolio.Catalogue || 0}</div><div class="kpi-label">En catalogue (production)</div></div>
                <div class="kpi-card"><div class="kpi-value">${kpis.par_statut_portfolio.Pipeline || 0}</div><div class="kpi-label">En pipeline</div></div>
                <div class="kpi-card"><div class="kpi-value">${kpis.par_criticite.Critique || 0}</div><div class="kpi-label">Criticité critique</div></div>
                <div class="kpi-card"><div class="kpi-value">${kpis.couverture_gouvernance_pct}%</div><div class="kpi-label">Couverture gouvernance</div></div>
                <div class="kpi-card"><div class="kpi-value">${kpis.couverture_continuite_pct}%</div><div class="kpi-label">Couverture continuité (RTO/RPO)</div></div>
                <div class="kpi-card"><div class="kpi-value">${kpis.taux_dependance_prestataire_pct}%</div><div class="kpi-label">Dépendance prestataire</div></div>
                <div class="kpi-card"><div class="kpi-value">${kpis.completude_moyenne_pct}%</div><div class="kpi-label">Complétude moyenne</div></div>
            </div>

            <div class="panel">
                <div class="panel-header">Points d'attention — veille du portefeuille</div>
                <div class="panel-body">${anomaliesHtml}</div>
            </div>

            <div class="panel">
                <div class="panel-header">Répartition par mode de développement</div>
                <div class="panel-body">${listRepartition(kpis.par_mode_developpement)}</div>
            </div>

            <div class="panel">
                <div class="panel-header">Répartition par hébergement</div>
                <div class="panel-body">${listRepartition(kpis.par_hebergement)}</div>
            </div>
        `);
    } catch (e) {
        Render.error(e.message);
    }
};

// ---------- Portefeuille (liste) ----------
Views.portfolio = async function (params, query) {
    Render.loading();
    try {
        const [servicesData, references] = await Promise.all([
            Api.getServices(query),
            Api.getReferences(),
        ]);

        const options = (values, current) =>
            values.map((v) => `<option value="${Render.escape(v)}" ${v === current ? "selected" : ""}>${Render.escape(v)}</option>`).join("");

        const rows = servicesData.services.length
            ? servicesData.services
                  .map(
                      (svc) => `
                <tr>
                    <td>${Render.escape(svc.id)}</td>
                    <td><a href="#/portefeuille/${encodeURIComponent(svc.id)}">${Render.escape(svc.identification.nom)}</a></td>
                    <td>${Render.escape(svc.identification.statut_portfolio || "—")}</td>
                    <td>${Render.badgeCriticite(svc.meta.criticite)}</td>
                    <td>${Render.escape(svc.identification.hebergement || "—")}</td>
                    <td>${Render.escape(svc.identification.proprietaire || "—")}</td>
                    <td>${Render.escape(svc.identification.direction_beneficiaire || "—")}</td>
                    <td>${svc.meta.completude_pct}%</td>
                </tr>`
                  )
                  .join("")
            : `<tr><td colspan="8" class="empty-state">Aucun service ne correspond à ces critères.</td></tr>`;

        Render.setApp(`
            <div class="page-header">
                <h1>Portefeuille des services SI</h1>
                <p>${servicesData.total} services au total</p>
            </div>

            <form class="filter-bar" id="filter-form">
                <input type="text" name="q" placeholder="Recherche globale (nom, techno, prestataire...)" value="${Render.escape(query.q || "")}">
                <select name="statut_portfolio"><option value="">Statut portfolio</option>${options(references.statut_portfolio.values, query.statut_portfolio)}</select>
                <select name="criticite"><option value="">Criticité</option>${options(references.criticite.values, query.criticite)}</select>
                <select name="hebergement"><option value="">Hébergement</option>${options(references.hebergement, query.hebergement)}</select>
                <select name="mode_developpement"><option value="">Mode de développement</option>${options(references.mode_developpement, query.mode_developpement)}</select>
                <button type="submit" class="btn btn-primary">Filtrer</button>
                <a href="#/portefeuille" class="btn">Réinitialiser</a>
            </form>

            <div class="results-count">${servicesData.nb_resultats} résultat${servicesData.nb_resultats > 1 ? "s" : ""}</div>

            <div class="panel">
                <table class="data-table">
                    <thead>
                        <tr><th>ID</th><th>Nom</th><th>Statut Portfolio</th><th>Criticité</th><th>Hébergement</th><th>Propriétaire</th><th>Direction</th><th>Complétude</th></tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `);

        document.getElementById("filter-form").addEventListener("submit", (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const params = new URLSearchParams();
            for (const [key, value] of formData.entries()) {
                if (value) params.set(key, value);
            }
            const qs = params.toString();
            window.location.hash = `#/portefeuille${qs ? "?" + qs : ""}`;
        });
    } catch (e) {
        Render.error(e.message);
    }
};

// ---------- Fiche service ----------
Views.detail = async function (params) {
    Render.loading();
    try {
        const svc = await Api.getService(params.id);

        const section = (title, fields) => `
            <div class="panel">
                <div class="panel-header">${Render.escape(title)}</div>
                <div class="panel-body field-grid">${fields.map(([l, v]) => Render.field(l, v)).join("")}</div>
            </div>`;

        Render.setApp(`
            <div class="page-header">
                <h1>${Render.escape(svc.id)} · ${Render.escape(svc.identification.nom)}</h1>
                <p>
                    ${Render.badgeCriticite(svc.meta.criticite)}
                    · ${Render.escape(svc.identification.statut_portfolio || "Statut non renseigné")}
                    · Complétude ${svc.meta.completude_pct}%
                </p>
            </div>

            ${section("1 · Identification", [
                ["Catégorie", svc.identification.categorie],
                ["Propriétaire", svc.identification.proprietaire],
                ["Direction bénéficiaire", svc.identification.direction_beneficiaire],
                ["Date de création", svc.identification.date_creation],
                ["Hébergement", svc.identification.hebergement],
                ["Mode de développement", svc.identification.mode_developpement],
                ["Prestataire", svc.identification.prestataire],
            ])}

            ${section("2 · Proposition de valeur", [
                ["Objectif", svc.proposition_valeur.objectif],
                ["Problème métier résolu", svc.proposition_valeur.probleme_resolu],
                ["Bénéfices attendus", svc.proposition_valeur.benefices],
                ["Parties prenantes", svc.proposition_valeur.parties_prenantes],
            ])}

            ${section("3 · Description", [
                ["Description fonctionnelle", svc.description.fonctionnelle],
                ["Utilisateurs", svc.description.utilisateurs],
                ["Processus supportés", svc.description.processus_supportes],
                ["Fréquence d'utilisation", svc.description.frequence_utilisation],
            ])}

            ${section("4 · Architecture & dépendances", [
                ["Stack technologique", svc.architecture.stack_technologique],
                ["Infrastructure", svc.architecture.infrastructure],
                ["Données traitées", svc.architecture.donnees_traitees],
                ["Intégrations", svc.architecture.integrations],
            ])}

            ${section("5 · Sécurité & conformité", [
                ["Données sensibles", Render.boolField(svc.securite.donnees_sensibles)],
                ["Réglementation", svc.securite.reglementation],
                ["Classification sécurité", svc.securite.classification],
                ["Journalisation", Render.boolField(svc.securite.journalisation)],
                ["Sauvegarde", Render.boolField(svc.securite.sauvegarde)],
            ])}

            ${section("6 · Performance & SLA", [
                ["Disponibilité cible", svc.performance_sla.disponibilite_cible],
                ["RTO", svc.performance_sla.rto],
                ["RPO", svc.performance_sla.rpo],
                ["Support horaire", svc.performance_sla.support_horaire],
            ])}

            ${section("7 · Risques", [
                ["Risques principaux", svc.risques.risques_principaux],
                ["Impact en cas d'arrêt", svc.risques.impact_arret],
                ["Plan de continuité (PCA)", svc.risques.pca],
                ["Plan de mitigation", svc.risques.plan_mitigation],
            ])}

            ${section("8 · Cycle de vie", [
                ["Conception", svc.cycle_vie.conception],
                ["Déploiement", svc.cycle_vie.deploiement],
                ["Exploitation", svc.cycle_vie.exploitation],
                ["Amélioration", svc.cycle_vie.amelioration],
                ["Retrait", svc.cycle_vie.retrait],
            ])}

            <p><a href="#/portefeuille" class="btn">&larr; Retour au portefeuille</a></p>
        `);
    } catch (e) {
        if (e.status === 404) {
            Render.setApp(`<div class="page-header"><h1>Service introuvable</h1></div><div class="panel"><div class="panel-body empty-state">Aucun service ne correspond à l'ID demandé.<br><a href="#/portefeuille" class="btn btn-primary" style="margin-top:12px;">Retour au portefeuille</a></div></div>`);
        } else {
            Render.error(e.message);
        }
    }
};

// ---------- Qualité des données ----------
Views.quality = async function (params, query) {
    Render.loading();
    try {
        const { report, anomalie_filtre, services_filtres } = await Api.getQuality(query);

        const anomaliesHtml = Object.keys(report.anomalies).length
            ? `<ul class="alert-list">${Object.entries(report.anomalies)
                  .map(
                      ([label, ids]) => `
                <li>
                    <a href="#/qualite?anomalie=${encodeURIComponent(label)}">${Render.escape(label)}</a>
                    <span class="alert-count">${ids.length} service${ids.length > 1 ? "s" : ""}</span>
                </li>`
                  )
                  .join("")}</ul>`
            : `<p class="empty-state">Aucune anomalie détectée.</p>`;

        let drillHtml = "";
        if (anomalie_filtre && services_filtres) {
            drillHtml = `
                <div class="panel">
                    <div class="panel-header">Services concernés — ${Render.escape(anomalie_filtre)}</div>
                    <div class="panel-body">
                        <table class="data-table">
                            <thead><tr><th>ID</th><th>Nom</th><th>Statut Portfolio</th><th>Criticité</th></tr></thead>
                            <tbody>
                                ${services_filtres
                                    .map(
                                        (svc) => `
                                    <tr>
                                        <td>${Render.escape(svc.id)}</td>
                                        <td><a href="#/portefeuille/${encodeURIComponent(svc.id)}">${Render.escape(svc.identification.nom)}</a></td>
                                        <td>${Render.escape(svc.identification.statut_portfolio || "—")}</td>
                                        <td>${Render.escape(svc.meta.criticite || "—")}</td>
                                    </tr>`
                                    )
                                    .join("")}
                            </tbody>
                        </table>
                    </div>
                </div>`;
        }

        Render.setApp(`
            <div class="page-header">
                <h1>Qualité des données</h1>
                <p>Complétude et anomalies du portefeuille</p>
            </div>

            <div class="kpi-grid">
                <div class="kpi-card"><div class="kpi-value">${report.completude.total}</div><div class="kpi-label">Services au total</div></div>
                <div class="kpi-card"><div class="kpi-value">${report.completude.completes}</div><div class="kpi-label">Fiches complètes (&ge;${report.completude.seuil_pct}%)</div></div>
                <div class="kpi-card"><div class="kpi-value">${report.completude.incompletes}</div><div class="kpi-label">Fiches incomplètes</div></div>
                <div class="kpi-card"><div class="kpi-value">${report.completude.taux_completude_pct}%</div><div class="kpi-label">Taux de complétude moyen</div></div>
                <div class="kpi-card"><div class="kpi-value">${report.nb_anomalies_total}</div><div class="kpi-label">Anomalies détectées</div></div>
            </div>

            <div class="panel">
                <div class="panel-header">Anomalies par catégorie</div>
                <div class="panel-body">${anomaliesHtml}</div>
            </div>

            ${drillHtml}
        `);
    } catch (e) {
        Render.error(e.message);
    }
};

// ---------- Placeholders (pages futures) ----------
const PLACEHOLDERS = {
    "/analyses": ["Analyses", "Graphiques de répartition détaillés — prévu V0.5/V0.6."],
    "/rapports": ["Rapports", "Génération PDF (WeasyPrint) — prévu V0.8."],
    "/importer": ["Importer", "Import Excel avec aperçu et validation — prévu V0.7."],
    "/exporter": ["Exporter", "Export Excel enrichi — prévu V0.7."],
    "/parametres": ["Paramètres", "Référentiels et gestion des backups — prévu V0.9."],
};

Views.placeholder = function (params) {
    const [title, desc] = PLACEHOLDERS[params.path] || ["Page", "Contenu non disponible."];
    Render.setApp(`
        <div class="page-header"><h1>${Render.escape(title)}</h1></div>
        <div class="panel"><div class="panel-body empty-state">${Render.escape(desc)}</div></div>
    `);
};

Views.notFound = function () {
    Render.setApp(`
        <div class="page-header"><h1>404 — Page introuvable</h1></div>
        <div class="panel"><div class="panel-body empty-state">
            La page demandée n'existe pas.
            <br><a href="#/" class="btn btn-primary" style="margin-top:12px;">Retour au tableau de bord</a>
        </div></div>
    `);
};
