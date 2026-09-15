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
        document.getElementById("app").innerHTML = html;
    },

    setActiveNav(path) {
        document.querySelectorAll("#main-nav a").forEach((a) => {
            const route = a.getAttribute("data-route");
            a.classList.toggle("active", route === path || (route === "/portefeuille" && path.startsWith("/portefeuille")) || (route === "/qualite" && path.startsWith("/qualite")));
        });
    },

    loading() {
        this.setApp('<div class="empty-state">Chargement...</div>');
    },

    error(message) {
        this.setApp(`<div class="panel"><div class="panel-body empty-state">Erreur : ${this.escape(message)}</div></div>`);
    },
};
