"""Record tools: generic CRUD + schema over SuiteTalk record/v1 (any record type)."""
from __future__ import annotations

import json

from imperal_sdk import ActionResult

import netsuite_client as nc
from app import chat
from handlers_connection import resolve_or_error
from schemas import (
    CreateRecordParams, DeleteRecordParams, DeleteResult, GetRecordParams,
    GetSchemaParams, ListRecordsParams, RecordDetail, RecordList,
    RecordSchemaResult, RecordWriteResult, UpdateRecordParams,
)


def _items(data) -> list:
    if isinstance(data, dict):
        items = data.get("items")
        if isinstance(items, list):
            return items
    if isinstance(data, list):
        return data
    return []


def _parse_fields(fields_json: str) -> dict | ActionResult:
    try:
        data = json.loads(fields_json)
    except ValueError:
        return ActionResult.error(nc.NS_VALIDATION, "fields_json is not valid JSON.")
    if not isinstance(data, dict):
        return ActionResult.error(nc.NS_VALIDATION, "fields_json must be a JSON object.")
    return data


@chat.function(
    "list_records",
    "List NetSuite records of any record type (customer, salesorder, invoice, item, vendor, ...) with "
    "limit/offset pagination, via SuiteTalk record/v1.",
    action_type="read", chain_callable=True, data_model=RecordList,
)
async def list_records(ctx, params: ListRecordsParams) -> ActionResult:
    """GET /record/v1/{record_type} with limit+offset."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        data = await nc.request(
            conn, "GET", f"/record/v1/{params.record_type}",
            params={"limit": params.limit, "offset": params.offset},
        )
    except nc.NetsuiteError as exc:
        return ActionResult.error(exc.code, exc.message)
    items = _items(data)
    total = data.get("totalResults") if isinstance(data, dict) else None
    has_more = bool(isinstance(data, dict) and data.get("hasMore"))
    return ActionResult.success(RecordList(items=items, total=total, has_more=has_more), summary="Records listed.")


@chat.function(
    "get_record",
    "Read one NetSuite record of any type in full by its internal id (e.g. customer 1042).",
    action_type="read", chain_callable=True, data_model=RecordDetail,
)
async def get_record(ctx, params: GetRecordParams) -> ActionResult:
    """GET /record/v1/{record_type}/{id}."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        data = await nc.request(conn, "GET", f"/record/v1/{params.record_type}/{params.record_id}")
    except nc.NetsuiteError as exc:
        return ActionResult.error(exc.code, exc.message)
    return ActionResult.success(RecordDetail(record=data if isinstance(data, dict) else {"raw": data}), summary="Record retrieved.")


@chat.function(
    "get_record_schema",
    "Read a NetSuite record type's field schema from the REST metadata catalog -- which fields exist, their "
    "types, and which are required. Use before create_record/update_record.",
    action_type="read", chain_callable=True, data_model=RecordSchemaResult,
)
async def get_record_schema(ctx, params: GetSchemaParams) -> ActionResult:
    """GET /record/v1/metadata-catalog/{record_type}."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        data = await nc.request(conn, "GET", f"/record/v1/metadata-catalog/{params.record_type}")
    except nc.NetsuiteError as exc:
        return ActionResult.error(exc.code, exc.message)
    return ActionResult.success(RecordSchemaResult(
        record_type=params.record_type,
        schema=data if isinstance(data, dict) else {"raw": data},
    ), summary="Record schema retrieved.")


@chat.function(
    "create_record",
    "Create a new NetSuite record of any type from a JSON object of its fields (use get_record_schema first "
    "to see valid fields), e.g. a new customer or sales order.",
    action_type="write", chain_callable=True, data_model=RecordWriteResult,
)
async def create_record(ctx, params: CreateRecordParams) -> ActionResult:
    """POST /record/v1/{record_type} with the given fields; 204/Location id."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    fields = _parse_fields(params.fields_json)
    if isinstance(fields, ActionResult):
        return fields
    try:
        data = await nc.request(conn, "POST", f"/record/v1/{params.record_type}", body=fields)
    except nc.NetsuiteError as exc:
        return ActionResult.error(exc.code, exc.message)
    rid = ""
    if isinstance(data, dict):
        rid = str(data.get("id") or "")
    return ActionResult.success(RecordWriteResult(
        ok=True, record_id=rid, message=f"{params.record_type} created.",
    ), summary="Record created.")


@chat.function(
    "update_record",
    "Update selected fields of an existing NetSuite record (PATCH). Only the fields in fields_json change.",
    action_type="write", chain_callable=True, data_model=RecordWriteResult,
)
async def update_record(ctx, params: UpdateRecordParams) -> ActionResult:
    """PATCH /record/v1/{record_type}/{id} with the given fields."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    fields = _parse_fields(params.fields_json)
    if isinstance(fields, ActionResult):
        return fields
    try:
        await nc.request(conn, "PATCH", f"/record/v1/{params.record_type}/{params.record_id}", body=fields)
    except nc.NetsuiteError as exc:
        return ActionResult.error(exc.code, exc.message)
    return ActionResult.success(RecordWriteResult(
        ok=True, record_id=params.record_id, message=f"{params.record_type} {params.record_id} updated.",
    ), summary="Record updated.")


@chat.function(
    "delete_record",
    "Permanently delete a NetSuite record of any type by internal id. Cannot be undone through the API.",
    action_type="destructive", chain_callable=True, data_model=DeleteResult,
    event="netsuite.record.deleted",
)
async def delete_record(ctx, params: DeleteRecordParams) -> ActionResult:
    """DELETE /record/v1/{record_type}/{id}."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        await nc.request(conn, "DELETE", f"/record/v1/{params.record_type}/{params.record_id}")
    except nc.NetsuiteError as exc:
        return ActionResult.error(exc.code, exc.message)
    return ActionResult.success(DeleteResult(
        deleted=True, message=f"{params.record_type} {params.record_id} deleted.",
    ), summary="Record deleted.")
