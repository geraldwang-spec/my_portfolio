"""重設碼錯誤次數上限：用 fakeredis 取代真的 Redis，CI 不需要啟動容器"""
from types import SimpleNamespace

import fakeredis
import pytest
from auth import login_redis_process as lrp

USER_ID = 7
CODE = 123456
WRONG = 111111
KEY = f"reset:auth:{USER_ID}"


@pytest.fixture
def fake():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def rds(fake):
     # FakeRedis 是 redis.Redis 的子類別，可以直接從建構子傳進去，不用 monkeypatch
    return lrp.LoginRedisProcess(client=fake)

@pytest.fixture
def user():
    # 只需要 id、username、mail 三個屬性，不必建立真的 UserModule
    return SimpleNamespace(id=USER_ID, username="u", mail="u@example.com")


def test_correct_code_passes(rds, user):
    rds.reset_password_number(user=user, number=CODE)
    assert rds.verify_reset_number(userId=USER_ID, reset_id=CODE)


def test_wrong_code_fails(rds, user):
    rds.reset_password_number(user=user, number=CODE)
    assert not rds.verify_reset_number(userId=USER_ID, reset_id=WRONG)


def test_invalidated_after_max_attempts(rds, user, fake):
    rds.reset_password_number(user=user, number=CODE)
    for _ in range(lrp.LoginRedisProcess.MAX_ATTEMPTS):
        assert not rds.verify_reset_number(userId=USER_ID, reset_id=WRONG)

    # 關鍵：作廢後連正確的碼也不能用
    assert not fake.exists(KEY)
    assert not rds.verify_reset_number(userId=USER_ID, reset_id=CODE)


def test_one_below_limit_still_allows_correct_code(rds, user, fake):
    rds.reset_password_number(user=user, number=CODE)
    for _ in range(lrp.LoginRedisProcess.MAX_ATTEMPTS - 1):
        rds.verify_reset_number(userId=USER_ID, reset_id=WRONG)

    assert rds.verify_reset_number(userId=USER_ID, reset_id=CODE)
    assert fake.ttl(KEY) > 0          # 累加 fails 不會讓 key 失去期限


def test_can_request_again_after_lockout(rds, user):
    rds.reset_password_number(user=user, number=CODE)
    for _ in range(lrp.LoginRedisProcess.MAX_ATTEMPTS):
        rds.verify_reset_number(userId=USER_ID, reset_id=WRONG)

    ok, _ = rds.reset_password_number(user=user, number=654321)
    assert ok


def test_missing_key_is_not_recreated_without_ttl(rds, fake):
    # 沒有申請過重設碼時驗證，不能留下沒有期限的 key（否則之後無法再申請）
    assert not rds.verify_reset_number(userId=USER_ID, reset_id=WRONG)
    assert not fake.exists(KEY)
