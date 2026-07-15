from dataclasses import dataclass
import os
import random
from tempfile import template
from typing import Any
from flask import Flask
from flask.cli import load_dotenv
from sqlalchemy import Null
from werkzeug.security import generate_password_hash, check_password_hash
from sql_module import DatabaseManager, UserModule
from login_process import UserData as user
from mail_process import MailProcess as mailp


@dataclass
class LoginResponse:
    template:str = ""
    error_message:str = ""
    extra_data: Any|None = None


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
        self.__db_m = DatabaseManager(db_url="mysql+pymysql://root:1234@localhost:3306/login")
        self.__db_m.init_db()
        self.__userProcess = user(db_manager=self.__db_m)

    def check_user_status(self, username:str, passwd:str):
        assert self.__userProcess is not None, "__userProcess should be init"
        user = self.__userProcess.get_user_by_username(username)
        if not user:
            return LoginResponse(
                template="index.html",
                error_message="User wasn't register"
            )

        if check_password_hash( user.passwd, passwd) == False:
            return LoginResponse(
                template="index.html",
                error_message="user name or password fail",
                extra_data=user.username
            )

        if user.mail_check_number == 0:
            return LoginResponse(
                template="index.html",
                error_message="E-mail doesn't verify"
            )

        return LoginResponse(
            template="game",
            extra_data=user.username
        )

    def user_register(self, user_name:str, passwd:str, email:str, name:str)->LoginResponse:
        assert self.__userProcess is not None, "__userProcess should be init"
        user_c = self.__userProcess.get_user_by_username(user_name)

        if user_c != None:
            return LoginResponse(
                template="register.html",
                error_message=f"{user_name} is exist"
            )

        user_c = UserModule(
            username = user_name,
            passwd = generate_password_hash(passwd),
            mail = email,
            name = name,
            mail_ready = False,
            mail_check_number = random.randint(1000, 9999),
        )

        if self.__userProcess.create_user(user_c) == False:
            return LoginResponse(
                template="register.html",
                error_message=f"create {user_name} fail, try again"
            )

        assert self.__mailproc is not None, "__mailproc should be init"
        self.__mailproc.start_mail_thread(user=user_c)
        return LoginResponse(template="index.html")

    def get_check_mail(self, user_name:str, number:str)->LoginResponse:
        assert self.__userProcess is not None, "__userProcess should be init"
        user_c = self.__userProcess.get_user_by_username(user_name)

        if user_c == None:
            return LoginResponse(
                template="mailcheck.html",
                error_message="Register error, Please register again"
            )
    
        if eval(number) != user_c.mail_check_number:
            return LoginResponse(
                template="index.html",
                error_message="Check Mail fail, please register again"
            )
        
        if self.__userProcess.update_mail_ready(user_name, True) == False:
            return LoginResponse(
                template="index.html",
                error_message="register error, please register again"
            )

        return LoginResponse(
            template="login")

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
