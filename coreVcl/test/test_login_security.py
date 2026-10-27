"""登入安全：不透露帳號是否存在、同一帳號連續失敗會暫時鎖定"""
import fakeredis
import pytest
from flask import Flask
from werkzeug.security import generate_password_hash

from auth.login_controller import LoginController
from auth.login_process import UserData
from auth.login_redis_process import LoginRedisProcess
from modules.errors import APIError
from modules.services import Services
from modules.sql_module import Base, DatabaseManager, UserModule


@pytest.fixture
def db(tmp_path):
    manager = DatabaseManager(db_url=f"sqlite:///{tmp_path / 'login.db'}")
    Base.metadata.create_all(manager.engine)
    users = UserData(db_manager=manager)
    users.create_user(UserModule(username="alice", passwd=generate_password_hash("correct-pw"),
                                 mail="alice@example.com", mail_ready=True, mail_check_number=0))
    users.create_user(UserModule(username="bob", passwd=generate_password_hash("bob-pw"),
                                 mail="bob@example.com", mail_ready=False, mail_check_number=0))
    return manager


@pytest.fixture
def core(db):
    # 只測 controller：Redis 用 fakeredis，登入流程不會寄信所以 mail 給 None
    services = Services(db=db, redis=fakeredis.FakeRedis(decode_responses=True), mail=None)  # type: ignore[arg-type]
    return LoginController(app=Flask(__name__), services=services)


def login_error(core, username, passwd) -> APIError:
    with pytest.raises(APIError) as exc:
        core.check_user_status(username=username, passwd=passwd)
    return exc.value


def test_correct_password_returns_username(core):
    assert core.check_user_status(username="alice", passwd="correct-pw") == "alice"


def test_unknown_user_and_wrong_password_look_the_same(core):
    unknown = login_error(core, "nobody", "x")
    wrong = login_error(core, "alice", "x")
    # 訊息、狀態碼、錯誤碼完全相同，攻擊者分不出帳號存不存在
    assert (unknown.message, unknown.status, unknown.code) == (wrong.message, wrong.status, wrong.code)
    assert unknown.status == 401


def test_unverified_email_only_after_correct_password(core):
    assert login_error(core, "bob", "wrong").code == "invalid_credentials"
    assert login_error(core, "bob", "bob-pw").code == "email_not_verified"


# ---- 連續失敗鎖定 ----
def fail_times(core, username, n):
    for _ in range(n):
        assert login_error(core, username, "wrong").code == "invalid_credentials"


def test_locked_after_five_failures_even_with_correct_password(core):
    fail_times(core, "alice", 5)
    err = login_error(core, "alice", "correct-pw")      # 第 6 次：密碼正確也不接受
    assert (err.status, err.code) == (429, "too_many_attempts")


def test_success_resets_counter(core):
    fail_times(core, "alice", 4)
    assert core.check_user_status(username="alice", passwd="correct-pw") == "alice"
    fail_times(core, "alice", 4)                        # 歸零後重新計算，還沒到 5 次
    assert core.check_user_status(username="alice", passwd="correct-pw") == "alice"


def test_lock_is_per_account(core):
    fail_times(core, "alice", 5)
    assert login_error(core, "bob", "bob-pw").code == "email_not_verified"   # 別的帳號不受影響


def test_unknown_user_is_locked_the_same_way(core):
    # 不存在的帳號也會被鎖：「會不會被鎖」不能洩漏帳號是否存在
    fail_times(core, "nobody", 5)
    assert login_error(core, "nobody", "x").code == "too_many_attempts"


def test_username_case_shares_one_counter(core):
    fail_times(core, "Alice", 3)
    fail_times(core, "alice", 2)
    assert login_error(core, "alice", "correct-pw").code == "too_many_attempts"


def test_lock_expires(core):
    fail_times(core, "alice", 5)
    assert core._rds._rds.ttl("login:fail:alice") <= LoginRedisProcess.LOGIN_LOCK_SECONDS
    core._rds._rds.delete("login:fail:alice")           # 模擬 15 分鐘到期
    assert core.check_user_status(username="alice", passwd="correct-pw") == "alice"
