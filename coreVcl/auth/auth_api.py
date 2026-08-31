from this import d
from typing import Any
from webbrowser import get
from flask import Flask, Blueprint, jsonify, render_template, request
from sqlalchemy.util import methods_equivalent
from auth.login_controller import LoginController as loginC, user
from auth.login_response import loginResponse
from modules.utils import UtilsTools

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


    @auth_bp.route('/login2', methods=['POST', "GET"])
    def login2():
        if request.method == "GET":
            return render_template(template_name_or_list="login2.html")
        data = request.get_json()
        if not isinstance(data, dict):
            return loginResponse(
                success=False,
                message="無效JSON格式",
                data=None
            ).to_response(), 400

        raw_user: Any = data.get('login-username')
        raw_passwd: Any = data.get('login-password')
        username:str = raw_user.strip() if isinstance(raw_user, str) else ""
        passwd: str = raw_passwd.strip() if isinstance(raw_passwd, str) else ""

        if not username or not passwd:
            return loginResponse(
                success=False,
                message="帳號或密碼不可為空",
                data=None
            ).to_response(), 400

        res:loginResponse = loginCore.check_user_status(
            username=username,
            passwd=passwd)
        return res.to_response()

    @auth_bp.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        if not isinstance(data, dict):
            return loginResponse(
                success=False,
                message="無效JSON格式",
                data=None
            )

        user_name = data.get('register-username')
        passwd = data.get('register-password')
        passwd_repeat = data.get('register-repeat')
        email = data.get('register-email')

        if not (isinstance(user_name, str) and
            isinstance(passwd, str) and
            isinstance(passwd_repeat, str) and
                isinstance(email, str)):
            return loginResponse(
                success=False,
                message="請鎮寫完全部欄位",
                data=None).to_response(), 400

        if passwd != passwd_repeat:
            return loginResponse(
                success=False,
                message="密碼不相同",
                data=None).to_response(), 400

        return loginCore.user_register(
            user_name=user_name,
            passwd= passwd,
            email=email
        ).to_response(), 200

    @auth_bp.route('/mailverify')
    def mail_verify():
        res:loginResponse = loginCore.get_check_mail(
            user_name=request.args.get("user", ""), 
            number=request.args.get("mail_number", ""))

        if not res.success:
            return render_template(template_name_or_list="error.html", error_message=res.message)
        return render_template("index.html")

    @auth_bp.route('/resetpasswd', methods=['POST'])
    def reset_passwd_html():
        data = request.get_json()
        if not isinstance(data, dict):
            return loginResponse(
                success=False,
                message="無效JSON格式",
                data=None
            )

        user_name = data.get('reset-username')
        email = data.get('reset-email')
        res:loginResponse = loginCore.send_reset_password(username=user_name, email=email)

        return res.to_response()

    @auth_bp.route('/reset_passwd')
    def reset_passwd_by_user():
        user = request.args.get("user","")
        result_ok, resetId = UtilsTools.try_parse_int(request.args.get("resetId",""))

        if not result_ok:
            return loginResponse(
                success=False,
                message="重設錯誤請重設",
                data=None)
         
        res:loginResponse = loginCore.check_reset_id(
            user=user,
            reset_id=resetId)

        if not res.success:
            return render_template(template_name_or_list="error.html", error_message=res.message)
        return render_template("index.html")

    return auth_bp
