/**
 * Point d'entrée de l'application SPA.
 * Charge les paramètres (nom de l'organisation, etc.) avant d'afficher quoi que ce soit,
 * pour éviter tout flash de valeurs par défaut ou de contenu codé en dur.
 */
document.addEventListener("DOMContentLoaded", async () => {
    try {
        const settings = await Api.getSettings();
        Render.applySettings(settings);
    } catch (e) {
        // Si les paramètres sont indisponibles, on continue avec les valeurs par défaut du HTML.
        console.warn("Impossible de charger les paramètres :", e.message);
    }
    Router.init();
});
