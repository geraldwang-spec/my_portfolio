import secrets
from typing import Any

import redis
from modules.sql_module import UserModule


class LoginRedisProcess:
    MAX_ATTEMPTS:int = 5
    __ex_second:int = 300

    def __init__(self, client:redis.Redis) -> None:
        self._rds: redis.Redis = client

    def get_reset_user_data(self, userId:int) ->dict[str,Any] | None:
        r:redis.Redis = self._rds
        data:dict[str, Any] = r.hgetall(f"reset:auth:{userId}")

        if not data:
            return None

        return data

    def reset_password_number(self, user:UserModule, number:int)->tuple[bool, str]:
        successed:bool = self.__set_hash_with_ttl(
            r=self._rds,
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

    def clean_password_number(self, user:UserModule)->bool:
        r:redis.Redis = self._rds
        result:int = r.delete(f"reset:auth:{user.id}")

        return bool(result)

    def verify_reset_number(self, userId:int, reset_id:int) -> bool:
        r:redis.Redis = self._rds
        key:str = f"reset:auth:{userId}"

        data:dict[str, Any] = r.hgetall(key)
        if not data:
            return False

        if secrets.compare_digest(data["number"], str(reset_id)):
            return True

        fails:int = r.hincrby(key, "fails", 1)
        if fails >= self.MAX_ATTEMPTS or r.ttl(key) == -1:
            r.delete(key)

        return False
        


        


