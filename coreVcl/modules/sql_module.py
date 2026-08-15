from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from sqlalchemy import Boolean, Engine, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

class Base(DeclarativeBase):
    pass

class UserModule(Base):
    __tablename__:str = "login"
    id:Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username:Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    passwd:Mapped[str] = mapped_column(String(255), nullable=False)
    mail: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    # name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    mail_ready:Mapped[bool] = mapped_column(Boolean, nullable=False, default=False) 
    mail_check_number:Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    account_created:Mapped[datetime] = mapped_column(
        nullable= False, 
        default=lambda: datetime.now(timezone.utc))
    mail_check_time:Mapped[datetime] = mapped_column(
        unique=False,
        default=lambda: datetime.now(tz=timezone.utc).replace(microsecond=0)+timedelta(minutes=15)
    ) 

@dataclass
class GameModule:
    user_name:str=""
    user_choice:str=""
    computer_choice:str = ""
    result:str = ""
    pass_count:int = 0

class DatabaseManager:
    def __init__(self, db_url:str = "sqlite:///login.db") -> None:
        self.engine: Engine = create_engine(db_url, echo=False)
        self.__session_factory:sessionmaker[Session] = sessionmaker(bind=self.engine, expire_on_commit=False)

    def init_db(self)->None:
        Base.metadata.create_all(bind=self.engine)

    def get_session(self)->Session:
        return self.__session_factory()


