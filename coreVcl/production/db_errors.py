from sqlalchemy.exc import IntegrityError

MYSQL_DUP_ENTRY = 1062  # MariaDB/MySQL：Duplicate entry


def is_unique_violation(e: IntegrityError) -> bool:
    args = getattr(e.orig, "args", ())
    if args and args[0] == MYSQL_DUP_ENTRY:
        return True
    return "UNIQUE constraint failed" in str(e.orig)  # sqlite3：只有訊息字串
