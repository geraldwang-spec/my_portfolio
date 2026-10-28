from typing import Any

from flask import Blueprint, render_template, request, session

from auth.login_controller import LoginController
from modules.api_response import ApiResponse
from modules.errors import APIError
from modules.utils import UtilsTools

MIN_PASSWORD_LENGTH = 8


def _require_new_password(passwd: str) -> None:
    """新密碼的共同規則：註冊和重設密碼都用這一個"""
    if len(passwd) < MIN_PASSWORD_LENGTH:
        raise APIError(f"密碼至少 {MIN_PASSWORD_LENGTH} 個字元", status=400, code="password_too_short")


def create_auth_bp(login_core: LoginController, name: str = "auth") -> Blueprint:
    auth_bp = Blueprint(name, __name__, url_prefix=f"/{name}")

    @auth_bp.route('/login', methods=['POST', "GET"])
    def login():
        if request.method == "GET":
            return render_template(template_name_or_list=f"{name}/login.html")
        data = request.get_json()
        if not isinstance(data, dict):
            return ApiResponse(
                success=False,
                message="無效JSON格式",
                data=None
            ).to_response(), 400

        raw_user: Any = data.get('login-username')
        raw_passwd: Any = data.get('login-password')
        username:str = raw_user.strip() if isinstance(raw_user, str) else ""
        passwd: str = raw_passwd.strip() if isinstance(raw_passwd, str) else ""

        if not username or not passwd:
            return ApiResponse(
                success=False,
                message="帳號或密碼不可為空",
                data=None
            ).to_response(), 400

        user_name = login_core.check_user_status(username=username, passwd=passwd)

        session.clear()
        session["user"] = user_name
        session.permanent = True
        return ApiResponse(success=True, message="", data=user_name).to_response(), 200

    @auth_bp.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        if not isinstance(data, dict):
            return ApiResponse(
                success=False,
                message="無效JSON格式",
                data=None).to_response(), 400

        user_name = data.get('register-username')
        passwd = data.get('register-password')
        passwd_repeat = data.get('register-repeat')
        email = data.get('register-email')

        # 逐一寫 isinstance，型別檢查器才知道之後這四個變數都是 str
        if not (isinstance(user_name, str) and isinstance(passwd, str)
                and isinstance(passwd_repeat, str) and isinstance(email, str)):
            raise APIError("請填寫完全部欄位", status=400, code="fields_required")
        user_name, email = user_name.strip(), email.strip()
        if not user_name or not email:
            raise APIError("請填寫完全部欄位", status=400, code="fields_required")

        if passwd != passwd_repeat:
            raise APIError("密碼不相同", status=400, code="password_mismatch")
        _require_new_password(passwd)

        login_core.user_register(user_name=user_name, passwd=passwd, email=email)
        return ApiResponse(
            success=True, message="註冊成功，請到信箱完成 E-mail 驗證", data=None
        ).to_response(), 201

    @auth_bp.route('/mailverify')
    def mail_verify():
        res:ApiResponse = login_core.get_check_mail(
            user_name=request.args.get("user", ""),
            number=request.args.get("mail_number", ""))

        if not res.success:
            return render_template(template_name_or_list="error.html", error_message=res.message), 400
        return render_template("index.html")

    @auth_bp.route('/resetpasswd', methods=['POST'])
    def reset_passwd_html():
        data = request.get_json()
        if not isinstance(data, dict):
            return ApiResponse(
                success=False,
                message="無效JSON格式",
                data=None).to_response(), 400

        user_name = data.get('reset-username')
        email = data.get('reset-email')

        if not (isinstance(user_name, str) and isinstance(email, str)):
            raise APIError("請輸入帳號和 E-mail", status=400, code="fields_required")
        user_name, email = user_name.strip(), email.strip()
        if not user_name or not email:
            raise APIError("請輸入帳號和 E-mail", status=400, code="fields_required")

        login_core.send_reset_password(username=user_name, email=email)
        # 不論帳號存不存在都回同一句話，不透露帳號是否存在
        return ApiResponse(
            success=True,
            message="如果帳號與 E-mail 相符，重設密碼信已寄出，請到信箱查看",
            data=None,
        ).to_response(), 200

    @auth_bp.route('/reset_passwd')
    def reset_passwd_by_user():
        user = request.args.get("user","")
        result_ok, reset_id = UtilsTools.try_parse_int(request.args.get("resetId",""))

        if not result_ok:
            # 這是使用者從信件點開的網頁，錯誤時顯示錯誤頁而不是 JSON
            return render_template(
                template_name_or_list="error.html",
                error_message="連結無效，請重新申請重設密碼"), 400

        res:ApiResponse = login_core.check_reset_id(
            user=user,
            reset_id=reset_id)

        if not res.success:
            return render_template(template_name_or_list="error.html", error_message=res.message), 400
        session["reset_user"] = user
        return render_template(f"{name}/reset_passwd.html")

    @auth_bp.route('/renew_password', methods=['POST'])
    def renew_passwd():
        current_user = session.get("reset_user", "")
        if not current_user:
            raise APIError(message="重設失敗請在重設", status=400, code="reset_session_missing")

        data = request.get_json()
        if not isinstance(data, dict):
            raise APIError(message="無效JSON格式", status=400, code="invalid_json")

        passwd = data.get('reset-pw-password')
        repeat = data.get('reset-pw-repeat')

        if not isinstance(passwd, str) or not isinstance(repeat, str) or not passwd:
            raise APIError(message="請輸入新密碼", status=400, code="password_required")
        _require_new_password(passwd)

        res:ApiResponse = login_core.change_user_password(current_user, passwd, repeat)

        session.pop("reset_user", None)
        return res.to_response(), 200


    @auth_bp.route('/me')
    def me():
        name = session.get("user")
        if not name:
            return ApiResponse(
                success=False,
                message="didn't login",
                data=None).to_response(), 401

        return {"success":True, "user": {"username": name}}

    @auth_bp.route('/logout', methods=['POST'])
    def logout():
        session.clear()
        return ApiResponse(
            success=True,
            message="logout",
            data=None).to_response(), 200

    return auth_bp
