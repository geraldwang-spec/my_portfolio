from dataclasses import dataclass

import redis
from flask import Flask

from modules.mail_process import MailProcess
from modules.redis_module import RedisClient, RedisSetting
from modules.settings import AppSettings
from modules.sql_module import DatabaseManager


@dataclass(frozen=True)
class Services:
    db: DatabaseManager
    redis: redis.Redis
    mail: MailProcess

def build_services(app:Flask, settings:AppSettings)->Services:
    return Services(
        db = DatabaseManager(db_url=settings.database_url),
        redis=RedisClient(
            RedisSetting(
                host=settings.redis_ip,
                password=settings.redis_password,
            )).get_connection(),
        mail=MailProcess(app=app),
    )
