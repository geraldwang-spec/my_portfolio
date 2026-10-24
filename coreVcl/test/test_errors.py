# test/test_errors.py
from flask import Flask

from modules.errors import APIError, register_error_handlers


def make_app() -> Flask:
    app = Flask(__name__)
    register_error_handlers(app)

    @app.post("/api/boom")
    def boom():
        raise APIError("壞掉了", status=409, code="conflict")

    @app.post("/api/crash")
    def crash():
        raise RuntimeError("secret detail")   # 模擬沒預期的錯誤

    return app

def test_api_error_keeps_status_and_code():
    res = make_app().test_client().post("/api/boom", json={})
    assert res.status_code == 409
    assert res.get_json() == {"success": False, "message": "壞掉了", "data": {"code": "conflict"}}

def test_unexpected_error_is_500_and_hides_detail():
    res = make_app().test_client().post("/api/crash", json={})
    assert res.status_code == 500
    assert "secret detail" not in res.get_data(as_text=True)   # 內部訊息不可外洩

