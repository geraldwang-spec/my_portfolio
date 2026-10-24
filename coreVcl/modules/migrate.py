"""資料庫 migration：在 app 開始服務之前，把資料庫升級到最新版本"""
from pathlib import Path

from alembic import command
from alembic.config import Config

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def upgrade_database(dburl: str | None = None) -> None:
    """等同命令列的 alembic upgrade head

    dburl：指定其他資料庫（測試用）；不指定就讀正式設定（環境變數 + /run/secrets）
    """
    cfg = Config(str(ALEMBIC_INI))
    if dburl is not None:
        cfg.attributes["dburl"] = dburl     # migrations/env.py 會優先使用這個值
    command.upgrade(cfg, "head")
