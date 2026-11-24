from sqlalchemy.exc import IntegrityError

MYSQL_DUP_ENTRY = 1062  # MariaDB/MySQL：Duplicate entry
MYSQL_ROW_IS_REFERENCED = 1451  # 刪除被參照的父資料
MYSQL_NO_REFERENCED_ROW = 1452  # 新增時外鍵指向不存在的資料


def is_unique_violation(e: IntegrityError) -> bool:
    args = getattr(e.orig, "args", ())
    if args and args[0] == MYSQL_DUP_ENTRY:
        return True
    return "UNIQUE constraint failed" in str(e.orig)  # sqlite3：只有訊息字串


def is_fk_violation(e: IntegrityError) -> bool:
    args = getattr(e.orig, "args", ())
    if args and args[0] in (MYSQL_ROW_IS_REFERENCED, MYSQL_NO_REFERENCED_ROW):
        return True
    return "FOREIGN KEY constraint failed" in str(e.orig)
