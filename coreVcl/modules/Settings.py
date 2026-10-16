import os
from pathlib import Path

class settings:

    def __init__(self) -> None:
        pass

    def read_secret(self, name:str)->str:
        secrets_dir:Path = Path(os.environ.get("SECRETS_DIR", "/run/secrets"))
        path = secrets_dir / name

        if path.is_file():
            return path.read_text(encoding="utf-8").strip()

        raise RuntimeError(f"找不到機密 {name!r}：{path} 不存在")

    def require_env(self, name:str)->str:
        if value := os.environ.get(name):
            return value

        raise RuntimeError(f"環境變數 {name} 未設定")


        


    
