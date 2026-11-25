from ntpath import exists
import fakeredis
import pytest
from flask import Flask
from production.modules import Role, Workspace, WorkspaceMember
from sqlalchemy import event, func, select
from werkzeug.security import generate_password_hash

from auth.login_controller import LoginController
from auth.login_process import UserData
from modules.errors import APIError
from modules.services import Services
from modules.sql_module import Base, DatabaseManager, UserModule
from production.setting.config_process import ConfigProcess


@pytest.fixture
def env(tmp_path):
    print(f"{tmp_path}")
    db = DatabaseManager(db_url=f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(db.engine)
    return db


@pytest.fixture
def ws_id(env: DatabaseManager) -> int:
    with env.get_session() as s:
        ws = Workspace(name="test ws")
        s.add(ws)
        s.commit()
        return ws.id


@pytest.fixture
def repo(env) -> ConfigProcess:
    return ConfigProcess(env)


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
