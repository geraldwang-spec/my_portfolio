from sys import modules
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from modules.sql_module import DatabaseManager,UserModule

class UserData:
    _db_m:DatabaseManager
    __pass_count:int

    def __init__(self, db_manager:DatabaseManager ) -> None:
        self._db_m = db_manager
        self.__pass_count:int = 0

    def set_pass_count(self):
        self.__pass_count += 1

    def get_pass_count(self):
        return self.__pass_count

    # datebase process
    def create_user(self, user_data: UserModule)->bool:
        with self._db_m.get_session() as session:
            try:
                session.add(user_data)
                session.commit()
                return True
            except SQLAlchemyError as e:
                session.rollback()
                print(f"create user db failed: {e}")
                return False

    def get_user_by_username(self, username:str) -> UserModule | None:
        with self._db_m.get_session() as session:
            try:
                stmt = select(UserModule).where(UserModule.username == username)
                user = session.scalars(stmt).first()
                if user:
                    session.expunge(user)
                return user
            except SQLAlchemyError as e:
                session.rollback()
                print(f"get user db failed: {e}")
                return None

    def update_mail_ready(self, username:str, ready:bool) ->bool:
        with self._db_m.get_session() as session:
            try:
                stmt = select(UserModule).where(UserModule.username == username)
                user = session.scalars(stmt).first()
                if not user:
                    print(f"can't find user = {username}")
                    return False

                user.mail_ready = ready
                session.commit()
                return True
            except SQLAlchemyError as e:
                session.rollback()
                print(f"Update mail ready db failed: {e}")
                return False






