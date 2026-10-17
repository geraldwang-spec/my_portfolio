from dataclasses import dataclass
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
        database_url = URL.create(
            drivername = "mysql+pymysql",
            username = require_env("MYSQL_USER"),
            password = read_secret("mysql_password"),
            host = require_env("MARIADB_IP"),
            port = 3306,
            database = require_env("MYSQL_DATABASE"), 
        ),
    )



