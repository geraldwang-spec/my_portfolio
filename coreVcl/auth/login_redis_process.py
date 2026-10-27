import secrets
from typing import Any

import redis

from modules.sql_module import UserModule


class LoginRedisProcess:
    MAX_ATTEMPTS:int = 5
    _ex_second:int = 300

    LOGIN_MAX_FAILS: int = 5
    LOGIN_LOCK_SECONDS: int = 15 * 60 # 15分鐘

    def __init__(self, client:redis.Redis) -> None:
        self._rds: redis.Redis = client

    def get_reset_user_data(self, user_id:int) ->dict[str,Any] | None:
        r:redis.Redis = self._rds
        data:dict[str, Any] = r.hgetall(f"reset:auth:{user_id}")

        if not data:
            return None

        return data

    def reset_password_number(self, user:UserModule, number:int)->tuple[bool, str]:
        successed:bool = self._set_hash_with_ttl(
            r=self._rds,
            key=f"reset:auth:{user.id}",
            mapping={
                "username":user.username,
                "email":user.mail,
                "number":number
            },
            ex_second=self._ex_second
        )

        if not successed:
            return successed, f"請於{int(self._ex_second/60)}分鐘之後在操作"

        return True, ""

    def _set_hash_with_ttl(self, r:redis.Redis, key:str, mapping:dict[str, str|int], ex_second:int) ->bool:
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

    def verify_reset_number(self, user_id:int, reset_id:int) -> bool:
        r:redis.Redis = self._rds
        key:str = f"reset:auth:{user_id}"

        data:dict[str, Any] = r.hgetall(key)
        if not data:
            return False

        if secrets.compare_digest(data["number"], str(reset_id)):
            return True

        fails:int = r.hincrby(key, "fails", 1)
        if fails >= self.MAX_ATTEMPTS or r.ttl(key) == -1:
            r.delete(key)

        return False

    # ---- 登入失敗計數：以「送出的帳號名稱」為 key，不管帳號存不存在 ----
    # 不存在的帳號也一樣計數、一樣鎖定，否則「會不會被鎖」本身就會洩漏帳號是否存在

    @staticmethod
    def _login_key(username:str)->str:
        return f"login:fail:{username.lower()}"

    def is_login_locked(self, username:str)->bool:
        count = self._rds.get(self._login_key(username))
        return int(count or 0) >= self.LOGIN_MAX_FAILS

    def record_login_failure(self, username:str) -> int:
        key = self._login_key(username)
        pipe = self._rds.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.LOGIN_LOCK_SECONDS, nx=True)
        count, _ = pipe.execute()
        return int(count)

    def clear_login_failure(self, username:str)->None:
        self._rds.delete(self._login_key(username))




