import os
import sys

# Sous Windows, WeasyPrint a besoin de localiser les DLL Pango/GObject (fournies par MSYS2,
# voir README section "Prérequis spécifiques pour Windows"). Sans cela : OSError
# "cannot load library 'gobject-2.0-0'". Ce bloc doit rester tout en haut du fichier,
# avant tout import qui charge WeasyPrint (directement ou indirectement).
if sys.platform == "win32":
    msys_bin = r"C:\msys64\ucrt64\bin"
    if os.path.exists(msys_bin):
        os.environ["PATH"] = msys_bin + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(msys_bin)

from flask import Flask, send_from_directory
from config import Config


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(Config)

    if not app.config["DEBUG"] and app.config["SECRET_KEY"] == "dev-secret-change-in-production":
        app.logger.warning(
            "MIRSAAD_SECRET_KEY n'est pas configurée : la clé secrète par défaut est utilisée en dehors du mode debug. "
            "Définissez la variable d'environnement MIRSAAD_SECRET_KEY avant un déploiement réel."
        )

    from routes.api_dashboard import bp as api_dashboard_bp
    from routes.api_services import bp as api_services_bp
    from routes.api_quality import bp as api_quality_bp
    from routes.api_settings import bp as api_settings_bp
    from routes.api_import import bp as api_import_bp
    from routes.api_export import bp as api_export_bp
    from routes.api_reports import bp as api_reports_bp

    app.register_blueprint(api_dashboard_bp)
    app.register_blueprint(api_services_bp)
    app.register_blueprint(api_quality_bp)
    app.register_blueprint(api_settings_bp)
    app.register_blueprint(api_import_bp)
    app.register_blueprint(api_export_bp)
    app.register_blueprint(api_reports_bp)

    @app.errorhandler(413)
    def too_large(e):
        from flask import jsonify
        return jsonify({"error": "Fichier trop volumineux."}), 413

    @app.errorhandler(500)
    def server_error(e):
        from flask import jsonify, request
        app.logger.exception("Erreur serveur non gérée")
        if request.path.startswith("/api/"):
            return jsonify({"error": "Une erreur interne est survenue."}), 500
        return "Une erreur interne est survenue.", 500

    @app.route("/")
    @app.route("/<path:path>")
    def spa_shell(path=None):
        """Sert le shell SPA pour toutes les routes front ; 404 JSON pour /api/* inconnu."""
        from flask import jsonify
        if path and path.startswith("api/"):
            return jsonify({"error": "Route API introuvable"}), 404
        # Toute autre route est prise en charge par le routeur JS côté client
        return send_from_directory(app.static_folder, "index.html")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
