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


class DuplicateError(Exception):
    def __init__(self, entity: str, key: str) -> None:
        super().__init__(f"{entity} already exists: {key}")
        self.entity, self.key = entity, key


class NotFoundError(Exception):
    def __init__(self, entity: str, key: str) -> None:
        super().__init__(f"{entity} not found: {key}")
        self.entity, self.key = entity, key


class InUseError(Exception):
    def __init__(self, entity: str, key: str) -> None:
        super().__init__(f"{entity} is still use: {key}")
        self.entity, self.key = entity, key
