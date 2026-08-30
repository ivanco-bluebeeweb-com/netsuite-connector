"""Pydantic schemas for every NetSuite Connector tool (V17/V18/V23)."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------- params ----

class ConnectNetsuiteParams(BaseModel):
    label: str = Field(default="", description="A friendly name for this account, e.g. 'Acme production ERP'.")
    account_id: str = Field(description="NetSuite account id, e.g. '1234567' (production) or '1234567_SB1' (sandbox).")
    consumer_key: str = Field(description="Consumer key from the NetSuite Integration record (TBA enabled).")
    consumer_secret: str = Field(description="Consumer secret from the same Integration record.")
    token_key: str = Field(description="Token key from the NetSuite Access Token page.")
    token_secret: str = Field(description="Token secret from the same Access Token page.")


class ConnectionIdParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")


class ListRecordsParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    record_type: str = Field(description="NetSuite record type, e.g. 'customer', 'salesorder', 'invoice', 'item', 'vendor'.")
    limit: int = Field(default=50, ge=1, le=1000, description="Max records to return (1-1000).")
    offset: int = Field(default=0, ge=0, description="Skip this many records (pagination).")


class GetRecordParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    record_type: str = Field(description="NetSuite record type, e.g. 'customer'.")
    record_id: str = Field(description="Internal id of the record.")


class CreateRecordParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    record_type: str = Field(description="NetSuite record type to create, e.g. 'customer'.")
    fields_json: str = Field(description="JSON object of the record's fields, e.g. {\"companyName\": \"Acme Ltd\"}. Use get_record_schema first to see valid fields.")


class UpdateRecordParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    record_type: str = Field(description="NetSuite record type, e.g. 'customer'.")
    record_id: str = Field(description="Internal id of the record to update.")
    fields_json: str = Field(description="JSON object of only the fields to change.")


class DeleteRecordParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    record_type: str = Field(description="NetSuite record type, e.g. 'customer'.")
    record_id: str = Field(description="Internal id of the record to delete.")


class GetSchemaParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    record_type: str = Field(description="NetSuite record type whose field schema to read, e.g. 'customer'.")


class RunSuiteqlParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    query: str = Field(description="SuiteQL SELECT query, e.g. \"SELECT id, companyName FROM customer\". Read-only.")
    limit: int = Field(default=100, ge=1, le=1000, description="Max rows to return (1-1000).")
    offset: int = Field(default=0, ge=0, description="Skip this many rows (pagination).")


class ReportParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    scan_limit: int = Field(default=100, ge=10, le=1000, description="How many rows each report scan reads.")


# ---------------------------------------------------------------- results ---

class ConnectionRecord(BaseModel):
    id: str
    label: str
    account_id: str
    masked_key: str


class ConnectionList(BaseModel):
    items: list[ConnectionRecord]
    total: int


class ConnectNetsuiteResult(BaseModel):
    connected: bool
    connection_id: str
    label: str
    message: str


class DeleteResult(BaseModel):
    deleted: bool
    message: str


class RecordList(BaseModel):
    items: list[dict[str, Any]]
    total: Optional[int] = None
    has_more: bool = False


class RecordDetail(BaseModel):
    record: dict[str, Any]


class RecordWriteResult(BaseModel):
    ok: bool
    record_id: str = ""
    message: str


class RecordSchemaResult(BaseModel):
    record_type: str
    schema: dict[str, Any]


class SuiteqlResult(BaseModel):
    rows: list[dict[str, Any]]
    total: Optional[int] = None
    has_more: bool = False


class AccountOverviewReport(BaseModel):
    label: str
    account_id: str
    counts: dict[str, int]
    notes: list[str] = []


class OpenSalesOrdersReport(BaseModel):
    label: str
    scanned: int
    open_count: int
    orders: list[dict[str, Any]]
    notes: list[str] = []
