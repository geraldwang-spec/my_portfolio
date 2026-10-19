from typing import Any
from flask import Blueprint, render_template, request, session
from auth.login_controller import LoginController as loginC
from auth.login_response import loginResponse
from modules.utils import UtilsTools

def create_auth_bp(loginCore:loginC, mName:str = "auth")->Blueprint:
    auth_bp = Blueprint(mName, __name__, url_prefix=f"/{mName}")
    
    @auth_bp.route('/login', methods=['POST', "GET"])
    def login():
        if request.method == "GET":
            return render_template(template_name_or_list=f"{mName}/login.html")
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

        if not res.success:
            return res.to_response(), 401
        session.clear()
        session.permanent = True
        session["user"] = res.data
        return res.to_response(), 200

    @auth_bp.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        if not isinstance(data, dict):
            return loginResponse(
                success=False,
                message="無效JSON格式",
                data=None).to_response(), 400

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
            return render_template(template_name_or_list="error.html", error_message=res.message), 400
        return render_template("index.html")

    @auth_bp.route('/resetpasswd', methods=['POST'])
    def reset_passwd_html():
        data = request.get_json()
        if not isinstance(data, dict):
            return loginResponse(
                success=False,
                message="無效JSON格式",
                data=None).to_response(), 400

        user_name = data.get('reset-username')
        email = data.get('reset-email')
        res:loginResponse = loginCore.send_reset_password(username=user_name, email=email)

        return res.to_response(), 200

    @auth_bp.route('/reset_passwd')
    def reset_passwd_by_user():
        user = request.args.get("user","")
        result_ok, resetId = UtilsTools.try_parse_int(request.args.get("resetId",""))

        if not result_ok:
            # 這是使用者從信件點開的網頁，錯誤時顯示錯誤頁而不是 JSON
            return render_template(
                template_name_or_list="error.html",
                error_message="連結無效，請重新申請重設密碼"), 400

        res:loginResponse = loginCore.check_reset_id(
            user=user,
            reset_id=resetId)

        if not res.success:
            return render_template(template_name_or_list="error.html", error_message=res.message), 400
        session["reset_user"] = user
        return render_template(f"{mName}/reset_passwd.html")

    @auth_bp.route('/renew_password', methods=['POST'])
    def renew_passwd():
        current_user = session.get("reset_user", "")
        if not current_user:
            return loginResponse(
                success=False,
                message="重設失敗請在重設",
                data=None).to_response(), 400


        data = request.get_json()
        if not isinstance(data, dict):
            return loginResponse(
                success=False,
                message="無效JSON格式",
                data=None
            ).to_response(), 400

        passwd = data.get('reset-pw-password')
        repeat = data.get('reset-pw-repeat')

        res:loginResponse = loginCore.change_user_password(current_user, passwd, repeat)

        if not res.success:
            return res.to_response(), 400

        session.pop("reset_user", None)

        return res.to_response(), 200


    @auth_bp.route('/me')
    def me():
        name = session.get("user")
        if not name:
            return loginResponse(
                success=False,
                message="didn't login",
                data=None).to_response(), 401

        return {"success":True, "user": {"username": name}}

    @auth_bp.route('/logout', methods=['POST'])
    def logout():
        session.clear()
        return loginResponse(
            success=True,
            message="logout",
            data=None).to_response(), 200

    @auth_bp.route('/test')
    def webTest():
        return render_template(f"{mName}/reset_passwd.html")

    return auth_bp
