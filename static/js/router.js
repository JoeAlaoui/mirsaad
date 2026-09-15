/**
 * Routeur SPA à base de hash (#/chemin?query).
 * Pas de dépendance externe : History/hashchange natifs.
 */
const Router = {
    routes: [
        { pattern: /^\/$/, view: "dashboard" },
        { pattern: /^\/portefeuille$/, view: "portfolio" },
        { pattern: /^\/portefeuille\/([^/]+)$/, view: "detail", params: ["id"] },
        { pattern: /^\/qualite$/, view: "quality" },
        { pattern: /^\/(analyses|rapports|importer|exporter|parametres)$/, view: "placeholder", params: ["path"], isPath: true },
    ],

    parseHash() {
        const raw = window.location.hash.replace(/^#/, "") || "/";
        const [path, queryString] = raw.split("?");
        const query = Object.fromEntries(new URLSearchParams(queryString || ""));
        return { path: path || "/", query };
    },

    async resolve() {
        const { path, query } = this.parseHash();
        Render.setActiveNav(path);

        for (const route of this.routes) {
            const match = path.match(route.pattern);
            if (match) {
                const params = {};
                if (route.params) {
                    route.params.forEach((name, i) => {
                        params[name] = route.isPath ? path : match[i + 1];
                    });
                }
                await Views[route.view](params, query);
                return;
            }
        }
        Views.notFound();
    },

    init() {
        window.addEventListener("hashchange", () => this.resolve());
        this.resolve();
    },
};
