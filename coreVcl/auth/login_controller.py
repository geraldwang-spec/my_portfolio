import logging

from flask import Flask
from werkzeug.security import check_password_hash, generate_password_hash

import modules.secret_number
from auth.login_process import UserData
from auth.login_redis_process import LoginRedisProcess
from modules.api_response import ApiResponse
from modules.errors import APIError
from modules.mail_process import MailProcess
from modules.services import Services
from modules.sql_module import UserModule

# 帳號不存在時拿來比對的假雜湊：讓「帳號不存在」和「密碼錯誤」花的時間一樣，
# 避免攻擊者用回應時間差猜出哪些帳號存在
logger = logging.getLogger(__name__)

_DUMMY_HASH = generate_password_hash("timeing-equalizer")

class LoginController:

    def __init__(self, app: Flask, services: Services) -> None:
        self.app: Flask = app
        self._mail: MailProcess = services.mail
        self._users: UserData = UserData(db_manager=services.db)
        self._rds: LoginRedisProcess = LoginRedisProcess(client=services.redis)

    def check_user_status(self, username:str, passwd:str)-> str:
        """驗證帳號密碼，成功回傳使用者名稱；失敗一律 raise APIError"""

        if self._rds.is_login_locked(username):
            # 鎖定期間連正確密碼也不接受，否則攻擊者仍然可以繼續猜
            raise APIError("登入失敗次數過多，請 15 分鐘後再試", status=429, code="too_many_attempts")

        user = self._users.get_user_by_username(username)
        # if not user:
        #     return ApiResponse(success= False, message= f"{username}未註冊", data= None)

        # 帳號不存在也照樣做一次雜湊比對（見 _DUMMY_HASH）
        password_ok = check_password_hash(user.passwd if user else _DUMMY_HASH, passwd)
        if user is None or not password_ok:
            self._rds.record_login_failure(username)
            raise APIError(
                message="帳號或密碼錯誤",
                status=401,
                code="invalid_credentials")

        self._rds.clear_login_failure(username)

        if not user.mail_ready:
            raise APIError(message="E-mail 尚未驗證，請先完成驗證", status=403, code="email_not_verified")

        return user.username

    def user_register(self, user_name: str, passwd: str, email: str) -> None:
        """建立帳號並寄出驗證信；失敗一律 raise APIError

        順序：先建立帳號、再寄信。寄信失敗就刪掉剛建立的帳號（補償動作），
        避免出現「信寄出去了，帳號卻沒建成」或「帳號建了，卻收不到驗證信」
        """
        # 註冊頁本來就必須告訴使用者名稱被用掉了；列舉的速度由限流控制（4-5）
        if self._users.get_user_by_username(user_name) is not None:
            raise APIError("此帳號已被使用", status=409, code="username_taken")
        if self._users.get_user_by_mail(email) is not None:
            raise APIError("此 E-mail 已被註冊", status=409, code="email_taken")

        user_c = UserModule(
            username=user_name,
            passwd=generate_password_hash(passwd),
            mail=email,
            mail_ready=False,
            mail_check_number=modules.secret_number.generate_random_number(100000, 999999),
        )

        if not self._users.create_user(user_c):
            # 上面檢查過了還是重複：兩個人同時註冊同一個名稱（race condition），由 unique 限制擋下
            raise APIError("此帳號或 E-mail 已被註冊", status=409, code="account_exists")

        if not self._mail.send_verify_mail(user=user_c):
            self._users.delete_user(user_name)   # 補償：撤銷剛建立的帳號，使用者可以直接重新註冊
            raise APIError("驗證信寄送失敗，請稍後再註冊", status=503, code="mail_send_failed")

    def get_check_mail(self, user_name:str, number:str)->ApiResponse:
        user_c = self._users.get_user_by_username(user_name)

        if user_c is None:
            return ApiResponse(success=False,  message="註冊失敗，請重新註冊", data=None)

        if not number.isdigit() or int(number) != user_c.mail_check_number:
            return ApiResponse(success=False, message="E-mail驗證失敗，請重新註冊", data=None)

        if not self._users.update_mail_ready(user_name, True):
            return ApiResponse(success=False, message="註冊失敗，請重新註冊", data=None)

        return ApiResponse(success=True, message="", data=None)

    def send_reset_password(self, username:str, email:str)->None:
        user_c:UserModule | None = self._users.get_user_by_username_and_mail(username, email)

        if not user_c:
            logger.info("password reset requested for unknown account")
            return

        if not user_c.mail_ready:
            logger.info("password reset requested for unverified account")
            return

        rand_num: int = modules.secret_number.generate_random_number(100000, 999999)
        created, _ = self._rds.reset_password_number(user=user_c, number=rand_num)
        if not created:
            # 5 分鐘內已經寄過：不重寄，也不告訴對方（否則等於確認帳號存在）
            return

        if not self._mail.send_reset_mail(user=user_c, reset_nu=rand_num):
            # 寄信失敗就清掉 redis 的重設碼，讓使用者可以立即重試
            self._rds.clean_password_number(user_c)

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






