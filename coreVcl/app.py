from flask import Flask, render_template, request

def create_app()->Flask:
    app = Flask(__name__)

    @app.route('/')
    def index_html():
        return render_template('index.html')

    @app.route('/login')
    def login_html():
        return render_template('login.html')
    

    @app.route('/resetpasswd')
    def reset_passwd_html():
        return render_template('reset_passwd.html')
    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(host="0.0.0.0", debug=True, port=5000)

