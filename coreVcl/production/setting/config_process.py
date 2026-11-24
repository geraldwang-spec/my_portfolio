from math import e
import select
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from modules.sql_module import DatabaseManager
from production.db_errors import is_fk_violation, is_unique_violation
from production.errors import DuplicateError, InUseError, NotFoundError
from production.modules import Customer


class ConfigProcess:
    def __init__(self, db_m: DatabaseManager) -> None:
        self._db_m = db_m

    def add_customer(self, workspace_id: int, name: str) -> Customer:
        with self._db_m.get_session() as session:
            cus = Customer(workspace_id=workspace_id, name=name.strip())
            session.add(cus)
            try:
                session.commit()
            except IntegrityError as e:
                session.rollback()
                if is_unique_violation(e):
                    raise DuplicateError("customer", cus.name) from e
                raise
            session.expunge(cus)
            return cus

    def get_customer(self, workspace_id: int, name: str) -> Customer | None:
        with self._db_m.get_session() as session:
            return session.scalar(
                select(Customer).where(
                    Customer.workspace_id == workspace_id, Customer.name == name.strip()
                )
            )

    def delete_customer(self, workspace_id: int, customer_id: int) -> None:
        with self._db_m.get_session() as session:
            try:
                result = session.execute(
                    delete(Customer).where(
                        Customer.workspace_id == workspace_id,
                        Customer.id == customer_id,
                    )
                )
                session.commit()
            except IntegrityError as e:
                session.rollback()
                if is_fk_violation(e):
                    raise InUseError("customer", str(customer_id)) from e
                raise
            if result.rowcount == 0:
                raise NotFoundError("customer", str(customer_id))
