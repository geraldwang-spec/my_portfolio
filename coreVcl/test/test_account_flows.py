"""註冊與忘記密碼：寄信失敗的補償、不透露帳號是否存在"""

import fakeredis
import pytest
from flask import Flask
from middleware.production_process.production_modules import (
    Role,
    Workspace,
    WorkspaceMember,
)
from sqlalchemy import event, func, select
from werkzeug.security import generate_password_hash

from auth.login_controller import LoginController
from auth.login_process import UserData
from modules.errors import APIError
from modules.services import Services
from modules.sql_module import Base, DatabaseManager, UserModule


class FakeMail:
    """取代 MailProcess：記錄寄了哪些信，可以設定成寄信失敗"""

    def __init__(self) -> None:
        self.fail = False
        self.sent: list[tuple[str, str]] = []  # (信件種類, 收件帳號)

    def send_verify_mail(self, user) -> bool:
        if self.fail:
            return False
        self.sent.append(("verify", user.username))
        return True

    def send_reset_mail(self, user, reset_nu) -> bool:
        if self.fail:
            return False
        self.sent.append(("reset", user.username))
        return True


@pytest.fixture
def env(tmp_path):
    db = DatabaseManager(db_url=f"sqlite:///{tmp_path / 'acct.db'}")

    # SQLite 預設不檢查外鍵；打開才測得出「有工作區成員時刪不掉帳號」這類問題
    @event.listens_for(db.engine, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(db.engine)
    users = UserData(db_manager=db)
    users.create_user(
        UserModule(
            username="alice",
            passwd=generate_password_hash("correct-pw"),
            mail="alice@example.com",
            mail_ready=True,
            mail_check_number=0,
        )
    )
    users.create_user(
        UserModule(
            username="bob",
            passwd=generate_password_hash("bob-pw"),
            mail="bob@example.com",
            mail_ready=False,
            mail_check_number=0,
        )
    )
    mail = FakeMail()
    redis = fakeredis.FakeRedis(decode_responses=True)
    core = LoginController(
        app=Flask(__name__), services=Services(db=db, redis=redis, mail=mail)
    )  # type: ignore[arg-type]
    return core, users, mail, redis


def count(db: DatabaseManager, model) -> int:
    """數某張表有幾筆，用來確認有沒有殘留資料"""
    with db.get_session() as session:
        return session.scalar(select(func.count()).select_from(model))


def memberships_of(db: DatabaseManager, username: str) -> list[tuple[str, Role]]:
    """回傳這個帳號加入的工作區：[(工作區名稱, 角色), ...]"""
    with db.get_session() as session:
        stmt = (
            select(Workspace.name, WorkspaceMember.role)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .join(UserModule, UserModule.id == WorkspaceMember.user_id)
            .where(UserModule.username == username)
        )
        return [tuple(row) for row in session.execute(stmt)]


# ---- 4-4 註冊 ----
def test_register_creates_user_then_sends_mail(env):
    core, users, mail, _ = env
    core.user_register(user_name="carol", passwd="password1", email="carol@example.com")
    assert users.get_user_by_username("carol") is not None
    assert mail.sent == [("verify", "carol")]


def test_register_rolls_back_when_mail_fails(env):
    core, users, mail, _ = env
    mail.fail = True
    with pytest.raises(APIError) as exc:
        core.user_register(
            user_name="carol", passwd="password1", email="carol@example.com"
        )
    assert (exc.value.status, exc.value.code) == (503, "mail_send_failed")
    assert users.get_user_by_username("carol") is None  # 補償：帳號已撤銷
    mail.fail = False
    core.user_register(
        user_name="carol", passwd="password1", email="carol@example.com"
    )  # 可以直接重新註冊


@pytest.mark.parametrize(
    "name, email, code",
    [
        ("alice", "new@example.com", "username_taken"),
        ("newbie", "alice@example.com", "email_taken"),
    ],
)
def test_register_duplicate_is_409(env, name, email, code):
    core, _, mail, _ = env
    with pytest.raises(APIError) as exc:
        core.user_register(user_name=name, passwd="password1", email=email)
    assert (exc.value.status, exc.value.code) == (409, code)
    assert mail.sent == []  # 沒有寄出任何信


# ---- 註冊時建立個人工作區 ----
def test_register_creates_personal_workspace(env):
    core, users, _, _ = env
    core.user_register(user_name="carol", passwd="password1", email="carol@example.com")
    assert memberships_of(users._db_m, "carol") == [("carol的工作區", Role.OWNER)]


def test_mail_failure_leaves_no_user_or_workspace(env):
    core, users, mail, _ = env
    db = users._db_m
    before = (count(db, UserModule), count(db, Workspace), count(db, WorkspaceMember))
    mail.fail = True
    with pytest.raises(APIError) as exc:
        core.user_register(
            user_name="carol", passwd="password1", email="carol@example.com"
        )
    assert exc.value.status == 503  # 不是 500：刪除沒有被外鍵擋下
    after = (count(db, UserModule), count(db, Workspace), count(db, WorkspaceMember))
    assert after == before  # 帳號、工作區、成員三張表都沒有殘留


def test_duplicate_user_creates_no_orphan_workspace(env):
    _, users, _, _ = env
    db = users._db_m
    workspaces_before = count(db, Workspace)
    # 直接呼叫 create_user，模擬兩人同時註冊、繞過 controller 事先檢查的情況
    dup = UserModule(
        username="alice",
        passwd="x",
        mail="other@example.com",
        mail_ready=False,
        mail_check_number=0,
    )
    assert users.create_user(dup) is False
    assert count(db, Workspace) == workspaces_before  # 交易回滾，工作區沒有多出來


# ---- 4-3 忘記密碼 ----
def test_reset_sends_mail_for_matching_verified_account(env):
    core, _, mail, _ = env
    core.send_reset_password(username="alice", email="alice@example.com")
    assert mail.sent == [("reset", "alice")]


@pytest.mark.parametrize(
    "name, email",
    [
        ("nobody", "nobody@example.com"),  # 帳號不存在
        ("alice", "wrong@example.com"),  # 帳號存在但 E-mail 不符
        ("bob", "bob@example.com"),  # E-mail 尚未驗證
    ],
)
def test_reset_silently_does_nothing(env, name, email):
    core, _, mail, _ = env
    core.send_reset_password(
        username=name, email=email
    )  # 不 raise：對外結果和成功時一樣
    assert mail.sent == []


def test_reset_within_cooldown_does_not_resend(env):
    core, _, mail, _ = env
    core.send_reset_password(username="alice", email="alice@example.com")
    core.send_reset_password(username="alice", email="alice@example.com")
    assert mail.sent == [("reset", "alice")]  # 5 分鐘內只寄一封


def test_reset_mail_failure_clears_code_so_user_can_retry(env):
    core, _, mail, redis = env
    mail.fail = True
    core.send_reset_password(username="alice", email="alice@example.com")
    assert redis.keys("reset:auth:*") == []  # 重設碼已清掉
    mail.fail = False
    core.send_reset_password(username="alice", email="alice@example.com")
    assert mail.sent == [("reset", "alice")]
