from flask import Flask, Response
from werkzeug.exceptions import HTTPException

from modules.api_response import ApiResponse


class APIError(Exception):
    """可預期的業務錯誤：在任何一層 raise，狀態碼跟著錯誤一起走"""
    message: str
    status: int
    code: str

    def __init__(self, message: str, status: int = 400, code: str = "bad_request") -> None:
        super().__init__(message)   # 讓 str(e) 和 log 顯示 message
        self.message, self.status, self.code = message, status, code


def _error_body(message: str, code: str) -> Response:
    return ApiResponse(success=False, message=message, data={"code": code}).to_response()


def register_error_handlers(app: Flask) -> None:
    def _api_error(e: APIError) -> tuple[Response, int]:
        return _error_body(e.message, e.code), e.status

    def _http_error(e: HTTPException) -> tuple[Response, int]:
        code = (e.name or "error").lower().replace(" ", "_")   # Not Found → not_found
        return _error_body(e.description or e.name, code), e.code or 500

    def _unexpected(e: Exception) -> tuple[Response, int]:
        app.logger.exception("unhandled error")   # 必要：被接住的例外 Flask 不會自動記錄
        return _error_body("Server error, please try again later", "internal_error"), 500

    # 明確登記：效果和 @app.errorhandler 相同，型別檢查器也看得出函式有被使用
    app.register_error_handler(APIError, _api_error)
    app.register_error_handler(HTTPException, _http_error)
    app.register_error_handler(Exception, _unexpected)
