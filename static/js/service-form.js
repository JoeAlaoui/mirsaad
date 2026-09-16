/**
 * Schéma déclaratif du formulaire service : une seule source de vérité pour générer
 * le HTML (création/édition) et pour collecter les données soumises en objet imbriqué.
 * Ajouter un champ = une ligne dans FORM_SCHEMA, rien à dupliquer ailleurs.
 */
const FORM_SCHEMA = [
    {
        section: "identification", title: "1 · Identification",
        fields: [
            { key: "nom", label: "Nom du service *", type: "text", required: true },
            { key: "categorie", label: "Catégorie", type: "select", refKey: "categorie" },
            { key: "proprietaire", label: "Propriétaire", type: "text" },
            { key: "direction_beneficiaire", label: "Direction bénéficiaire", type: "text" },
            { key: "date_creation", label: "Date de création", type: "text" },
            { key: "statut_portfolio", label: "Statut Portfolio", type: "select", refKey: "statut_portfolio" },
            { key: "hebergement", label: "Hébergement", type: "select", refKey: "hebergement" },
            { key: "mode_developpement", label: "Mode de développement", type: "select", refKey: "mode_developpement" },
            { key: "prestataire", label: "Prestataire", type: "text" },
        ],
    },
    {
        section: "proposition_valeur", title: "2 · Proposition de valeur",
        fields: [
            { key: "objectif", label: "Objectif", type: "textarea" },
            { key: "probleme_resolu", label: "Problème métier résolu", type: "textarea" },
            { key: "benefices", label: "Bénéfices attendus", type: "textarea" },
            { key: "parties_prenantes", label: "Parties prenantes", type: "text" },
        ],
    },
    {
        section: "description", title: "3 · Description",
        fields: [
            { key: "fonctionnelle", label: "Description fonctionnelle", type: "textarea" },
            { key: "utilisateurs", label: "Utilisateurs", type: "text" },
            { key: "processus_supportes", label: "Processus supportés", type: "text" },
            { key: "frequence_utilisation", label: "Fréquence d'utilisation", type: "text" },
        ],
    },
    {
        section: "architecture", title: "4 · Architecture & dépendances",
        fields: [
            { key: "stack_technologique", label: "Stack technologique", type: "text" },
            { key: "infrastructure", label: "Infrastructure", type: "text" },
            { key: "donnees_traitees", label: "Données traitées", type: "text" },
            { key: "integrations", label: "Intégrations", type: "text" },
        ],
    },
    {
        section: "securite", title: "5 · Sécurité & conformité",
        fields: [
            { key: "donnees_sensibles", label: "Données sensibles", type: "checkbox" },
            { key: "reglementation", label: "Réglementation", type: "text" },
            { key: "classification", label: "Classification sécurité", type: "text" },
            { key: "journalisation", label: "Journalisation", type: "checkbox" },
            { key: "sauvegarde", label: "Sauvegarde", type: "checkbox" },
        ],
    },
    {
        section: "performance_sla", title: "6 · Performance & SLA",
        fields: [
            { key: "disponibilite_cible", label: "Disponibilité cible", type: "text" },
            { key: "rto", label: "RTO", type: "text" },
            { key: "rpo", label: "RPO", type: "text" },
            { key: "support_horaire", label: "Support horaire", type: "text" },
        ],
    },
    {
        section: "risques", title: "7 · Risques",
        fields: [
            { key: "risques_principaux", label: "Risques principaux", type: "textarea" },
            { key: "impact_arret", label: "Impact en cas d'arrêt", type: "textarea" },
            { key: "pca", label: "Plan de continuité (PCA)", type: "text" },
            { key: "plan_mitigation", label: "Plan de mitigation", type: "textarea" },
        ],
    },
    {
        section: "cycle_vie", title: "8 · Cycle de vie",
        fields: [
            { key: "conception", label: "Conception", type: "lifecycle" },
            { key: "deploiement", label: "Déploiement", type: "lifecycle" },
            { key: "exploitation", label: "Exploitation", type: "lifecycle" },
            { key: "amelioration", label: "Amélioration", type: "lifecycle" },
            { key: "retrait", label: "Retrait", type: "lifecycle" },
        ],
    },
];

const LIFECYCLE_OPTIONS = [
    { value: "", label: "—" },
    { value: "en_cours", label: "En cours" },
    { value: "fait", label: "Fait" },
];

const ServiceForm = {
    render(svc, references) {
        const get = (section, key) => (svc && svc[section] ? svc[section][key] : null);

        const fieldHtml = (section, field) => {
            const name = `${section}.${field.key}`;
            const value = get(section, field.key);

            if (field.type === "checkbox") {
                const checked = value === true ? "checked" : "";
                return `
                    <label class="form-field form-field-checkbox">
                        <input type="checkbox" name="${name}" ${checked}>
                        <span>${Render.escape(field.label)}</span>
                    </label>`;
            }

            if (field.type === "textarea") {
                return `
                    <label class="form-field form-field-wide">
                        <span>${Render.escape(field.label)}</span>
                        <textarea name="${name}" rows="3">${Render.escape(value)}</textarea>
                    </label>`;
            }

            if (field.type === "select") {
                const options = (references[field.refKey] && (references[field.refKey].values || references[field.refKey])) || [];
                return `
                    <label class="form-field">
                        <span>${Render.escape(field.label)}</span>
                        <select name="${name}">
                            <option value="">—</option>
                            ${options.map((o) => `<option value="${Render.escape(o)}" ${o === value ? "selected" : ""}>${Render.escape(o)}</option>`).join("")}
                        </select>
                    </label>`;
            }

            if (field.type === "lifecycle") {
                return `
                    <label class="form-field">
                        <span>${Render.escape(field.label)}</span>
                        <select name="${name}">
                            ${LIFECYCLE_OPTIONS.map((o) => `<option value="${o.value}" ${o.value === (value || "") ? "selected" : ""}>${o.label}</option>`).join("")}
                        </select>
                    </label>`;
            }

            return `
                <label class="form-field">
                    <span>${Render.escape(field.label)}</span>
                    <input type="text" name="${name}" value="${Render.escape(value)}" ${field.required ? "required" : ""}>
                </label>`;
        };

        // Champs de meta.criticite / meta.statut, ajoutés hors schéma (section réservée)
        const metaCriticite = svc ? svc.meta.criticite : null;
        const metaStatut = svc ? svc.meta.statut : null;
        const metaHtml = `
            <div class="panel">
                <div class="panel-header">Pilotage</div>
                <div class="panel-body form-grid">
                    <label class="form-field">
                        <span>Statut</span>
                        <select name="meta.statut">
                            <option value="">—</option>
                            ${(references.statut ? references.statut.values || references.statut : ["En production", "En projet", "Obsolète / Arrêt"])
                                .map((o) => `<option value="${Render.escape(o)}" ${o === metaStatut ? "selected" : ""}>${Render.escape(o)}</option>`)
                                .join("")}
                        </select>
                    </label>
                    <label class="form-field">
                        <span>Criticité</span>
                        <select name="meta.criticite">
                            <option value="">—</option>
                            ${(references.criticite.values || references.criticite)
                                .map((o) => `<option value="${Render.escape(o)}" ${o === metaCriticite ? "selected" : ""}>${Render.escape(o)}</option>`)
                                .join("")}
                        </select>
                    </label>
                </div>
            </div>`;

        const sectionsHtml = FORM_SCHEMA.map(
            (sec) => `
            <div class="panel">
                <div class="panel-header">${Render.escape(sec.title)}</div>
                <div class="panel-body form-grid">
                    ${sec.fields.map((f) => fieldHtml(sec.section, f)).join("")}
                </div>
            </div>`
        ).join("");

        return sectionsHtml + metaHtml;
    },

    collect(formEl) {
        const payload = {};
        const formData = new FormData(formEl);

        // Champs texte/select/textarea
        for (const [name, rawValue] of formData.entries()) {
            const [section, key] = name.split(".");
            if (!payload[section]) payload[section] = {};
            payload[section][key] = rawValue.trim() === "" ? null : rawValue;
        }

        // Cases à cocher : FormData omet celles décochées, il faut les parcourir explicitement
        formEl.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
            const [section, key] = cb.name.split(".");
            if (!payload[section]) payload[section] = {};
            payload[section][key] = cb.checked;
        });

        return payload;
    },
};
