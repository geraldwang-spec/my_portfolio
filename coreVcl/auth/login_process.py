import logging

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from modules.sql_module import DatabaseManager, UserModule

logger = logging.getLogger(__name__)


class UserData:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db_m = db_manager

    # 查詢：DB 錯誤直接往上拋（由 error handler 回 500），None 只代表「查不到」
    # 寫入：失敗時記 log 並回傳 False，由 controller 決定回應
    def create_user(self, user_data: UserModule) -> bool:
        """建立帳號；帳號或 E-mail 重複（違反 unique）回傳 False，其他 DB 錯誤往上拋"""
        with self._db_m.get_session() as session:
            try:
                session.add(user_data)
                session.commit()
                return True
            except IntegrityError:
                session.rollback()
                logger.warning("create user rejected by unique constraint")
                return False

    def delete_user(self, username:str) -> None:
        with self._db_m.get_session() as session:
            session.execute(delete(UserModule).where(UserModule.username == username))
            session.commit()

    def get_user_by_username(self, username:str) -> UserModule | None:
        with self._db_m.get_session() as session:
            stmt = select(UserModule).where(UserModule.username == username)
            user = session.scalars(stmt).first()
            if user:
                session.expunge(user)
            return user

    def get_user_by_mail(self, mail:str) -> UserModule | None:
        with self._db_m.get_session() as session:
            stmt = select(UserModule).where(UserModule.mail == mail)
            user = session.scalars(stmt).first()
            if user:
                session.expunge(user)
            return user

    def get_user_by_username_and_mail(self, username:str, mail:str) -> UserModule|None:
        with self._db_m.get_session() as session:
            stmt = select(UserModule).where((UserModule.username == username) & (UserModule.mail == mail))
            user = session.scalars(stmt).first()
            if user:
                session.expunge(user)
            return user

    def update_mail_ready(self, username:str, ready:bool) ->bool:
        with self._db_m.get_session() as session:
            try:
                stmt = select(UserModule).where(UserModule.username == username)
                user = session.scalars(stmt).first()
                if not user:
                    logger.warning("update mail_ready: user not found")
                    return False

                user.mail_ready = ready
                session.commit()
                return True
            except SQLAlchemyError:
                session.rollback()
                logger.exception("update mail_ready failed")
                return False

    def update_password_by_user(self, user:str, pwd_hash:str)->bool:
        with self._db_m.get_session() as session:
            try:
                stmt = select(UserModule).where(UserModule.username == user)
                user_row = session.scalars(stmt).first()
                if not user_row:
                    logger.warning("update password: user not found")
                    return False

                user_row.passwd = pwd_hash
                session.commit()
                return True
            except SQLAlchemyError:
                session.rollback()
                logger.exception("update password failed")
                return False
