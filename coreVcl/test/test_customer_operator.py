import pytest
from production.errors import InUseError, NotFoundError
from production.modules import Project, Workspace
from production.setting.config_process import ConfigProcess

from modules.sql_module import Base, DatabaseManager


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


@pytest.fixture(name="make_ws")
def _make_ws(db: DatabaseManager):
    def _make(name: str = "test ws") -> int:
        with db.get_session() as s:
            ws = Workspace(name=name)
            s.add(ws)
            s.commit()
            return ws.id

    return _make

@pytest.fixture
def test_name()->str:
    return "ACMP"


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

def test_delete_customer_not_found(ws_id:int, repo:ConfigProcess)->None:
    with pytest.raises(NotFoundError, match="999"):
        repo.delete_customer(ws_id, 999)

def test_detete_customer_of_other_workspace(make_ws, repo:ConfigProcess)->None:
    ws1,ws2 = make_ws("ws1"), make_ws("ws2")
    cus = repo.add_customer(ws1, "ACMP")
    with pytest.raises(NotFoundError):
        repo.delete_customer(ws2, cus.id)
    assert repo.get_customer(ws1, "ACMP") is not None

def test_delete_customer_in_use(db:DatabaseManager, ws_id:int, repo:ConfigProcess, test_name:str)->None:
    cus = repo.add_customer(ws_id, test_name)
    with db.get_session() as s:
        s.add(Project(workspace_id=ws_id, project_code="P001", name="Demo", customer_id=cus.id))
        s.commit()

    with pytest.raises(InUseError) as e:
        repo.delete_customer(ws_id, cus.id)

    err = e.value
    print(repr(err))
    assert repo.get_customer(ws_id, test_name) is not None

