from flask import Flask, Blueprint, jsonify, render_template, request
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

    @auth_bp.route('/login2', methods=['POST', "GET"])
    def login2():
        if request.method == "GET":
            return render_template(template_name_or_list="login2.html")
        else:
            loginCore.check_user_status
            return jsonify({"success": True, "message":"登入成功"})

    return auth_bp
