from auth.login_redis_process import LoginRedisProcess as auth_rds
from modules.sql_module import UserModule as userM

def test_redis():
    test_rds = auth_rds("127.0.0.1", "vclpasswd")
    result, mesg = test_rds.reset_password_number_test("ddd", "ddd@example.com", 2, 222)
    if not result:
        print(mesg)
    else:
        print("account exist")

