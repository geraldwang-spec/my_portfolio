from ast import Dict
from dataclasses import asdict, dataclass
import os
import random
from typing import Any
from flask import Flask, jsonify
from flask.cli import load_dotenv
from sqlalchemy import false, null, true
from werkzeug.security import generate_password_hash, check_password_hash
from auth.login_response import loginResponse
from modules.sql_module import DatabaseManager, UserModule
from auth.login_process import UserData as user
from modules.mail_process import MailProcess as mailp
from auth.login_process import LoginResponse 


class LoginController:
    users: list[user] = []
    app: Flask
    __mailproc: mailp |None
    __db_m:DatabaseManager|None
    __userProcess:user |None
    # __gameUsers:list[GameModule] | None 

    def __init__(self, _app:Flask) -> None:
        self.app = _app
        self.__mailproc = None
        self.__db_m = None
        self.__userProcess = None
        self.__gameUsers = []

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
        self.__mailproc = mailp(self.app)
        # self.__db_m = DatabaseManager()
        self.__db_m = DatabaseManager(db_url="mysql+pymysql://services:password@mariadb_db:3306/vision_db")
        self.__db_m.init_db()
        self.__userProcess = user(db_manager=self.__db_m)

    def check_user_status(self, username:str, passwd:str):
        assert self.__userProcess is not None, "__userProcess should be init"
        user = self.__userProcess.get_user_by_username(username)
        if not user:
            return loginResponse(success= False, message= f"{username}未註冊", data= None)

        if check_password_hash( user.passwd, passwd) == False:
            return loginResponse(success=False, message=f"帳號或密碼錯誤", data=None)

        if user.mail_check_number == 0:
            return loginResponse(success=False, message=f"E-mail未確認", data=None)

        return loginResponse(success=True, message="", data=user.username)

    def user_register(self, user_name:str, passwd:str, email:str, name:str)->LoginResponse:
        assert self.__userProcess is not None, "__userProcess should be init"
        user_c:UserModule | None = self.__userProcess.get_user_by_username(user_name)

        if user_c != None:
            return loginResponse(success=False, message=f"{user_name}存在", data=None)

        user_c = UserModule(
            username = user_name,
            passwd = generate_password_hash(passwd),
            mail = email,
            name = name,
            mail_ready = False,
            mail_check_number = random.randint(1000, 9999),
        )

        if self.__userProcess.create_user(user_c) == False:
            return loginResponse(success=False, message=f"{user_name}註冊失敗，請重新註冊", data=None)

        assert self.__mailproc is not None, "__mailproc should be init"
        self.__mailproc.start_mail_thread(user=user_c)

        return loginResponse(success=True, message="", data=None)

    def get_check_mail(self, user_name:str, number:str)->LoginResponse:
        assert self.__userProcess is not None, "__userProcess should be init"
        user_c = self.__userProcess.get_user_by_username(user_name)

        if user_c == None:
            return loginResponse(success=False,  message=f"註冊失敗，請重新註冊", data=None)
    
        if eval(number) != user_c.mail_check_number:
            return loginResponse(success=False, message=f"E-mail驗證失敗，請重新註冊", data=None)
        
        if self.__userProcess.update_mail_ready(user_name, True) == False:
            return loginResponse(success=False, message="註冊失敗，請重新註冊", data=None)


        return loginResponse(success=True, message="", data=None)

    # def game_process(self, input_user_name:str, input_user_choice:str)->LoginResponse:
    #     if input_user_choice == "":
    #         return LoginResponse(
    #             template="game.html", 
    #             error_message=f"{input_user_name} or {input_user_choice} are not current input",
    #             extra_data=GameModule(user_name=input_user_name)
    #         )
    #
    #     target_game_user:GameModule|None = None
    #
    #     if self.__gameUsers is not None:
    #         target_game_user = next((t for t in self.__gameUsers if t.user_name == input_user_name), None)
    #     else:
    #         self.__gameUsers = []
    #
    #     if target_game_user is None:
    #         target_game_user= GameModule(user_name=input_user_name, user_choice = input_user_choice)
    #         self.__gameUsers.append(target_game_user)
    #     else:
    #         target_game_user.user_choice = input_user_choice
    #
    #     choices:list[str] = ["paper", "scissors", "tone"]
    #     target_game_user.computer_choice = choices[ random.randint(0, 2)]
    #     if input_user_choice == target_game_user.computer_choice:
    #             target_game_user.result = "平手！"
    #     elif (input_user_choice == 'stone' and target_game_user.computer_choice == 'scissors') or \
    #          (input_user_choice == 'scissors' and target_game_user.computer_choice == 'paper') or \
    #          (input_user_choice == 'paper' and target_game_user.computer_choice == 'stone'):
    #         target_game_user.result = "你贏了！🎉"
    #         target_game_user.pass_count += 1
    #     else:
    #         target_game_user.result = "你輸了...😢"
    #
    #
    #
    #     return LoginResponse(
    #         template="game.html",
    #         error_message="",
    #         extra_data=target_game_user)
    #
    #
    #
    #
