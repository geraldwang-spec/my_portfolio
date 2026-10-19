"""寄信失敗的 log 只能出現網域，不能出現完整 Email"""
from modules.mail_process import _mail_domain


def test_plain_address_keeps_domain_only():
    assert _mail_domain(["alice@gmail.com"]) == "gmail.com"


def test_named_tuple_recipient():
    assert _mail_domain([("Alice", "alice@example.com")]) == "example.com"


def test_empty_or_invalid():
    assert _mail_domain(None) == "-"
    assert _mail_domain([]) == "-"
    assert _mail_domain(["not-an-email"]) == "-"
