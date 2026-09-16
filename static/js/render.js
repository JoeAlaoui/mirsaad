/**
 * Helpers de rendu partagés entre les vues.
 */
const Render = {
    escape(str) {
        if (str === null || str === undefined) return "";
        const div = document.createElement("div");
        div.textContent = String(str);
        return div.innerHTML;
    },

    badgeCriticite(criticite) {
        const map = {
            "Critique": "badge-critique",
            "Élevée": "badge-elevee",
            "Moyenne": "badge-moyenne",
            "Faible": "badge-faible",
        };
        const cls = map[criticite] || "badge-neutral";
        const label = criticite || "—";
        return `<span class="badge ${cls}">${this.escape(label)}</span>`;
    },

    field(label, value) {
        const empty = value === null || value === undefined || value === "";
        return `
            <div class="field-label">${this.escape(label)}</div>
            <div class="field-value ${empty ? "empty" : ""}">${empty ? "Non renseigné" : this.escape(value)}</div>
        `;
    },

    boolField(value) {
        if (value === null || value === undefined) return null;
        return value ? "Oui" : "Non";
    },

    setApp(html) {
        Charts.destroyAll();
        const app = document.getElementById("app");
        app.classList.remove("view-enter");
        app.innerHTML = html;
        // force reflow pour rejouer l'animation d'entrée à chaque changement de vue
        void app.offsetWidth;
        app.classList.add("view-enter");
    },

    setActiveNav(path) {
        document.querySelectorAll("#main-nav a").forEach((a) => {
            const route = a.getAttribute("data-route");
            a.classList.toggle(
                "active",
                route === path ||
                    (route === "/portefeuille" && path.startsWith("/portefeuille")) ||
                    (route === "/qualite" && path.startsWith("/qualite"))
            );
        });
    },

    loading() {
        Charts.destroyAll();
        this.setApp(`
            <div class="skeleton-kpi-grid">
                ${Array(4).fill('<div class="skeleton-card"></div>').join("")}
            </div>
            <div class="skeleton-panel"></div>
        `);
    },

    error(message) {
        this.setApp(`<div class="panel"><div class="panel-body empty-state">Erreur : ${this.escape(message)}</div></div>`);
    },

    // ---------- Branding dynamique (paramètres) ----------
    applySettings(settings) {
        window.MirsaadSettings = settings;
        const appName = settings.application_name || "MIRSAAD";
        const appNameAr = settings.application_name_ar || "";
        const org = settings.organisation_name || "votre organisation";

        document.getElementById("page-title").textContent = appName;
        document.getElementById("brand-name").textContent = appName;
        document.getElementById("brand-name-ar").textContent = appNameAr;
        document.getElementById("footer-org").textContent = org;
    },

    // ---------- Notifications ----------
    toast(message, type = "success") {
        let container = document.getElementById("toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "toast-container";
            document.body.appendChild(container);
        }
        const el = document.createElement("div");
        el.className = `toast toast-${type}`;
        el.textContent = message;
        container.appendChild(el);

        setTimeout(() => el.classList.add("toast-out"), 3200);
        setTimeout(() => el.remove(), 3600);
    },

    confirmAction(message) {
        return window.confirm(message);
    },
};
