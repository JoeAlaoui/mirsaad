/**
 * Vues MIRSAAD. Chaque fonction reçoit les paramètres de route (params) et
 * une query object (query), fetch les données via Api, injecte le HTML puis,
 * le cas échéant, instancie les graphiques (après que les <canvas> existent dans le DOM).
 */
const Views = {};

function orgLabel() {
    return (window.MirsaadSettings && window.MirsaadSettings.organisation_name) || "votre organisation";
}

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

        const hasData = kpis.total > 0;

        Render.setApp(`
            <div class="page-header">
                <h1>Tableau de bord</h1>
                <p>Vue consolidée du portefeuille de ${Render.escape(orgLabel())} — ${metadata.total_services} services${metadata.last_updated ? " · dernière mise à jour " + Render.escape(metadata.last_updated) : ""}</p>
            </div>

            <div class="kpi-grid">
                <div class="kpi-card kpi-anim"><div class="kpi-value">${kpis.total}</div><div class="kpi-label">Total services</div></div>
                <div class="kpi-card kpi-anim"><div class="kpi-value">${kpis.par_statut_portfolio.Catalogue || 0}</div><div class="kpi-label">En catalogue (production)</div></div>
                <div class="kpi-card kpi-anim"><div class="kpi-value">${kpis.par_statut_portfolio.Pipeline || 0}</div><div class="kpi-label">En pipeline</div></div>
                <div class="kpi-card kpi-anim"><div class="kpi-value">${kpis.par_criticite.Critique || 0}</div><div class="kpi-label">Criticité critique</div></div>
                <div class="kpi-card kpi-anim"><div class="kpi-value">${kpis.couverture_gouvernance_pct}%</div><div class="kpi-label">Couverture gouvernance</div></div>
                <div class="kpi-card kpi-anim"><div class="kpi-value">${kpis.couverture_continuite_pct}%</div><div class="kpi-label">Couverture continuité (RTO/RPO)</div></div>
                <div class="kpi-card kpi-anim"><div class="kpi-value">${kpis.taux_dependance_prestataire_pct}%</div><div class="kpi-label">Dépendance prestataire</div></div>
                <div class="kpi-card kpi-anim"><div class="kpi-value">${kpis.completude_moyenne_pct}%</div><div class="kpi-label">Complétude moyenne</div></div>
            </div>

            <div class="panel">
                <div class="panel-header">Points d'attention — veille du portefeuille</div>
                <div class="panel-body">${anomaliesHtml}</div>
            </div>

            ${hasData ? `
            <div class="chart-grid">
                <div class="panel">
                    <div class="panel-header">Répartition par criticité</div>
                    <div class="panel-body"><div class="chart-box"><canvas id="chart-criticite"></canvas></div></div>
                </div>
                <div class="panel">
                    <div class="panel-header">Répartition par hébergement</div>
                    <div class="panel-body"><div class="chart-box"><canvas id="chart-hebergement"></canvas></div></div>
                </div>
            </div>
            <div class="panel">
                <div class="panel-header">Répartition par mode de développement</div>
                <div class="panel-body"><div class="chart-box chart-box-wide"><canvas id="chart-mode-dev"></canvas></div></div>
            </div>
            ` : `<div class="panel"><div class="panel-body empty-state">Aucune donnée à visualiser — importez un portefeuille pour activer les graphiques.</div></div>`}
        `);

        if (hasData) {
            const critLabels = Object.keys(kpis.par_criticite);
            Charts.doughnut(
                "chart-criticite",
                critLabels,
                Object.values(kpis.par_criticite),
                critLabels.map((l) => Charts.criticitePalette[l] || "#4b5568")
            );
            Charts.doughnut("chart-hebergement", Object.keys(kpis.par_hebergement), Object.values(kpis.par_hebergement));
            Charts.bar("chart-mode-dev", Object.keys(kpis.par_mode_developpement), Object.values(kpis.par_mode_developpement));
        }
    } catch (e) {
        Render.error(e.message);
    }
};

// ---------- Analyses ----------
Views.analyses = async function () {
    Render.loading();
    try {
        const { kpis } = await Api.getDashboard();

        if (kpis.total === 0) {
            Render.setApp(`
                <div class="page-header"><h1>Analyses</h1></div>
                <div class="panel"><div class="panel-body empty-state">Aucune donnée à analyser — importez un portefeuille pour activer les graphiques.</div></div>
            `);
            return;
        }

        Render.setApp(`
            <div class="page-header">
                <h1>Analyses</h1>
                <p>Répartitions détaillées du portefeuille — ${kpis.total} services</p>
            </div>

            <div class="chart-grid">
                <div class="panel"><div class="panel-header">Criticité</div><div class="panel-body"><div class="chart-box"><canvas id="a-criticite"></canvas></div></div></div>
                <div class="panel"><div class="panel-header">Statut Portfolio</div><div class="panel-body"><div class="chart-box"><canvas id="a-statut"></canvas></div></div></div>
                <div class="panel"><div class="panel-header">Hébergement</div><div class="panel-body"><div class="chart-box"><canvas id="a-hebergement"></canvas></div></div></div>
                <div class="panel"><div class="panel-header">Catégorie</div><div class="panel-body"><div class="chart-box"><canvas id="a-categorie"></canvas></div></div></div>
            </div>

            <div class="panel">
                <div class="panel-header">Mode de développement</div>
                <div class="panel-body"><div class="chart-box chart-box-wide"><canvas id="a-mode-dev"></canvas></div></div>
            </div>

            <div class="panel">
                <div class="panel-header">Répartition par direction bénéficiaire</div>
                <div class="panel-body"><div class="chart-box chart-box-wide"><canvas id="a-direction"></canvas></div></div>
            </div>

            <div class="panel">
                <div class="panel-header">Concentration prestataire</div>
                <div class="panel-body"><div class="chart-box chart-box-wide"><canvas id="a-prestataire"></canvas></div></div>
            </div>
        `);

        const critLabels = Object.keys(kpis.par_criticite);
        Charts.doughnut("a-criticite", critLabels, Object.values(kpis.par_criticite), critLabels.map((l) => Charts.criticitePalette[l] || "#4b5568"));
        Charts.doughnut("a-statut", Object.keys(kpis.par_statut_portfolio), Object.values(kpis.par_statut_portfolio));
        Charts.doughnut("a-hebergement", Object.keys(kpis.par_hebergement), Object.values(kpis.par_hebergement));
        Charts.doughnut("a-categorie", Object.keys(kpis.par_categorie), Object.values(kpis.par_categorie));
        Charts.bar("a-mode-dev", Object.keys(kpis.par_mode_developpement), Object.values(kpis.par_mode_developpement));

        const directions = Object.entries(kpis.par_direction_beneficiaire).sort((a, b) => b[1] - a[1]).slice(0, 10);
        Charts.horizontalBar("a-direction", directions.map((d) => d[0]), directions.map((d) => d[1]));

        const prestataires = Object.entries(kpis.par_prestataire).sort((a, b) => b[1] - a[1]).slice(0, 10);
        if (prestataires.length) {
            Charts.horizontalBar("a-prestataire", prestataires.map((p) => p[0]), prestataires.map((p) => p[1]), "#7a3ea1");
        } else {
            document.getElementById("a-prestataire").closest(".panel-body").innerHTML = '<p class="empty-state">Aucun prestataire renseigné.</p>';
        }
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
                    <td>
                        <div class="completude-bar" title="${svc.meta.completude_pct}%">
                            <div class="completude-fill" style="width:${svc.meta.completude_pct}%"></div>
                        </div>
                    </td>
                </tr>`
                  )
                  .join("")
            : `<tr><td colspan="8" class="empty-state">Aucun service ne correspond à ces critères.<br><a href="#/importer" class="btn btn-primary" style="margin-top:10px;">Importer un portefeuille</a></td></tr>`;

        Render.setApp(`
            <div class="page-header page-header-row">
                <div>
                    <h1>Portefeuille des services SI</h1>
                    <p>${servicesData.total} services au total</p>
                </div>
                <a href="#/portefeuille/nouveau" class="btn btn-primary">+ Ajouter un service</a>
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
            <div class="page-header page-header-row">
                <div>
                    <h1>${Render.escape(svc.id)} · ${Render.escape(svc.identification.nom)}</h1>
                    <p>
                        ${Render.badgeCriticite(svc.meta.criticite)}
                        · ${Render.escape(svc.identification.statut_portfolio || "Statut non renseigné")}
                        · Complétude ${svc.meta.completude_pct}%
                    </p>
                </div>
                <div class="header-actions">
                    <a href="#/portefeuille/${encodeURIComponent(svc.id)}/modifier" class="btn">Modifier</a>
                    <button type="button" id="delete-btn" class="btn btn-danger">Supprimer</button>
                </div>
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

        document.getElementById("delete-btn").addEventListener("click", async () => {
            if (!Render.confirmAction(`Supprimer définitivement « ${svc.identification.nom} » (${svc.id}) ?\nUne sauvegarde sera créée avant suppression.`)) {
                return;
            }
            try {
                await Api.deleteService(svc.id);
                Render.toast(`Le service « ${svc.identification.nom} » a été supprimé. Une sauvegarde a été créée.`, "success");
                window.location.hash = "#/portefeuille";
            } catch (e) {
                Render.toast(`Erreur lors de la suppression : ${e.message}`, "error");
            }
        });
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
                <div class="kpi-card kpi-anim"><div class="kpi-value">${report.completude.total}</div><div class="kpi-label">Services au total</div></div>
                <div class="kpi-card kpi-anim"><div class="kpi-value">${report.completude.completes}</div><div class="kpi-label">Fiches complètes (&ge;${report.completude.seuil_pct}%)</div></div>
                <div class="kpi-card kpi-anim"><div class="kpi-value">${report.completude.incompletes}</div><div class="kpi-label">Fiches incomplètes</div></div>
                <div class="kpi-card kpi-anim"><div class="kpi-value">${report.completude.taux_completude_pct}%</div><div class="kpi-label">Taux de complétude moyen</div></div>
                <div class="kpi-card kpi-anim"><div class="kpi-value">${report.nb_anomalies_total}</div><div class="kpi-label">Anomalies détectées</div></div>
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

// ---------- Paramètres ----------
Views.settings = async function () {
    Render.loading();
    try {
        const settings = await Api.getSettings();

        Render.setApp(`
            <div class="page-header">
                <h1>Paramètres</h1>
                <p>Identité de l'organisation et réglages de l'application</p>
            </div>

            <form class="panel" id="settings-form">
                <div class="panel-header">Identité</div>
                <div class="panel-body settings-grid">
                    <label>Nom de l'organisation *
                        <input type="text" name="organisation_name" value="${Render.escape(settings.organisation_name)}" required>
                    </label>
                    <label>Nom complet / officiel (optionnel)
                        <input type="text" name="organisation_name_complete" value="${Render.escape(settings.organisation_name_complete)}">
                    </label>
                    <label>Nom de l'application
                        <input type="text" name="application_name" value="${Render.escape(settings.application_name)}" required>
                    </label>
                    <label>Nom de l'application (arabe)
                        <input type="text" name="application_name_ar" value="${Render.escape(settings.application_name_ar)}">
                    </label>
                </div>
            </form>

            <form class="panel" id="settings-form-2">
                <div class="panel-header">Qualité des données</div>
                <div class="panel-body settings-grid">
                    <label>Seuil de complétude d'une fiche "complète" (%)
                        <input type="number" name="seuil_completude_pct" min="0" max="100" value="${settings.seuil_completude_pct}" required>
                    </label>
                </div>
            </form>

            <div id="settings-feedback"></div>
            <button type="button" id="settings-save" class="btn btn-primary">Enregistrer les paramètres</button>
        `);

        document.getElementById("settings-save").addEventListener("click", async () => {
            const feedback = document.getElementById("settings-feedback");
            const data1 = new FormData(document.getElementById("settings-form"));
            const data2 = new FormData(document.getElementById("settings-form-2"));
            const payload = Object.fromEntries([...data1.entries(), ...data2.entries()]);
            payload.seuil_completude_pct = parseInt(payload.seuil_completude_pct, 10);

            try {
                const updated = await Api.updateSettings(payload);
                Render.applySettings(updated);
                feedback.innerHTML = `<p class="feedback-success">Paramètres enregistrés avec succès. Une sauvegarde a été créée.</p>`;
            } catch (e) {
                feedback.innerHTML = `<p class="feedback-error">Erreur : ${Render.escape(e.message)}</p>`;
            }
        });
    } catch (e) {
        Render.error(e.message);
    }
};

// ---------- Création / édition de service ----------
Views.serviceCreate = async function () {
    Render.loading();
    try {
        const references = await Api.getReferences();

        Render.setApp(`
            <div class="page-header"><h1>Ajouter un service</h1></div>
            <form id="service-form">
                ${ServiceForm.render(null, references)}
                <div id="form-feedback"></div>
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">Créer le service</button>
                    <a href="#/portefeuille" class="btn">Annuler</a>
                </div>
            </form>
        `);

        document.getElementById("service-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const feedback = document.getElementById("form-feedback");
            const payload = ServiceForm.collect(e.target);
            try {
                const svc = await Api.createService(payload);
                Render.toast(`Service « ${svc.identification.nom} » créé avec succès (${svc.id}).`, "success");
                window.location.hash = `#/portefeuille/${encodeURIComponent(svc.id)}`;
            } catch (err) {
                feedback.innerHTML = `<p class="feedback-error">${Render.escape(err.message)}</p>`;
            }
        });
    } catch (e) {
        Render.error(e.message);
    }
};

Views.serviceEdit = async function (params) {
    Render.loading();
    try {
        const [svc, references] = await Promise.all([Api.getService(params.id), Api.getReferences()]);

        Render.setApp(`
            <div class="page-header"><h1>Modifier · ${Render.escape(svc.identification.nom)}</h1></div>
            <form id="service-form">
                ${ServiceForm.render(svc, references)}
                <div id="form-feedback"></div>
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">Enregistrer les modifications</button>
                    <a href="#/portefeuille/${encodeURIComponent(svc.id)}" class="btn">Annuler</a>
                </div>
            </form>
        `);

        document.getElementById("service-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const feedback = document.getElementById("form-feedback");
            const payload = ServiceForm.collect(e.target);
            try {
                const updated = await Api.updateService(svc.id, payload);
                Render.toast("Service mis à jour avec succès.", "success");
                window.location.hash = `#/portefeuille/${encodeURIComponent(updated.id)}`;
            } catch (err) {
                feedback.innerHTML = `<p class="feedback-error">${Render.escape(err.message)}</p>`;
            }
        });
    } catch (e) {
        if (e.status === 404) {
            Render.setApp(`<div class="page-header"><h1>Service introuvable</h1></div><div class="panel"><div class="panel-body empty-state"><a href="#/portefeuille" class="btn btn-primary">Retour au portefeuille</a></div></div>`);
        } else {
            Render.error(e.message);
        }
    }
};

// ---------- Importer ----------
Views.importer = function () {
    Render.setApp(`
        <div class="page-header">
            <h1>Importer un portefeuille</h1>
            <p>Formats acceptés : JSON natif MIRSAAD ou Excel (modèle simplifié à plat, une ligne par service)</p>
        </div>

        <div class="panel">
            <div class="panel-body">
                <input type="file" id="import-file" accept=".json,.xlsx">
                <button type="button" id="import-analyze-btn" class="btn btn-primary" style="margin-left:10px;">Analyser le fichier</button>
            </div>
        </div>

        <div id="import-preview"></div>
    `);

    document.getElementById("import-analyze-btn").addEventListener("click", async () => {
        const fileInput = document.getElementById("import-file");
        const previewZone = document.getElementById("import-preview");
        if (!fileInput.files.length) {
            Render.toast("Sélectionnez un fichier à importer.", "error");
            return;
        }

        previewZone.innerHTML = '<div class="panel"><div class="panel-body empty-state">Analyse en cours...</div></div>';

        try {
            const { token, preview } = await Api.importPreview(fileInput.files[0]);
            const r = preview.resume;

            const errorsHtml = preview.erreurs.length
                ? `<ul class="alert-list">${preview.erreurs.map((e) => `<li><span>Ligne ${e.ligne}</span><span>${Render.escape(e.message)}</span></li>`).join("")}</ul>`
                : "";

            const listNames = (items) => items.map((s) => Render.escape(s.identification ? s.identification.nom : s.nom)).join(", ") || "—";

            previewZone.innerHTML = `
                <div class="kpi-grid">
                    <div class="kpi-card"><div class="kpi-value">${r.nouveaux}</div><div class="kpi-label">Nouveaux services</div></div>
                    <div class="kpi-card"><div class="kpi-value">${r.modifies}</div><div class="kpi-label">Services modifiés</div></div>
                    <div class="kpi-card"><div class="kpi-value">${r.inchanges}</div><div class="kpi-label">Inchangés</div></div>
                    <div class="kpi-card"><div class="kpi-value">${r.doublons_fichier}</div><div class="kpi-label">Doublons dans le fichier</div></div>
                    <div class="kpi-card"><div class="kpi-value">${r.erreurs}</div><div class="kpi-label">Erreurs</div></div>
                </div>

                <div class="panel">
                    <div class="panel-header">Détail</div>
                    <div class="panel-body field-grid">
                        ${Render.field("Nouveaux", listNames(preview.nouveaux))}
                        ${Render.field("Modifiés", listNames(preview.modifies))}
                    </div>
                </div>

                ${preview.erreurs.length ? `<div class="panel"><div class="panel-header">Erreurs</div><div class="panel-body">${errorsHtml}</div></div>` : ""}

                <div class="panel">
                    <div class="panel-header">Stratégie d'import</div>
                    <div class="panel-body">
                        <div class="filter-bar">
                            <select id="import-strategy">
                                <option value="maj">Mise à jour par ID (recommandé) — met à jour les existants, ajoute les nouveaux</option>
                                <option value="ajouter">Ajouter uniquement — ignore les services déjà présents</option>
                                <option value="remplacer">Remplacer entièrement le portefeuille</option>
                            </select>
                            <button type="button" id="import-confirm-btn" class="btn btn-primary">Confirmer l'import</button>
                        </div>
                    </div>
                </div>
            `;

            document.getElementById("import-confirm-btn").addEventListener("click", async () => {
                const strategy = document.getElementById("import-strategy").value;
                if (!Render.confirmAction("Confirmer l'import selon la stratégie sélectionnée ? Une sauvegarde sera créée avant toute écriture.")) {
                    return;
                }
                try {
                    const result = await Api.importConfirm(token, strategy);
                    Render.toast(`Import terminé — portefeuille : ${result.total_services} services.`, "success");
                    window.location.hash = "#/portefeuille";
                } catch (e) {
                    Render.toast(`Erreur lors de l'import : ${e.message}`, "error");
                }
            });
        } catch (e) {
            previewZone.innerHTML = `<div class="panel"><div class="panel-body empty-state">Erreur : ${Render.escape(e.message)}</div></div>`;
        }
    });
};

// ---------- Exporter ----------
Views.exporter = function () {
    Render.setApp(`
        <div class="page-header">
            <h1>Exporter le portefeuille</h1>
            <p>Fichier Excel avec synthèse et inventaire complet, réimportable tel quel</p>
        </div>

        <div class="panel">
            <div class="panel-body">
                <p>L'export contient une feuille <strong>Synthèse</strong> (KPI) et une feuille
                <strong>Inventaire</strong> (un service par ligne, filtres et volets figés activés).</p>
                <a href="/api/export/excel" class="btn btn-primary">Télécharger l'export Excel</a>
            </div>
        </div>
    `);
};

// ---------- Placeholders (pages futures) ----------
const PLACEHOLDERS = {
    "/rapports": ["Rapports", "Génération PDF (WeasyPrint) — prévu V0.8."],
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
