from enum import StrEnum


class GateCode(StrEnum):
    SKIPPED_STATION = "skipped_station"  # 上一個必測站還沒 PASS
    RETRY_LIMIT = "retry_limit"  # 達重測上限，需送修
    WRONG_SW_VERSION = "wrong_sw_version"  # 測試程式版本不符
    UNIT_NOT_TESTABLE = "unit_not_testable"  # 維修中／已組裝／報廢


class GateError(Exception):
    def __init__(self, code: GateCode, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message
