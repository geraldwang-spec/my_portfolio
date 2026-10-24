"""整個 app 的設定：環境變數、/run/secrets，以及由它們組出來的 Flask 設定"""
import json
import os
import urllib.request
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from sqlalchemy.engine import URL


def read_secret(name:str)->str:
    secrets_dir:Path = Path(os.environ.get("SECRETS_DIR", "/run/secrets"))
    path = secrets_dir / name

    if path.is_file():
        return path.read_text(encoding="utf-8").strip()

    raise RuntimeError(f"找不到機密 {name!r}：{path} 不存在")

def require_env(name:str)->str:
    if value := os.environ.get(name):
        return value

    raise RuntimeError(f"環境變數 {name} 未設定")

def public_base_url() -> str:
    """對外網址，結尾不含斜線，例如 https://xxxx.trycloudflare.com

    - 有 PUBLIC_BASE_URL（正式環境的固定網域）就直接用
    - 否則向 cloudflared 查詢目前的 quick tunnel 網址
    刻意不快取：tunnel 容器重啟後網址會變，每次寄信時重新查詢。
    """
    if fixed := os.environ.get("PUBLIC_BASE_URL"):
        return fixed.rstrip("/")

    metrics = os.environ.get("TUNNEL_METRICS_URL", "http://vcl_tunnel:2000")
    try:
        with urllib.request.urlopen(f"{metrics}/quicktunnel", timeout=3) as resp:
            hostname = json.load(resp)["hostname"]
    except (OSError, KeyError, ValueError) as exc:
        # OSError：連不上；KeyError：回傳格式不對；ValueError：不是 JSON
        raise RuntimeError(f"無法從 {metrics}/quicktunnel 取得 tunnel 網址") from exc

    if not hostname:
        # tunnel 剛啟動、還沒連上 Cloudflare 時會回傳空字串
        raise RuntimeError("tunnel 尚未取得網址，請稍後再試")
    return f"https://{hostname}"


@dataclass(frozen=True)
class AppSettings:
    secret_key:str
    mail_username:str
    mail_password:str
    redis_ip:str
    redis_password:str
    database_url: URL

    def __repr__(self) -> str:
       # 避免 print(settings) 或例外訊息把密碼印進 log
       return f"Settings(mail_username={self.mail_username!r}, redis_ip={self.redis_ip!r}, db={self.database_url!r})"


def get_settings()-> AppSettings:
    return AppSettings(
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

def mail_config(settings: AppSettings)->dict[str, object]:
    """Flask-Mail 需要的設定，原本寫在 LoginController.init_core 裡"""
    return {
        "MAIL_SERVER": "smtp.gmail.com",
        "MAIL_PORT": 465,
        "MAIL_USE_TLS": False,
        "MAIL_USE_SSL": True,
        "MAIL_USERNAME": settings.mail_username,
        "MAIL_PASSWORD": settings.mail_password,
    }

