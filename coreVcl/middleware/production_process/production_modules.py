"""產線卡控的資料表（設計見 planning/data-model.md）

規則：
- 時間一律存 naive UTC（MariaDB 的 DATETIME 不存時區），用 utcnow() 取得
- 外鍵一律 ON DELETE RESTRICT：有人指向的資料刪不掉，測試紀錄不會被連帶刪除
- 測試紀錄只新增不修改；units.status / current_station_id 只在卡控服務的同一個交易裡更新
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Computed,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from modules.sql_module import Base


def utcnow() -> datetime:
    # 全專案只從這裡拿「現在」：存進 DB 的都是不帶時區的 UTC
    return datetime.now(UTC).replace(tzinfo=None)


def fk(target: str) -> ForeignKey:
    # 統一外鍵寫法，避免哪天有人改成 CASCADE 把測試紀錄連帶刪掉
    return ForeignKey(target, ondelete="RESTRICT")


def str_enum(cls: type[StrEnum]) -> Enum:
    # 存成 VARCHAR，不用 MariaDB 原生 ENUM：之後加狀態不用 ALTER 欄位；值由 Python 的 enum 把關
    return Enum(
        cls,
        native_enum=False,
        length=20,
        values_callable=lambda e: [m.value for m in e],
    )


class Role(StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class PartType(StrEnum):
    PRODUCT = "product"  # 成品
    SEMI = "semi"  # 半成品（中途換標用）
    BOARD = "board"  # 基板
    MODULE = "module"  # 模組
    PANEL = "panel"  # 拼板


class UnitStatus(StrEnum):
    WIP = "wip"  # 在製
    REPAIR = "repair"  # 維修中
    DONE = "done"  # 完成（這條途程走完）
    ASSEMBLED = "assembled"  # 已組裝（板子綁進上層，不能再測、不能再裝到別台）
    SCRAPPED = "scrapped"  # 報廢


class TestResult(StrEnum):
    PASS = "pass"
    FAIL = "fail"


# ---------- 工作區 ----------


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))  # 只給人看，不唯一
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(fk("workspaces.id"))
    user_id: Mapped[int] = mapped_column(fk("login.id"))  # 既有的登入表
    role: Mapped[Role] = mapped_column(str_enum(Role))
    joined_at: Mapped[datetime] = mapped_column(default=utcnow)


# ---------- 主檔 ----------


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("workspace_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(fk("workspaces.id"))
    name: Mapped[str] = mapped_column(String(100))


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("workspace_id", "project_code"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(fk("workspaces.id"))
    project_code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))
    customer_id: Mapped[int] = mapped_column(fk("customers.id"))


class Part(Base):
    __tablename__ = "parts"
    __table_args__ = (UniqueConstraint("workspace_id", "part_no"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(fk("workspaces.id"))
    part_no: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))
    project_id: Mapped[int] = mapped_column(fk("projects.id"))
    part_type: Mapped[PartType] = mapped_column(str_enum(PartType))


class PartBom(Base):
    """一列＝上層料號需要的一種子料；第一版只記錄，齊套檢查第二版才做"""

    __tablename__ = "part_bom"
    __table_args__ = (UniqueConstraint("parent_part_id", "slot"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_part_id: Mapped[int] = mapped_column(fk("parts.id"))
    child_part_id: Mapped[int] = mapped_column(fk("parts.id"))
    slot: Mapped[str] = mapped_column(String(50))
    qty: Mapped[int] = mapped_column(default=1)


class Station(Base):
    """途程：每個料號一條，seq 決定順序（留間隔 10、20、30）"""

    __tablename__ = "stations"
    __table_args__ = (UniqueConstraint("part_id", "seq"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    part_id: Mapped[int] = mapped_column(fk("parts.id"))
    seq: Mapped[int]
    station_name: Mapped[str] = mapped_column(String(50))
    allowed_sw_version: Mapped[str | None] = mapped_column(
        String(50)
    )  # None＝不檢查版本
    max_retry: Mapped[int] = mapped_column(default=3)
    config: Mapped[int] = mapped_column(default=1)  # 0＝抽測站，其他＝必測站
    bind_conf: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (UniqueConstraint("workspace_id", "employee_no"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(fk("workspaces.id"))
    employee_no: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(50))
    title: Mapped[str | None] = mapped_column(String(50))


# ---------- 序號與紀錄 ----------


class Unit(Base):
    """序號主檔：換料號＝新的一筆，序號在 (工作區, 料號) 內唯一"""

    __tablename__ = "units"
    __table_args__ = (UniqueConstraint("workspace_id", "part_id", "sn"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(fk("workspaces.id"))
    part_id: Mapped[int] = mapped_column(fk("parts.id"))
    sn: Mapped[str] = mapped_column(String(64))
    status: Mapped[UnitStatus] = mapped_column(
        str_enum(UnitStatus), default=UnitStatus.WIP
    )
    current_station_id: Mapped[int | None] = mapped_column(
        fk("stations.id")
    )  # 最後一個 PASS 的站
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class UnitBinding(Base):
    """組裝履歷：只新增，拆下時補上 unbound_at"""

    __tablename__ = "unit_bindings"
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_unit_id: Mapped[int] = mapped_column(fk("units.id"))
    child_unit_id: Mapped[int] = mapped_column(fk("units.id"))
    slot: Mapped[str] = mapped_column(String(50))
    bound_at: Mapped[datetime] = mapped_column(default=utcnow)
    unbound_at: Mapped[datetime | None]
    # 生成欄位：只有「目前在裝」才有值，NULL 可以重複 → 一片板子同時只能裝在一台
    # 用 CASE 不用 IF()：MariaDB 和 SQLite（測試）都支援
    active_child_id: Mapped[int | None] = mapped_column(
        Computed("CASE WHEN unbound_at IS NULL THEN child_unit_id END", persisted=True),
        unique=True,
    )


class Operation(Base):
    """作業員在某線、某治具登入的一段作業"""

    __tablename__ = "operations"
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(fk("employees.id"))
    product_line: Mapped[str] = mapped_column(String(30))
    fixture_id: Mapped[str | None] = mapped_column(String(50))
    login_at: Mapped[datetime] = mapped_column(default=utcnow)


class TestRecord(Base):
    """每測一次一筆，只新增不修改"""

    __tablename__ = "test_records"
    __test__ = False  # 名稱以 Test 開頭，告訴 pytest 這不是測試類別
    __table_args__ = (Index("ix_test_records_unit_station", "unit_id", "station_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    client_uuid: Mapped[str] = mapped_column(
        String(36), unique=True
    )  # 每次測試一個，網路重送沿用
    unit_id: Mapped[int] = mapped_column(fk("units.id"))
    station_id: Mapped[int] = mapped_column(fk("stations.id"))
    attempt_no: Mapped[int]  # 這個序號在這站第幾次測（一直累加）
    operation_id: Mapped[int | None] = mapped_column(fk("operations.id"))
    test_time: Mapped[datetime]  # 測試站端的量測時間
    received_at: Mapped[datetime] = mapped_column(default=utcnow)
    result: Mapped[TestResult] = mapped_column(str_enum(TestResult))
    defect_code: Mapped[str | None] = mapped_column(String(30))
    sw_version: Mapped[str] = mapped_column(String(50))
    test_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class Repair(Base):
    """送修單：開單時新增；修好時補上 action、employee_id、repaired_at（只補一次）"""

    __tablename__ = "repairs"
    __table_args__ = (Index("ix_repairs_unit", "unit_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(fk("units.id"))
    test_record_id: Mapped[int | None] = mapped_column(
        fk("test_records.id")
    )  # 觸發的那筆 FAIL
    error_code: Mapped[str | None] = mapped_column(String(30))
    abnormal: Mapped[str | None] = mapped_column(String(200))
    action: Mapped[str | None] = mapped_column(String(200))  # None＝待修
    employee_id: Mapped[int | None] = mapped_column(fk("employees.id"))
    opened_at: Mapped[datetime] = mapped_column(default=utcnow)
    repaired_at: Mapped[datetime | None]  # 重測上限從這個時間之後重新算
