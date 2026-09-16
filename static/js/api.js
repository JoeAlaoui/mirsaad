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

    async _send(url, method, payload) {
        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const body = await res.json();
        if (!res.ok) {
            const err = new Error(body.error || `Erreur HTTP ${res.status}`);
            err.status = res.status;
            throw err;
        }
        return body;
    },

    createService(payload) {
        return this._send("/api/services", "POST", payload);
    },

    updateService(id, payload) {
        return this._send(`/api/services/${encodeURIComponent(id)}`, "PUT", payload);
    },

    async deleteService(id) {
        const res = await fetch(`/api/services/${encodeURIComponent(id)}`, { method: "DELETE" });
        const body = await res.json();
        if (!res.ok) {
            const err = new Error(body.error || `Erreur HTTP ${res.status}`);
            err.status = res.status;
            throw err;
        }
        return body;
    },

    async importPreview(file) {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch("/api/import/preview", { method: "POST", body: formData });
        const body = await res.json();
        if (!res.ok) {
            const err = new Error(body.error || `Erreur HTTP ${res.status}`);
            throw err;
        }
        return body;
    },

    importConfirm(token, strategy) {
        return this._send("/api/import/confirm", "POST", { token, strategy });
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

    getSettings() {
        return this._get("/api/settings");
    },

    async updateSettings(payload) {
        const res = await fetch("/api/settings", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const body = await res.json();
        if (!res.ok) {
            const err = new Error(body.error || `Erreur HTTP ${res.status}`);
            err.status = res.status;
            throw err;
        }
        return body;
    },
};
