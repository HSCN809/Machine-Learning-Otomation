"""Selective timeline rollback helpers."""

from __future__ import annotations

import ast
from typing import Any

import numpy as np
import pandas as pd
from fastapi import HTTPException

from backend.modules.config import settings
from backend.modules.data_preprocessing.encoding.processor import binary_encode
from backend.modules.data_preprocessing.feature_engineering.processor import (
    create_binned_feature,
    create_categorical_combination,
    create_datetime_feature,
    create_numeric_feature,
    drop_columns,
)
from backend.modules.data_preprocessing.missing_values.processor import (
    fill_missing_values_interpolation,
    fill_missing_values_knn,
    fill_missing_values_regression,
)
from backend.modules.data_preprocessing.outlier.processor import apply_outlier_method
from backend.modules.data_preprocessing.scaling.processor import apply_scaling_method


ACTIVE = "active"
REVERTED = "reverted"


def dataframe_memory_mb(df: pd.DataFrame) -> float:
    return int(df.memory_usage(index=True, deep=True).sum()) / (1024 * 1024)


def validate_dataframe_limits(df: pd.DataFrame) -> None:
    row_count = len(df)
    column_count = len(df.columns)
    memory_mb = dataframe_memory_mb(df)

    if row_count > settings.MAX_DATAFRAME_ROWS:
        raise HTTPException(status_code=413, detail="Dataset row limit exceeded.")
    if column_count > settings.MAX_DATAFRAME_COLUMNS:
        raise HTTPException(status_code=413, detail="Dataset column limit exceeded.")
    if memory_mb > settings.MAX_DATAFRAME_MEMORY_MB:
        raise HTTPException(status_code=413, detail="Dataset memory limit exceeded.")


def normalize_event_metadata(event: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(event.get("metadata") or {})
    metadata.setdefault("rollback_status", ACTIVE)
    metadata.setdefault("scope", infer_event_scope(event))
    metadata.setdefault("replayable", is_replayable_event(event))
    event["metadata"] = metadata
    event["rollback_status"] = metadata.get("rollback_status", ACTIVE)
    event["scope"] = metadata.get("scope") or {}
    event["replayable"] = bool(metadata.get("replayable"))
    event["reverted_by_event_id"] = metadata.get("reverted_by_event_id")
    event["rollback_reason"] = metadata.get("rollback_reason")
    return event


def is_event_active(event: dict[str, Any]) -> bool:
    metadata = event.get("metadata") or {}
    return metadata.get("rollback_status", event.get("rollback_status", ACTIVE)) == ACTIVE


def is_data_event(event: dict[str, Any]) -> bool:
    return event.get("category") in {"preprocessing", "editor"}


def is_replayable_event(event: dict[str, Any]) -> bool:
    if not is_data_event(event):
        return False

    if event.get("category") == "editor":
        payload = event.get("payload") or {}
        return event.get("action") == "manual_edit_commit" and any(
            isinstance(payload.get(key), list)
            for key in ("updated_cells", "cleared_cells", "deleted_row_ids", "trim_columns", "renamed_columns")
        )

    payload = event.get("payload") or {}
    step = event.get("step") or payload.get("step")
    action = event.get("action") or payload.get("action")

    return step in {"missing_values", "outliers", "encoding", "scaling", "feature_engineering"} and bool(action)


def infer_event_scope(event: dict[str, Any]) -> dict[str, Any]:
    payload = dict(event.get("payload") or {})
    metadata = dict(event.get("metadata") or {})
    category = event.get("category")
    step = event.get("step") or payload.get("step")
    action = event.get("action") or payload.get("action")

    scope: dict[str, Any] = {
        "columns": [],
        "rows": [],
        "created_columns": [],
        "removed_columns": [],
        "renamed_columns": [],
        "affects_row_order": False,
    }

    if category == "editor":
        renamed_columns = payload.get("renamed_columns") or metadata.get("renamed_column_names") or []
        trim_columns = payload.get("trim_columns") or metadata.get("trim_columns") or []
        updated_cells = payload.get("updated_cells") if isinstance(payload.get("updated_cells"), list) else []
        cleared_cells = payload.get("cleared_cells") if isinstance(payload.get("cleared_cells"), list) else []
        deleted_rows = payload.get("deleted_row_ids") or []

        columns = set(trim_columns)
        rows = set(deleted_rows)
        for cell in [*updated_cells, *cleared_cells]:
            if isinstance(cell, dict):
                if cell.get("column") is not None:
                    columns.add(str(cell["column"]))
                if cell.get("row_id") is not None:
                    rows.add(int(cell["row_id"]))

        for item in renamed_columns:
            if not isinstance(item, dict):
                continue
            old_name = item.get("column")
            new_name = item.get("new_name")
            if old_name is not None:
                columns.add(str(old_name))
            if new_name is not None:
                columns.add(str(new_name))
            scope["renamed_columns"].append({"column": old_name, "new_name": new_name})

        scope["columns"] = sorted(columns)
        scope["rows"] = sorted(rows)
        scope["affects_row_order"] = bool(deleted_rows)
        return scope

    if category != "preprocessing":
        return scope

    columns = set(_string_list(payload.get("columns")))
    columns.update(_string_list(payload.get("source_columns")))
    created_columns = set(_string_list(payload.get("new_columns")))
    removed_columns: set[str] = set()

    if action == "drop_columns":
        removed_columns.update(columns)
    if step == "missing_values" and action == "drop_columns":
        removed_columns.update(columns)
    if step == "encoding" and action in {"onehot", "binary"}:
        created_columns.update(_string_list(payload.get("new_columns")))
        if action == "onehot":
            removed_columns.update(columns)
    if step == "feature_engineering":
        created_columns.update(_string_list(payload.get("new_columns")))

    scope["columns"] = sorted(columns | created_columns | removed_columns)
    scope["created_columns"] = sorted(created_columns)
    scope["removed_columns"] = sorted(removed_columns)
    return scope


def build_rollback_plan(
    events: list[dict[str, Any]],
    event_id: str,
) -> dict[str, Any]:
    normalized_events = [normalize_event_metadata(dict(event)) for event in events]
    target_index = next((index for index, event in enumerate(normalized_events) if event.get("id") == event_id), -1)
    if target_index < 0:
        raise HTTPException(status_code=404, detail="Timeline event not found.")

    target = normalized_events[target_index]
    if not is_event_active(target):
        raise HTTPException(status_code=409, detail="Timeline event is already reverted.")
    if not is_data_event(target):
        raise HTTPException(status_code=409, detail="Timeline event cannot be selectively rolled back.")

    rollback_ids = {event_id}
    rollback_scope = _scope_resources(target.get("scope") or {})
    dependent_events: list[dict[str, Any]] = []
    preserved_events: list[dict[str, Any]] = []
    invalidated_model_events: list[dict[str, Any]] = []

    for event in normalized_events[target_index + 1:]:
        if not is_event_active(event):
            continue
        if event.get("category") == "model":
            invalidated_model_events.append(event)
            continue
        if not is_data_event(event):
            preserved_events.append(event)
            continue

        event_scope = _scope_resources(event.get("scope") or {})
        if _scopes_overlap(rollback_scope, event_scope):
            rollback_ids.add(str(event["id"]))
            dependent_events.append(event)
            rollback_scope = _merge_scope_resources(rollback_scope, event_scope)
        else:
            preserved_events.append(event)

    replay_events = [
        event
        for event in normalized_events
        if is_event_active(event)
        and is_data_event(event)
        and event.get("id") not in rollback_ids
    ]
    unsupported_replay_events = [
        event
        for event in replay_events
        if not bool((event.get("metadata") or {}).get("replayable", event.get("replayable")))
    ]

    return {
        "target_event": target,
        "dependent_events": dependent_events,
        "preserved_events": preserved_events,
        "invalidated_model_events": invalidated_model_events,
        "rollback_event_ids": sorted(rollback_ids),
        "unsupported_replay_events": unsupported_replay_events,
        "can_rollback": not unsupported_replay_events,
    }


def apply_selective_rollback(
    *,
    original_df: pd.DataFrame,
    events: list[dict[str, Any]],
    event_id: str,
    rollback_event_id: str,
) -> dict[str, Any]:
    plan = build_rollback_plan(events, event_id)
    if not plan["can_rollback"]:
        raise HTTPException(status_code=409, detail="Timeline contains legacy events that cannot be replayed.")

    rollback_ids = set(plan["rollback_event_ids"])
    invalidated_model_ids = {event["id"] for event in plan["invalidated_model_events"]}
    df = original_df.copy(deep=True)

    for event in events:
        normalized_event = normalize_event_metadata(dict(event))
        if not is_event_active(normalized_event):
            continue
        if normalized_event.get("id") in rollback_ids:
            continue
        if not is_data_event(normalized_event):
            continue
        df = replay_event(df, normalized_event)
        validate_dataframe_limits(df)

    marked_events: list[dict[str, Any]] = []
    for event in events:
        normalized_event = normalize_event_metadata(dict(event))
        metadata = dict(normalized_event.get("metadata") or {})
        if normalized_event.get("id") in rollback_ids:
            metadata["rollback_status"] = REVERTED
            metadata["reverted_by_event_id"] = rollback_event_id
            metadata["rollback_reason"] = "selective_rollback"
        elif normalized_event.get("id") in invalidated_model_ids:
            metadata["rollback_status"] = REVERTED
            metadata["reverted_by_event_id"] = rollback_event_id
            metadata["rollback_reason"] = "data_changed_by_selective_rollback"
        normalized_event["metadata"] = metadata
        marked_events.append(normalize_event_metadata(normalized_event))

    return {
        "data": df,
        "events": marked_events,
        "plan": plan,
    }


def replay_event(df: pd.DataFrame, event: dict[str, Any]) -> pd.DataFrame:
    category = event.get("category")
    payload = dict(event.get("payload") or {})

    if category == "editor":
        return _replay_editor_event(df, payload)
    if category == "preprocessing":
        return _replay_preprocessing_event(df, event, payload)

    return df


def _replay_editor_event(df: pd.DataFrame, payload: dict[str, Any]) -> pd.DataFrame:
    result = df.copy(deep=True).reset_index(drop=True)
    rename_map: dict[str, str] = {}

    for column in _string_list(payload.get("trim_columns")):
        if column in result.columns:
            result[column] = result[column].map(lambda value: value.strip() if isinstance(value, str) else value)

    for cell in payload.get("cleared_cells") or []:
        if not isinstance(cell, dict):
            continue
        row_id = int(cell.get("row_id", -1))
        column = str(cell.get("column"))
        if 0 <= row_id < len(result) and column in result.columns:
            result.at[row_id, column] = _empty_cell_value(result[column])

    for cell in payload.get("updated_cells") or []:
        if not isinstance(cell, dict):
            continue
        row_id = int(cell.get("row_id", -1))
        column = str(cell.get("column"))
        if 0 <= row_id < len(result) and column in result.columns:
            result.at[row_id, column] = cell.get("value")

    deleted_row_ids = sorted({int(row_id) for row_id in payload.get("deleted_row_ids") or []})
    valid_deleted_row_ids = [row_id for row_id in deleted_row_ids if 0 <= row_id < len(result)]
    if valid_deleted_row_ids:
        result = result.drop(index=valid_deleted_row_ids).reset_index(drop=True)

    for item in payload.get("renamed_columns") or []:
        if not isinstance(item, dict):
            continue
        old_name = str(item.get("column", ""))
        new_name = str(item.get("new_name", "")).strip()
        if old_name in result.columns and new_name:
            rename_map[old_name] = new_name
    if rename_map:
        result = result.rename(columns=rename_map)

    return result


def _replay_preprocessing_event(df: pd.DataFrame, event: dict[str, Any], payload: dict[str, Any]) -> pd.DataFrame:
    step = event.get("step") or payload.get("step")
    action = event.get("action") or payload.get("action")

    if step == "missing_values":
        return _replay_missing_values(df, action, payload)
    if step == "outliers":
        return _replay_outliers(df, action, payload)
    if step == "encoding":
        return _replay_encoding(df, action, payload)
    if step == "scaling":
        return _replay_scaling(df, action, payload)
    if step == "feature_engineering":
        return _replay_feature_engineering(df, action, payload)

    raise HTTPException(status_code=409, detail="Timeline event cannot be replayed.")


def _replay_missing_values(df: pd.DataFrame, action: str, payload: dict[str, Any]) -> pd.DataFrame:
    result = df.copy(deep=True)
    for column in _string_list(payload.get("columns")):
        if column not in result.columns:
            continue
        if action == "fill_mean" and np.issubdtype(result[column].dtype, np.number):
            result[column] = result[column].fillna(result[column].mean())
        elif action == "fill_median" and np.issubdtype(result[column].dtype, np.number):
            result[column] = result[column].fillna(result[column].median())
        elif action == "fill_mode":
            mode_value = result[column].mode()
            if len(mode_value) > 0:
                result[column] = result[column].fillna(mode_value.iloc[0])
        elif action == "fill_knn":
            result = fill_missing_values_knn(result, [column])
        elif action == "fill_interpolation":
            result = fill_missing_values_interpolation(result, [column], method="linear")
        elif action == "fill_regression":
            result = fill_missing_values_regression(result, [column])
        elif action == "fill_ffill":
            result[column] = result[column].ffill()
        elif action == "fill_bfill":
            result[column] = result[column].bfill()
        elif action == "drop_columns" and result[column].isnull().sum() > 0:
            result = result.drop(columns=[column])
        else:
            raise HTTPException(status_code=409, detail="Timeline event cannot be replayed.")
    return result


def _replay_outliers(df: pd.DataFrame, action: str, payload: dict[str, Any]) -> pd.DataFrame:
    columns = [column for column in _string_list(payload.get("columns")) if column in df.columns]
    if not columns:
        return df.copy(deep=True)

    kwargs: dict[str, Any] = {}
    threshold = payload.get("threshold")
    if action in {"iqr_cap", "iqr_winsorize"} and threshold is not None:
        kwargs["factor"] = threshold
    if action == "iqr_winsorize":
        kwargs["tail_percent"] = payload.get("winsorize_percent") or 5.0
    return apply_outlier_method(df.copy(deep=True), columns, method=action, **kwargs)


def _replay_encoding(df: pd.DataFrame, action: str, payload: dict[str, Any]) -> pd.DataFrame:
    result = df.copy(deep=True)
    for column in _string_list(payload.get("columns")):
        if column not in result.columns:
            continue
        if action == "label":
            result[column] = result[column].astype("category").cat.codes
        elif action == "onehot":
            drop_first = bool((payload.get("params") or {}).get("drop_first"))
            dummies = pd.get_dummies(result[column], prefix=column, drop_first=drop_first)
            result = pd.concat([result.drop(columns=[column]), dummies], axis=1)
        elif action == "ordinal":
            ordinal_mapping = (payload.get("params") or {}).get("ordinal_mapping")
            if ordinal_mapping:
                result[column] = result[column].map(ordinal_mapping)
            else:
                result[column] = result[column].astype("category").cat.codes
        elif action == "binary":
            result = binary_encode(result, [column])
        elif action == "frequency":
            freq_map = result[column].value_counts(normalize=True).to_dict()
            result[column] = result[column].map(freq_map)
        else:
            raise HTTPException(status_code=409, detail="Timeline event cannot be replayed.")
    return result


def _replay_scaling(df: pd.DataFrame, action: str, payload: dict[str, Any]) -> pd.DataFrame:
    method_map = {
        "standard": "standard_scaler",
        "minmax": "minmax_scaler",
        "robust": "robust_scaler",
        "maxabs": "maxabs_scaler",
        "normalizer": "normalizer",
    }
    method = method_map.get(str(action))
    if not method:
        raise HTTPException(status_code=409, detail="Timeline event cannot be replayed.")

    columns = [
        column
        for column in _string_list(payload.get("columns"))
        if column in df.columns and pd.api.types.is_numeric_dtype(df[column])
    ]
    if not columns:
        return df.copy(deep=True)

    kwargs: dict[str, Any] = {}
    feature_range = (payload.get("params") or {}).get("feature_range")
    if action == "minmax" and feature_range is not None:
        kwargs["feature_range"] = tuple(feature_range)
    return apply_scaling_method(df.copy(deep=True), columns, method, **kwargs)


def _replay_feature_engineering(df: pd.DataFrame, action: str, payload: dict[str, Any]) -> pd.DataFrame:
    result = df.copy(deep=True)
    columns = _string_list(payload.get("source_columns") or payload.get("columns"))
    params = dict(payload.get("params") or {})

    if action == "drop_columns":
        return drop_columns(result, [column for column in columns if column in result.columns])
    if action == "polynomial":
        for column in columns:
            if column in result.columns and np.issubdtype(result[column].dtype, np.number):
                result[f"{column}_squared"] = result[column] ** 2
        return result

    new_column_name = _first_string(payload.get("new_columns")) or payload.get("new_column_name")
    if not new_column_name:
        raise HTTPException(status_code=409, detail="Timeline event cannot be replayed.")

    if action == "create_numeric":
        numeric_operation = params.get("numericOperation")
        if numeric_operation == "custom":
            expression = str(payload.get("expression") or params.get("expression") or "")
            _validate_expression(expression, set(columns))
            safe_scope = {column: result[column] for column in columns if column in result.columns}
            result[str(new_column_name)] = eval(expression, {"__builtins__": {}}, safe_scope)
            return result
        return create_numeric_feature(result, str(numeric_operation), columns, str(new_column_name))
    if action == "binning":
        return create_binned_feature(
            result,
            columns[0],
            str(new_column_name),
            str(params.get("strategy", "equal_width")),
            int(params.get("binCount", 5)),
        )
    if action == "create_datetime":
        return create_datetime_feature(result, columns[0], str(params.get("datetimePart", "year")), str(new_column_name))
    if action == "create_categorical":
        return create_categorical_combination(result, columns, str(new_column_name), str(params.get("separator", "_")))

    raise HTTPException(status_code=409, detail="Timeline event cannot be replayed.")


def _scope_resources(scope: dict[str, Any]) -> dict[str, Any]:
    columns = set(_string_list(scope.get("columns")))
    columns.update(_string_list(scope.get("created_columns")))
    columns.update(_string_list(scope.get("removed_columns")))
    for item in scope.get("renamed_columns") or []:
        if isinstance(item, dict):
            if item.get("column") is not None:
                columns.add(str(item["column"]))
            if item.get("new_name") is not None:
                columns.add(str(item["new_name"]))
    return {
        "columns": columns,
        "rows": {int(row) for row in scope.get("rows") or []},
        "affects_row_order": bool(scope.get("affects_row_order")),
    }


def _scopes_overlap(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left["affects_row_order"] or right["affects_row_order"]:
        return True
    if left["columns"] and right["columns"] and left["columns"].intersection(right["columns"]):
        return True
    if left["rows"] and right["rows"] and left["rows"].intersection(right["rows"]):
        return True
    return False


def _merge_scope_resources(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "columns": set(left["columns"]) | set(right["columns"]),
        "rows": set(left["rows"]) | set(right["rows"]),
        "affects_row_order": bool(left["affects_row_order"] or right["affects_row_order"]),
    }


def _empty_cell_value(series: pd.Series) -> Any:
    if pd.api.types.is_datetime64_any_dtype(series.dtype):
        return pd.NaT
    if pd.api.types.is_numeric_dtype(series.dtype):
        return np.nan
    return pd.NA


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def _first_string(value: Any) -> str | None:
    if isinstance(value, list):
        for item in value:
            if item is not None:
                return str(item)
    return None


def _validate_expression(expression: str, allowed_columns: set[str]) -> None:
    if not expression:
        raise HTTPException(status_code=409, detail="Timeline event cannot be replayed.")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise HTTPException(status_code=409, detail="Timeline event cannot be replayed.") from exc

    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Name,
        ast.Load,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.Mod,
        ast.USub,
        ast.UAdd,
        ast.Constant,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise HTTPException(status_code=409, detail="Timeline event cannot be replayed.")
        if isinstance(node, ast.Name) and node.id not in allowed_columns:
            raise HTTPException(status_code=409, detail="Timeline event cannot be replayed.")
