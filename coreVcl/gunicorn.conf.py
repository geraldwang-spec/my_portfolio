"""gunicorn 設定：開發和正式環境共用

啟動：python -m gunicorn -c gunicorn.conf.py "app:create_app()"
開發時加上 --reload，程式碼改動會自動重新啟動 worker
"""
from modules.migrate import upgrade_database

bind = "0.0.0.0:5000"
workers = 2            # 2 OCPU 的 VM；之後依實際負載調整
timeout = 60
accesslog = "-"        # access log 輸出到 stdout，podman logs 看得到
errorlog = "-"


def on_starting(server) -> None:
    """主程序在產生 worker 之前執行一次：先升級資料庫，失敗就不啟動"""
    server.log.info("running database migrations")
    upgrade_database()
    server.log.info("database is up to date")
