from ast import Dict
from dataclasses import asdict, dataclass
import os
import random
from readline import redisplay
from typing import Any
from flask import Flask, jsonify
from flask.cli import load_dotenv
from redis import SubkeyspaceChannel
from sqlalchemy import false, null, true
from werkzeug.security import generate_password_hash, check_password_hash
from auth.login_response import loginResponse
from modules.sql_module import DatabaseManager, UserModule
from auth.login_process import UserData as user
from modules.mail_process import MailProcess as mailp
from auth.login_redis_process import LoginRedisProcess as redisP
# from auth.login_process import LoginResponse 


class LoginController:
    users: list[user] = []
    app: Flask
    __mailproc: mailp |None
    __db_m:DatabaseManager|None
    __userProcess:user |None
    # __gameUsers:list[GameModule] | None 
    __vcl_tunnel_url:str = ""
    __rds:redisP |None

    def __init__(self, _app:Flask) -> None:
        self.app = _app
        self.__mailproc = None
        self.__db_m = None
        self.__userProcess = None
        self.__gameUsers = []
        # self.__vcl_tunnel_url = "https://img-models-basin-changing.trycloudflare.com/"
        self.__rds = None

    def init_core(self)->None:
        _ = load_dotenv()
        self.app.secret_key = os.environ.get("SECRET_KEY")
        self.app.config.update(
            MAIL_SERVER='smtp.gmail.com',
            MAIL_PORT=465,
            MAIL_USE_TLS=False,
            MAIL_USE_SSL=True,
            MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
            MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD")
        )
        self.__vcl_tunnel_url = os.environ.get("VCL_TUNNEL")
        self.__mailproc = mailp(self.app, _tunnel_url=self.__vcl_tunnel_url)
        # self.__db_m = DatabaseManager()
        self.__db_m = DatabaseManager(db_url="mysql+pymysql://services:password@mariadb_db:3306/vision_db")
        self.__db_m.init_db()
        self.__userProcess = user(db_manager=self.__db_m)
        self.__rds = redisP(host=os.environ.get("REDIS_HOST"), passwd= os.environ.get("REDIS_PASSWORD"))

    def check_user_status(self, username:str, passwd:str):
        assert self.__userProcess is not None, "__userProcess should be init"
        user = self.__userProcess.get_user_by_username(username)
        if not user:
            return loginResponse(success= False, message= f"{username}未註冊", data= None)

        if check_password_hash( user.passwd, passwd) == False:
            return loginResponse(success=False, message=f"帳號或密碼錯誤", data=None)

        print(f"mail_check_number {user.mail_check_number}")

        if user.mail_check_number != 0:
            return loginResponse(success=False, message=f"E-mail未確認", data=None)

        return loginResponse(success=True, message="", data=user.username)

    def user_register(self, user_name:str, passwd:str, email:str)->loginResponse:
        assert self.__userProcess is not None, "__userProcess should be init"
        user_c:UserModule | None = self.__userProcess.get_user_by_username(user_name)

        if user_c != None:
            return loginResponse(success=False, message=f"{user_name}存在", data=None)

        user_c = UserModule(
            username = user_name,
            passwd = generate_password_hash(passwd),
            mail = email,
            # name = name,
            mail_ready = False,
            mail_check_number = random.randint(1000, 9999),
        )

        if self.__userProcess.create_user(user_c) == False:
            return loginResponse(success=False, message=f"{user_name}註冊失敗，請重新註冊", data=None)

        assert self.__mailproc is not None, "__mailproc should be init"
        self.__mailproc.start_mail_thread(user=user_c)

        return loginResponse(success=True, message="", data=None)

    def get_check_mail(self, user_name:str, number:str)->loginResponse:
        assert self.__userProcess is not None, "__userProcess should be init"
        user_c = self.__userProcess.get_user_by_username(user_name)

        if user_c == None:
            return loginResponse(success=False,  message=f"註冊失敗，請重新註冊", data=None)
    
        if eval(number) != user_c.mail_check_number:
            return loginResponse(success=False, message=f"E-mail驗證失敗，請重新註冊", data=None)
        
        if self.__userProcess.update_mail_ready(user_name, True) == False:
            return loginResponse(success=False, message="註冊失敗，請重新註冊", data=None)

        return loginResponse(success=True, message="", data=None)

    def send_reset_password(self, username:str, email:str)->loginResponse:
        assert self.__userProcess is not None, "__userProcess should be init"
        assert self.__rds is not None, "__rds should be init"
        assert self.__mailproc is not None, "__mailproc should be init"
        user_c:UserModule | None = self.__userProcess.get_user_by_username_and_mail(username, email)

        if not user_c:
            return loginResponse(
                success=False,
                message=f"{username}無此帳號",
                data=None)

        if not user_c.mail_ready:
            return loginResponse(
                success=False,
                message=f"{user_c.username} E-mail未完成驗證",
                data=None)

        randNum: int = random.randint(111111, 999999)
        result, mesg = self.__rds.reset_password_number(user=user_c, number=randNum)
        if not result:
            return loginResponse(
                success=False,
                message=mesg,
                data=None )

        self.__mailproc.send_reset_mail_thread(user=user_c, reset_nu=randNum)
        
        return loginResponse(
            success=True,
            message="請於E-mail收確認信",
            data=None)

    def check_reset_id(self, user:str, reset_id:int)->loginResponse:
        assert self.__rds is not None, "__rds should be init"
        assert self.__userProcess is not None, "__userProcess should be init"
        user_c:UserModule | None = self.__userProcess.get_user_by_username(username=user)

        if not user_c:
            return loginResponse(
                success=False,
                message="輸入使用者錯誤",
                data=None
            )

        rds_r = self.__rds.get_reset_user_data(userId=user_c.id)

        if not rds_r:
            return loginResponse(
                success=False,
                message="超過重設時間",
                data=None)

        if int(rds_r["number"]) != reset_id:
            return loginResponse(
                success=False,
                message="重設失敗，請在重新設定",
                data=None)

        return loginResponse(
            success=True,
            message="",
            data=None)



