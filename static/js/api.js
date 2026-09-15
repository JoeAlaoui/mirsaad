/**
 * Client API MIRSAAD — encapsule les appels fetch vers le backend Flask.
 */
const Api = {
    async _get(url) {
        const res = await fetch(url);
        if (!res.ok) {
            const body = await res.json().catch(() => ({}));
            const err = new Error(body.error || `Erreur HTTP ${res.status}`);
            err.status = res.status;
            throw err;
        }
        return res.json();
    },

    getDashboard() {
        return this._get("/api/dashboard");
    },

    getServices(params = {}) {
        const qs = new URLSearchParams(
            Object.fromEntries(Object.entries(params).filter(([, v]) => v))
        ).toString();
        return this._get(`/api/services${qs ? "?" + qs : ""}`);
    },

    getService(id) {
        return this._get(`/api/services/${encodeURIComponent(id)}`);
    },

    getQuality(params = {}) {
        const qs = new URLSearchParams(
            Object.fromEntries(Object.entries(params).filter(([, v]) => v))
        ).toString();
        return this._get(`/api/quality${qs ? "?" + qs : ""}`);
    },

    getReferences() {
        return this._get("/api/references");
    },
};
