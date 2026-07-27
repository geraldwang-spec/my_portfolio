from flask import Blueprint, Flask, render_template, request
from auth.auth_api import create_auth_bp
from auth.login_controller import LoginController as loginC


def create_app()->Flask:
    app:Flask = Flask(__name__)

    loginCore:loginC = loginC(_app=app)
    loginCore.init_core()

    auth_blueprint:Blueprint= create_auth_bp(loginCore)
    app.register_blueprint(blueprint=auth_blueprint)

    @app.route('/')
    def index_html():
        return render_template('index.html')

    return app

if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(host="0.0.0.0", debug=True, port=5000)
