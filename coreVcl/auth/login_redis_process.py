import redis
from modules.redis_module import RedisClient as redisC, RedisSetting
from modules.sql_module import UserModule


class LoginRedisProcess:
    __redis:redisC | None = None
    __ex_second:int = 300

    def __init__(self, host:str, passwd:str) -> None:
        self.__redis = redisC(setting=RedisSetting(
            host= host,
            port= 6379,
            password=passwd,
            max_connections=100,
            decode_responses=True,
            db = 0
        ))

    def reset_password_number(self, user:UserModule, number:int)->tuple[bool, str]:
        assert self.__redis is not None
        successed:bool = self.__set_hash_with_ttl(
            r=self.__redis.get_connection(),
            key=f"reset:auth:{user.id}",
            mapping={
                "username":user.username,
                "email":user.mail,
                "number":number
            }, 
            ex_second=self.__ex_second
        )

        if successed == False:
            return successed, f"請於{int(self.__ex_second/60)}分鐘之後在操作"

        return True, ""

    def __set_hash_with_ttl(self, r:redis.Redis, key:str, mapping:dict[str, str|int], ex_second:int) ->bool:
        if r.exists(key):
            return False

        pipe= r.pipeline()
        pipe.hset(name=key, mapping=mapping)
        _ = pipe.expire(name=key, time=ex_second)
        _ = pipe.execute()

        return True
