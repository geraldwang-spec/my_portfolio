"""convert database and tables to utf8mb4

Revision ID: ca65357e797c
Revises: 0e77458a3289
Create Date: 2026-11-12 21:31:37.152002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

CHARSET= "utf8mb4"
COLLATION="utf8mb4_unicode_ci"

# revision identifiers, used by Alembic.
revision: str = 'ca65357e797c'
down_revision: Union[str, Sequence[str], None] = '0e77458a3289'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name != "mysql":     # pymysql 連 MariaDB 時 dialect 名稱是 mysql；SQLite 本來就是 UTF-8，跳過
        return
    # 資料庫的預設值：之後新建的表會跟著用 utf8mb4
    op.execute(f"ALTER DATABASE CHARACTER SET {CHARSET} COLLATE {COLLATION}")
    # 既有的表：連同欄位、現有資料一起轉換
    for table in sa.inspect(bind).get_table_names():   # 表名來自資料庫本身，不是使用者輸入
        op.execute(f"ALTER TABLE `{table}` CONVERT TO CHARACTER SET {CHARSET} COLLATE {COLLATION}")


def downgrade() -> None:
    # 不轉回 latin1：已經存進去的中文會變成亂碼或轉換失敗。要退回請用備份還原
    pass
