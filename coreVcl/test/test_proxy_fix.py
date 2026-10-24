"""ProxyFix：Flask 在 nginx 後面時，要拿到使用者的真實 IP 和 https"""
import pytest
from flask import request
from sqlalchemy.engine import make_url

from app import create_app
from modules.settings import AppSettings

NGINX_IP = "10.101.1.20"        # 連線來源：nginx 容器（frontend 網路）
USER_IP = "203.0.113.9"         # nginx 用 real_ip 判斷出的使用者 IP


@pytest.fixture
def client(tmp_path):
    settings = AppSettings(
        secret_key="test-only",
        mail_username="test@example.com",
        mail_password="unused",
        redis_ip="localhost",
        redis_password="unused",
        database_url=make_url(f"sqlite:///{tmp_path / 'test.db'}"),
    )
    app = create_app(settings=settings)

    @app.get("/_whoami")            # 只在測試裡加的路由，回傳 Flask 看到的連線資訊
    def whoami():
        return {"ip": request.remote_addr, "scheme": request.scheme, "host": request.host}

    client = app.test_client()
    client.environ_base["REMOTE_ADDR"] = NGINX_IP   # 模擬「連線來自 nginx 容器」
    return client


def test_uses_ip_appended_by_nginx(client):
    # nginx 的 $proxy_add_x_forwarded_for 會把使用者 IP 附加在最右邊
    res = client.get("/_whoami", headers={"X-Forwarded-For": USER_IP})
    assert res.get_json()["ip"] == USER_IP


def test_ignores_spoofed_ip_on_the_left(client):
    # 使用者自己送的 X-Forwarded-For 會留在左邊，只採用 nginx 附加的最右邊一筆
    res = client.get("/_whoami", headers={"X-Forwarded-For": f"1.2.3.4, {USER_IP}"})
    assert res.get_json()["ip"] == USER_IP


def test_scheme_from_nginx(client):
    res = client.get("/_whoami", headers={"X-Forwarded-Proto": "https"})
    assert res.get_json()["scheme"] == "https"


def test_forwarded_host_is_not_trusted(client):
    # nginx 沒有覆寫 X-Forwarded-Host，這個值可能是使用者偽造的，不能採用
    res = client.get("/_whoami", headers={"Host": "portfolio.example", "X-Forwarded-Host": "evil.example"})
    assert res.get_json()["host"] == "portfolio.example"


def test_without_proxy_headers_uses_connection_ip(client):
    res = client.get("/_whoami")
    assert res.get_json()["ip"] == NGINX_IP
