import os
import json
import urllib.request
from pathlib import Path

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
