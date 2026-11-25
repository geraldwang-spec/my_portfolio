from datetime import UTC, datetime, timedelta

from typing import Any
from sqlalchemy import Boolean, Engine, Integer, String, create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class UserModule(Base):
    __tablename__: str = "login"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    passwd: Mapped[str] = mapped_column(String(255), nullable=False)
    mail: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    mail_ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mail_check_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    account_created: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(UTC)
    )
    mail_check_time: Mapped[datetime] = mapped_column(
        unique=False,
        default=lambda: (
            datetime.now(tz=UTC).replace(microsecond=0) + timedelta(minutes=15)
        ),
    )


class DatabaseManager:
    def __init__(self, db_url: str | URL = "sqlite:///login.db") -> None:
        self.engine: Engine = create_engine(
            url=db_url,
            echo=False,
            hide_parameters=True,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        # 2. SQLite 才需要：每條新連線都打開外鍵檢查，讓測試行為跟 MariaDB 一致
        if self.engine.dialect.name == "sqlite":

            @event.listens_for(self.engine, "connect")
            def _enable_fk(dbapi_conn: Any, _record: Any) -> None:
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        self._session_factory: sessionmaker[Session] = sessionmaker(
            bind=self.engine, expire_on_commit=False
        )

    def get_session(self) -> Session:
        return self._session_factory()
