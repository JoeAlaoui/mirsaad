from flask import Flask, send_from_directory
from config import Config


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(Config)

    from routes.api_dashboard import bp as api_dashboard_bp
    from routes.api_services import bp as api_services_bp
    from routes.api_quality import bp as api_quality_bp
    from routes.api_settings import bp as api_settings_bp
    from routes.api_import import bp as api_import_bp
    from routes.api_export import bp as api_export_bp

    app.register_blueprint(api_dashboard_bp)
    app.register_blueprint(api_services_bp)
    app.register_blueprint(api_quality_bp)
    app.register_blueprint(api_settings_bp)
    app.register_blueprint(api_import_bp)
    app.register_blueprint(api_export_bp)

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
