"""帳號路由的錯誤輸入：任何錯誤輸入都不能變成 500"""
from pathlib import Path

import pytest
from flask import Flask

from auth.auth_api import create_auth_bp
from auth.login_response import loginResponse
from auth.login_setting import session_cookies_config

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


class FakeLoginCore:
    """取代 LoginController，不連 DB、Redis、SMTP"""

    def check_user_status(self, username, passwd):
        if username == "alice" and passwd == "correct-pw":
            return loginResponse(success=True, message="", data="alice")
        return loginResponse(success=False, message="帳號或密碼錯誤", data=None)

    def check_reset_id(self, user, reset_id):
        return loginResponse(success=False, message="連結無效", data=None)


@pytest.fixture
def client():
    app = Flask(__name__, template_folder=str(TEMPLATES))
    app.secret_key = "test-only"
    app.config.update(session_cookies_config())    # 用正式環境的 cookie 設定
    app.register_blueprint(create_auth_bp(FakeLoginCore()))
    client = app.test_client()
    # Secure cookie 只在 HTTPS 送出，所以測試也模擬 HTTPS 連線
    client.environ_base["wsgi.url_scheme"] = "https"
    return client


# ---- JSON 格式錯誤：內容是合法 JSON 但不是物件 ----
@pytest.mark.parametrize("path", ["/auth/register", "/auth/resetpasswd"])
def test_non_object_json_returns_400(client, path):
    res = client.post(path, json=["not", "an", "object"])
    assert res.status_code == 400
    assert res.get_json()["success"] is False


def test_reset_link_with_non_numeric_id_shows_error_page(client):
    res = client.get("/auth/reset_passwd?user=alice&resetId=abc")
    assert res.status_code == 400
    assert res.mimetype == "text/html"             # 使用者看到錯誤頁，不是 JSON


def test_reset_link_with_wrong_id_shows_error_page(client):
    res = client.get("/auth/reset_passwd?user=alice&resetId=123456")
    assert res.status_code == 400
    assert res.mimetype == "text/html"


# ---- 登入 / me / 登出 ----
def test_failed_login_does_not_create_session(client):
    res = client.post("/auth/login", json={"login-username": "alice", "login-password": "wrong"})
    assert res.status_code == 401
    assert client.get("/auth/me").status_code == 401


def test_login_me_logout_flow(client):
    res = client.post("/auth/login", json={"login-username": "alice", "login-password": "correct-pw"})
    assert res.status_code == 200

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.get_json()["user"]["username"] == "alice"

    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/me").status_code == 401


def test_login_cookie_flags(client):
    res = client.post("/auth/login", json={"login-username": "alice", "login-password": "correct-pw"})
    cookie = res.headers["Set-Cookie"]
    # 這些是安全需求，用測試鎖住，防止日後被誤改
    assert cookie.startswith("__Host-session=")
    assert "Secure" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Expires=" in cookie                    # 確認 session.permanent 有生效
