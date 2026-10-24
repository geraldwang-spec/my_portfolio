import modules.secret_number
from auth.login_process import UserData
from auth.login_redis_process import LoginRedisProcess
from modules.api_response import ApiResponse
from flask import Flask
from modules.errors import APIError
from modules.mail_process import MailProcess
from modules.services import Services
from modules.sql_module import UserModule
from werkzeug.security import check_password_hash, generate_password_hash

# from auth.login_process import LoginResponse 


class LoginController:

    def __init__(self, app: Flask, services: Services) -> None:
        self.app: Flask = app
        self._mail: MailProcess = services.mail
        self._users: UserData = UserData(db_manager=services.db)
        self._rds: LoginRedisProcess = LoginRedisProcess(client=services.redis)

    def check_user_status(self, username:str, passwd:str):
        user = self._users.get_user_by_username(username)
        if not user:
            return ApiResponse(success= False, message= f"{username}未註冊", data= None)

        if not check_password_hash(user.passwd, passwd):
            return ApiResponse(success=False, message="帳號或密碼錯誤", data=None)

        if not user.mail_ready:
            return ApiResponse(success=False, message="E-mail未確認", data=None)

        return ApiResponse(success=True, message="", data=user.username)

    def user_register(self, user_name:str, passwd:str, email:str)->ApiResponse:
        user_c:UserModule | None = self._users.get_user_by_username(user_name)

        if user_c is not None:
            return ApiResponse(success=False, message=f"{user_name}存在", data=None)

        if self._users.get_user_by_mail(email) is not None:
            return ApiResponse(success=False, message="此E-mail已被註冊", data=None)

        user_c = UserModule(
            username = user_name,
            passwd = generate_password_hash(passwd),
            mail = email,
            # name = name,
            mail_ready = False,
            # mail_check_number = random.randint(1000, 9999),
            mail_check_number = modules.secret_number.generate_random_number(100000, 999999)
        )

        if not self._mail.send_verify_mail(user=user_c):
            return ApiResponse(success=False, message="驗證信寄送失敗，請稍後再試", data=None)

        if not self._users.create_user(user_c):
            return ApiResponse(success=False, message=f"{user_name}註冊失敗，請重新註冊", data=None)

        return ApiResponse(success=True, message="", data=None)

    def get_check_mail(self, user_name:str, number:str)->ApiResponse:
        user_c = self._users.get_user_by_username(user_name)

        if user_c is None:
            return ApiResponse(success=False,  message="註冊失敗，請重新註冊", data=None)
    
        if not number.isdigit() or int(number) != user_c.mail_check_number:
            return ApiResponse(success=False, message="E-mail驗證失敗，請重新註冊", data=None)
        
        if not self._users.update_mail_ready(user_name, True):
            return ApiResponse(success=False, message="註冊失敗，請重新註冊", data=None)

        return ApiResponse(success=True, message="", data=None)

    def send_reset_password(self, username:str, email:str)->ApiResponse:
        user_c:UserModule | None = self._users.get_user_by_username_and_mail(username, email)

        if not user_c:
            return ApiResponse(
                success=False,
                message=f"{username}無此帳號",
                data=None)

        if not user_c.mail_ready:
            return ApiResponse(
                success=False,
                message=f"{user_c.username} E-mail未完成驗證",
                data=None)

        rand_num: int = modules.secret_number.generate_random_number(100000, 999999)
        result, mesg = self._rds.reset_password_number(user=user_c, number=rand_num)
        if not result:
            return ApiResponse(
                success=False,
                message=mesg,
                data=None )

        if not self._mail.send_reset_mail(user=user_c, reset_nu=rand_num):
            # 寄信失敗就清掉 redis 的重設碼，讓使用者可以立即重試
            _ = self._rds.clean_password_number(user_c)
            return ApiResponse(
                success=False,
                message="重設密碼信寄送失敗，請稍後再試",
                data=None)

        return ApiResponse(
            success=True,
            message="請於E-mail收確認信",
            data=None)

    def check_reset_id(self, user:str, reset_id:int)->ApiResponse:
        user_c:UserModule | None = self._users.get_user_by_username(username=user)

        if not user_c:
            return ApiResponse(
                success=False,
                message="輸入使用者錯誤",
                data=None
            )

        rds_r = self._rds.get_reset_user_data(user_id=user_c.id)

        if not rds_r:
            return ApiResponse(
                success=False,
                message="超過重設時間",
                data=None)

        if not self._rds.verify_reset_number(user_id=user_c.id, reset_id=reset_id):
            return ApiResponse(
                success=False,
                message="重設失敗，請在重新設定",
                data=None)

        return ApiResponse(
            success=True,
            message="",
            data=None)
        
    def change_user_password(self, user:str, passwd:str, repeat:str)->ApiResponse:
        if passwd != repeat:
            raise APIError(message="密碼不一致", status=400, code="password_mismatch")
        
        if not self._users.update_password_by_user(user, generate_password_hash(passwd)):
            raise APIError(
                message="更新密碼失敗，請重新設定",
                status=500,
                code="db_error")

        user_c:UserModule | None = self._users.get_user_by_username(username=user)
        if user_c is not None and not self._rds.clean_password_number(user_c):
            self.app.logger.warning("reset code cleanup failed after password change")

        return ApiResponse(
            success=True,
            message="",
            data =None)






