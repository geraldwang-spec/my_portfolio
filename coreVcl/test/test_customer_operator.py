from ntpath import exists
import fakeredis
import pytest
from flask import Flask
from production.modules import Customer, Role, Workspace, WorkspaceMember
from sqlalchemy import event, func, select
from werkzeug.security import generate_password_hash

from auth.login_controller import LoginController
from auth.login_process import UserData
from modules.errors import APIError
from modules.services import Services
from modules.sql_module import Base, DatabaseManager, UserModule
from production.setting.config_process import ConfigProcess


@pytest.fixture
def db(tmp_path):
    print(f"{tmp_path}")
    d = DatabaseManager(db_url=f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(d.engine)
    return d


@pytest.fixture
def ws_id(db: DatabaseManager) -> int:
    with db.get_session() as s:
        ws = Workspace(name="test ws")
        s.add(ws)
        s.commit()
        return ws.id


@pytest.fixture
def repo(db) -> ConfigProcess:
    return ConfigProcess(db)


@pytest.fixture
def _make_ws(_db: DatabaseManager):
    def _make(name: str = "test ws") -> int:
        with _db.get_session() as s:
            ws = Workspace(name=name)
            s.add(ws)
            s.commit()
            return ws.id

    return _make


def test_add_customer(ws_id: int, repo: ConfigProcess) -> None:
    cus = repo.add_customer(ws_id, "ACME")
    assert cus.id is not None
    assert cus.name == "ACME"


def test_get_customer(ws_id: int, repo: ConfigProcess) -> None:
    repo.add_customer(workspace_id=ws_id, name="QOO")
    cus = repo.get_customer(ws_id, "QOO")
    # print(f"cus.id = {cus.id}")
    # print(f"cus.name = {cus.name}")
    assert cus is not None
    assert cus.workspace_id == ws_id
    assert cus.name == "QOO"
    assert cus.id != 0


def test_get_customer_not_found_customer(ws_id: int, repo: ConfigProcess) -> None:
    assert repo.get_customer(ws_id, "NOPE") is None


def test_get_customer_other_workspace(db: DatabaseManager, repo: ConfigProcess) -> None:
    with db.get_session() as session:
        ws1, ws2 = Workspace(name="WS1"), Workspace(name="WS2")
        session.add_all([ws1, ws2])
        session.commit()

    repo.add_customer(ws1.id, "QOO")
    assert repo.get_customer(ws2.id, "ACMP") is None


def test_detete_customer(ws_id: int, repo: ConfigProcess) -> None:
    cus = repo.add_customer(ws_id, "ACMP")
    repo.delete_customer(ws_id, cus.id)
    assert repo.get_customer(ws_id, cus.name) is None
