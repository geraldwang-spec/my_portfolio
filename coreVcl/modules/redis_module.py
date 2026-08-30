from dataclasses import asdict, dataclass
import redis

@dataclass
class RedisSetting:
    host:str = "localhost"
    port:int = 6379
    db:int = 0
    max_connections:int = 100
    decode_responses:bool = True
    password:str | None = ""

class RedisClient:
    __pool:redis.ConnectionPool

    def __init__(self,  setting:RedisSetting ) -> None:
        self.__pool = redis.ConnectionPool(**asdict(obj=setting))

    def get_connection(self)-> redis.Redis:
        return redis.Redis(connection_pool=self.__pool)

    


