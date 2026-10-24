import os
from auth.auth_api import create_auth_bp
from auth.login_controller import LoginController
from modules.settings import AppSettings, get_settings, mail_config, session_cookies_config
from flask import Blueprint, Flask, render_template
from modules.errors import register_error_handlers
from modules.services import Services, build_services

def create_app(settings:AppSettings | None = None, services:Services | None = None)->Flask:
    settings = settings or get_settings()
    app:Flask = Flask(__name__)
    app.secret_key = settings.secret_key

    app.config.update(session_cookies_config())
    app.config.update(mail_config(settings))

    register_error_handlers(app=app)

    services = services or build_services(
        app=app,
        settings=settings
    )

    login_core = LoginController(app=app, services=services)

    auth_blueprint:Blueprint= create_auth_bp(login_core)
    app.register_blueprint(blueprint=auth_blueprint)

    @app.route('/')
    def index_html():
        return render_template('index.html')

    return app

if __name__ == "__main__":
    flask_app = create_app()
    debug:bool = os.environ.get("FLASK_DEBUG", "0") == "1"
    flask_app.run(host="0.0.0.0", debug=debug, port=5000)
