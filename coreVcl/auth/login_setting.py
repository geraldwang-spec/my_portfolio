from asyncio.windows_events import NULL
from dataclasses import dataclass
import secrets
from sqlalchemy import URL, Null
from modules.Settings import settings


@dataclass(frozen=True)
class auth_settings:
    secret_key:str
    mail_username:str
    mail_password:str
    redis_host:str
    redis_password:str
    database_url: URL

     def __repr__(self) -> str:
        # 避免 print(settings) 或例外訊息把密碼印進 log
        return f"Settings(mail_username={self.mail_username!r}, redis_host={self.redis_host!r}, db={self.database_url!r})"

#maill_password  mysql_password  mysql_root_password  redis_password  secret_key
#    MYSQL_USER=services
#   MYSQL_DATABASE=vision_db
#
# ---  Mail ---
# MAIL_USERNAME=g123erald456@gmail.com
#
#
#   ~/u/github/my_portfolio on   vision-color-lab +1 ?5 ❯  
# 

class auth_settings:
    __sets:settings = NULL
    def __init__(self) -> None:
        pass

    def get_settings(self)->auth_settings:
        sets = settings()
        return auth_settings(
            redis_host = sets.require_env("REDIS_HOST", "vclredis"),
            redis_password= sets.read_secret("redis_password"),
            secret_key = sets.read_secret("secret_key"),
            mail_username=sets.require_env("MAIL_USERNAME"),
            mail_password = sets.read_secret("mail_password"),
            database_url = URL.create(
                drivername="mysql+pymysql",
                username=sets.require_env("MYSQL_USER"),
                password=sets.read_secret("mysql_password"),
                host=sets.require_env("MYSQL_DATABASE"),
                port=3306,
                database=sets.require_env("MYSQL_DATABASE"), 
            ),
        )



