from sqlalchemy.exc import IntegrityError
from modules.sql_module import DatabaseManager
from production.modules import Customer


class DuplicateCustomerError(Exception):
    """同一 workspace 內客戶名稱重複"""

class ConfigProcess:
    def __init__(self, db_m:DatabaseManager) -> None:
        self._db_m=db_m

    def add_customer(self, workspace_id:int, name:str)->Customer:
        with self._db_m.get_session() as session:
            cus = Customer(workspace_id=workspace_id, name=name.strip())
            session.add(cus)
            try:
                session.commit()
            except IntegrityError as e:
                session.rollback()
                if "uq_customers_workspace_name" in str(e.orig()):
                    raise DuplicateCustomerError(name):
                raise
            session.expunge(cus)
            return cus
