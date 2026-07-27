from flask import Flask, Blueprint, render_template, request
from auth.login_controller import LoginController as loginC, user

def create_auth_bp(loginCore:loginC)->Blueprint:
    auth_bp = Blueprint('auth', __name__, url_prefix="/auth")
    
    @auth_bp.route('/login', methods=['POST', "GET"])
    def login()->str:
        if request.method == "GET":
            # current_user = session.get("user", "")
            # return render_template("login.html", user = current_user)
            return render_template("login.html")
        else:
            

            

            # data = request.get_json()


            return render_template("login.html")

    @auth_bp.route('/resetpasswd')
    def reset_passwd_html():
        return render_template('reset_passwd.html')

    @auth_bp.route('/login2')
    def login2()->str:
        return render_template('login2.html')

    return auth_bp
