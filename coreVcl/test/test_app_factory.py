"""用真正的 create_app() 組出 app，只把設定換成測試用的"""
import pytest
from app import create_app
from auth.login_setting import basic_settings
from sqlalchemy.engine import make_url
from modules.sql_module import Base
from sqlalchemy import create_engine


@pytest.fixture
def settings(tmp_path):
    # 測試用設定：DB 換成暫存資料夾裡的 SQLite 檔，其他給假值
    return basic_settings(
        secret_key="test-only",
        mail_username="test@example.com",
        mail_password="unused",
        redis_ip="localhost",          # 連線池是用到時才連線，建立 app 時不會真的連
        redis_password="unused",
        database_url=make_url(f"sqlite:///{tmp_path / 'test.db'}"),
    )


@pytest.fixture
def client(settings):
    Base.metadata.create_all(create_engine(settings.database_url))
    app = create_app(settings=settings)
    client = app.test_client()
    client.environ_base["wsgi.url_scheme"] = "https"   # Secure cookie 需要 HTTPS
    return client


def test_unknown_path_returns_json_404(client):
    # 驗證 create_app 有註冊 error handler（昨天在測試裡漏掉的那行）
    res = client.get("/no-such-page")
    assert res.status_code == 404
    assert res.get_json()["data"]["code"] == "not_found"


def test_login_unknown_user_is_401(client):
    # 這次走的是真正的 LoginController + SQLite，不是 FakeLoginCore
    res = client.post("/auth/login", json={"login-username": "nobody", "login-password": "x"})
    assert res.status_code == 401
    assert res.get_json()["success"] is False


def test_me_without_login_is_401(client):
    assert client.get("/auth/me").status_code == 401


def test_settings_are_applied(settings):
    app = create_app(settings=settings)
    assert app.secret_key == "test-only"
    assert app.config["MAIL_USERNAME"] == "test@example.com"
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
