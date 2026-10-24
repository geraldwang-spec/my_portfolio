from dataclasses import dataclass
from datetime import timedelta

from modules.Settings import read_secret, require_env
from sqlalchemy.engine import URL


@dataclass(frozen=True)
class basic_settings:
    secret_key:str
    mail_username:str
    mail_password:str
    redis_ip:str
    redis_password:str
    database_url: URL

    def __repr__(self) -> str:
       # 避免 print(settings) 或例外訊息把密碼印進 log
       return f"Settings(mail_username={self.mail_username!r}, redis_ip={self.redis_ip!r}, db={self.database_url!r})"


def get_settings()->basic_settings:
    return basic_settings(
        redis_ip = require_env("REDIS_IP"),
        redis_password= read_secret("redis_password"),
        secret_key = read_secret("secret_key"),
        mail_username= require_env("MAIL_USERNAME"),
        mail_password = read_secret("mail_password"),
        database_url = get_database_url(),
    )

def get_database_url()->URL:
    return URL.create(
            drivername = "mysql+pymysql",
            username = require_env("MYSQL_USER"),
            password = read_secret("mysql_password"),
            host = require_env("MARIADB_IP"),
            port = 3306,
            database = require_env("MYSQL_DATABASE"), 
    )


def session_cookies_config()->dict[str,object]:
    return {
        "SESSION_COOKIE_SECURE": True,           # dev 用 IP 連線時才不會吃掉 cookie
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "PERMANENT_SESSION_LIFETIME": timedelta(hours=8),
        # __Host- 前綴：瀏覽器強制要求 Secure、Path=/、不可設 Domain
        # 防止子網域覆寫你的 cookie，只能在 HTTPS 下使用，因此 dev 環境不加
        "SESSION_COOKIE_NAME": "__Host-session",
    }

def mail_config(settings: basic_settings)->dict[str, object]:
    """Flask-Mail 需要的設定，原本寫在 LoginController.init_core 裡"""
    return {
        "MAIL_SERVER": "smtp.gmail.com",
        "MAIL_PORT": 465,
        "MAIL_USE_TLS": False,
        "MAIL_USE_SSL": True,
        "MAIL_USERNAME": settings.mail_username,
        "MAIL_PASSWORD": settings.mail_password,
    }
    
