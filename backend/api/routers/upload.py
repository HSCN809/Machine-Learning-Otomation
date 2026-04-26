"""
Upload Router - File upload and data loading endpoints
"""

from datetime import date, datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Any, Optional
import logging
import pandas as pd
import numpy as np
import io
import os
import sys
import math

# Add parent paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ..dependencies import (
    delete_persisted_session,
    get_db,
    get_session_id,
    persist_session,
    require_authenticated_user,
    require_session,
    restore_persisted_session,
    session_manager,
)
from backend.modules.auth.models import User
from backend.modules.data_upload.persistence import DataSessionRepository

router = APIRouter()
logger = logging.getLogger(__name__)


class EditorCellUpdate(BaseModel):
    row_id: int
    column: str
    value: Any = None


class EditorCellRef(BaseModel):
    row_id: int
    column: str


class EditorColumnRename(BaseModel):
    column: str
    new_name: str


class EditorCommitRequest(BaseModel):
    updated_cells: list[EditorCellUpdate] = Field(default_factory=list)
    cleared_cells: list[EditorCellRef] = Field(default_factory=list)
    deleted_row_ids: list[int] = Field(default_factory=list)
    trim_columns: list[str] = Field(default_factory=list)
    renamed_columns: list[EditorColumnRename] = Field(default_factory=list)


class SavedDatasetRenameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=512)


def _serialize_editor_value(value: Any) -> Any:
    if pd.isna(value):
        return ""
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    return value


def _empty_cell_value(series: pd.Series) -> Any:
    if pd.api.types.is_datetime64_any_dtype(series.dtype):
        return pd.NaT
    if pd.api.types.is_numeric_dtype(series.dtype):
        return np.nan
    return pd.NA


def _get_editor_dataframe(session_id: str) -> pd.DataFrame:
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    return df.reset_index(drop=True).copy(deep=True)


def _clear_downstream_metadata(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        return

    for key in (
        "training_target_column",
        "problem_type",
        "training_results",
        "active_training_job_id",
        "trained_model_artifacts",
    ):
        session["metadata"].pop(key, None)


def _clear_downstream_timeline(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        return

    preserved_events = [
        event
        for event in session.get("timeline_events", [])
        if event.get("category") not in {"preprocessing", "model"}
    ]
    preserved_event_ids = {event.get("id") for event in preserved_events}
    session["timeline_events"] = preserved_events
    session["timeline_snapshots"] = [
        snapshot
        for snapshot in session.get("timeline_snapshots", [])
        if snapshot.get("event_id") in preserved_event_ids
    ]
    session["history"] = []
    session["history_snapshots"] = []


def _serialize_saved_dataset(record) -> dict[str, Any]:
    metadata = record.metadata_json or {}
    name = metadata.get("filename") or record.filename or "Adsiz veri seti"
    return {
        "id": record.id,
        "name": str(name),
        "rows": record.row_count,
        "columns": record.column_count,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
    }


def _append_timeline_event(
    session_id: str,
    *,
    category: str,
    action: str,
    title: str,
    description: str,
    undoable: bool,
    metadata: Optional[dict[str, Any]] = None,
    payload: Optional[dict[str, Any]] = None,
    snapshot_df: Optional[pd.DataFrame] = None,
) -> dict[str, Any]:
    event = session_manager.add_timeline_event(
        session_id,
        {
            "category": category,
            "action": action,
            "title": title,
            "description": description,
            "undoable": undoable,
            "metadata": metadata or {},
            "payload": payload or {},
        },
    )

    if undoable and snapshot_df is not None:
        session_manager.add_timeline_snapshot(session_id, event["id"], snapshot_df)

    return event


def _read_excel_content(content: bytes, filename: str) -> pd.DataFrame:
    lower_filename = filename.lower()
    engine = "xlrd" if lower_filename.endswith(".xls") else "openpyxl"
    return pd.read_excel(io.BytesIO(content), engine=engine)


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
):
    """Upload a file (CSV, Excel, JSON)"""
    try:
        # Read file content
        content = await file.read()
        
        # Determine file type and load
        filename = file.filename.lower()
        
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif filename.endswith(('.xls', '.xlsx')):
            df = _read_excel_content(content, filename)
        elif filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(content))
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Use CSV, Excel, or JSON."
            )
        
        # Store in session
        session_manager.set_dataframe(session_id, df, is_original=True)
        session_manager.set_metadata(session_id, "filename", file.filename)
        _append_timeline_event(
            session_id,
            category="upload",
            action="file_uploaded",
            title="Dosya yüklendi",
            description=f"{file.filename} veri seti oturuma yüklendi.",
            undoable=False,
            metadata={
                "filename": file.filename,
                "rows": len(df),
                "columns": len(df.columns),
            },
        )
        persist_session(session_id, db)
        
        # Return summary
        return {
            "success": True,
            "session_id": session_id,
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("File upload failed for session %s", session_id)
        raise HTTPException(status_code=500, detail="Dosya yüklenirken hata oluştu") from e


@router.post("/sample/{dataset_name}")
async def load_sample_dataset(
    dataset_name: str,
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
):
    """Load a sample dataset"""
    try:
        # Generate sample data
        df = _generate_sample_data(dataset_name)
        
        if df is None:
            raise HTTPException(
                status_code=404,
                detail=f"Dataset not found. Available: tips, iris, titanic"
            )
        
        # Store in session
        session_manager.set_dataframe(session_id, df, is_original=True)
        session_manager.set_metadata(session_id, "filename", dataset_name)
        _append_timeline_event(
            session_id,
            category="upload",
            action="sample_loaded",
            title="Örnek veri seti yüklendi",
            description=f"{dataset_name} örnek veri seti oturuma yüklendi.",
            undoable=False,
            metadata={
                "dataset": dataset_name,
                "rows": len(df),
                "columns": len(df.columns),
            },
        )
        persist_session(session_id, db)
        
        return {
            "success": True,
            "session_id": session_id,
            "dataset": dataset_name,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Sample dataset load failed for session %s: %s", session_id, dataset_name)
        raise HTTPException(status_code=500, detail="Örnek veri seti yüklenirken hata oluştu") from e


@router.get("/saved-datasets")
async def list_saved_datasets(
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    """List persisted datasets for the authenticated user."""
    repository = DataSessionRepository(db)
    records = repository.list_sessions(current_user.id)
    return {
        "datasets": [_serialize_saved_dataset(record) for record in records],
    }


@router.post("/saved-datasets/{dataset_session_id}/load")
async def load_saved_dataset(
    dataset_session_id: str,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    """Restore a persisted dataset and mark it as the active session."""
    repository = DataSessionRepository(db)
    record = repository.get_session(dataset_session_id, current_user.id)
    if record is None:
        raise HTTPException(status_code=404, detail="Kayitli veri seti bulunamadi")

    if not session_manager.owns_session(dataset_session_id, current_user.id):
        restored = restore_persisted_session(dataset_session_id, current_user.id, db)
        if not restored:
            raise HTTPException(status_code=404, detail="Kayitli veri seti bulunamadi")

    df = session_manager.get_dataframe(dataset_session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="Kayitli veri seti yuklenemedi")

    _append_timeline_event(
        dataset_session_id,
        category="upload",
        action="saved_dataset_loaded",
        title="Kayitli veri seti yüklendi",
        description=f"{record.filename or 'Veri seti'} aktif oturuma geri yüklendi.",
        undoable=False,
        metadata={
            "dataset_session_id": record.id,
            "filename": record.filename,
            "rows": record.row_count,
            "columns": record.column_count,
        },
    )
    persist_session(dataset_session_id, db)

    return {
        "success": True,
        "session_id": record.id,
        "filename": record.filename,
        "rows": record.row_count,
        "columns": record.column_count,
        "column_names": df.columns.tolist(),
    }


@router.patch("/saved-datasets/{dataset_session_id}")
async def rename_saved_dataset(
    dataset_session_id: str,
    request: SavedDatasetRenameRequest,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    """Rename a persisted dataset."""
    next_name = request.name.strip()
    if not next_name:
        raise HTTPException(status_code=400, detail="Veri seti adi bos birakilamaz")

    repository = DataSessionRepository(db)
    record = repository.rename_session(dataset_session_id, current_user.id, next_name)
    if record is None:
        raise HTTPException(status_code=404, detail="Kayitli veri seti bulunamadi")

    memory_session = session_manager.get_session(dataset_session_id)
    if memory_session and memory_session.get("owner_user_id") == current_user.id:
        memory_session.setdefault("metadata", {})["filename"] = next_name

    db.commit()
    return {
        "success": True,
        "dataset": _serialize_saved_dataset(record),
    }


@router.delete("/saved-datasets/{dataset_session_id}")
async def delete_saved_dataset(
    dataset_session_id: str,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    """Delete a persisted dataset and its related records."""
    repository = DataSessionRepository(db)
    record = repository.get_session(dataset_session_id, current_user.id)
    if record is None:
        raise HTTPException(status_code=404, detail="Kayitli veri seti bulunamadi")

    repository.delete_session(dataset_session_id, current_user.id)
    db.commit()
    session_manager.delete_session(dataset_session_id)

    logger.info(
        "Persisted dataset deleted for user %s: dataset_session_id=%s",
        current_user.id,
        dataset_session_id,
    )
    return {
        "success": True,
        "message": "Kayitli veri seti silindi",
    }


@router.get("/summary")
async def get_summary(session_id: str = Depends(require_session)):
    """Get data summary"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "memory_usage": int(df.memory_usage(deep=True).sum()),
            "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object', 'category']).columns.tolist(),
            "missing_total": int(df.isnull().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "column_info": [
                {
                    "name": col,
                    "dtype": str(df[col].dtype),
                    "missing_count": int(df[col].isnull().sum()),
                    "missing_percentage": round(df[col].isnull().sum() / len(df) * 100, 2),
                    "unique_count": int(df[col].nunique()),
                }
                for col in df.columns
            ],
        }
    except Exception as e:
        logger.exception("Data summary failed for session %s", session_id)
        raise HTTPException(status_code=500, detail="Veri özeti oluşturulurken hata oluştu") from e


@router.get("/validate")
async def validate_upload(session_id: str = Depends(require_session)):
    """Validate uploaded data (without LLM - basic validation only)"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        # Build detailed issues list
        issues = []
        issue_id = 0
        
        # Check for missing values - per column
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count > 0:
                missing_pct = (missing_count / len(df)) * 100
                issues.append({
                    "id": f"missing_{issue_id}",
                    "type": "missing_values",
                    "severity": "warning",
                    "column": col,
                    "description": f"{col} sütununda %{missing_pct:.1f} eksik değer var"
                })
                issue_id += 1
        
        # Check for duplicates
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            issues.append({
                "id": f"duplicates_{issue_id}",
                "type": "duplicate_rows",
                "severity": "info",
                "description": f"{dup_count} tekrarlayan satır tespit edildi"
            })
            issue_id += 1
        
        # Build data summary
        data_summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "missing_total": int(df.isnull().sum().sum()),
        }
        
        # Return validation report WITHOUT LLM enhancements
        return {
            "is_valid": len([i for i in issues if i["severity"] == "critical"]) == 0,
            "issues": issues,
            "summary": data_summary
        }
    except Exception as e:
        logger.exception("Upload validation failed for session %s", session_id)
        raise HTTPException(status_code=500, detail="Veri doğrulaması sırasında hata oluştu") from e


@router.get("/preview")
async def get_preview(
    rows: int = 10,
    session_id: str = Depends(require_session)
):
    """Get data preview (first N rows)"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    preview_df = df.head(rows)
    
    return {
        "columns": preview_df.columns.tolist(),
        "data": preview_df.fillna("").to_dict(orient="records"),
        "total_rows": len(df),
    }


@router.get("/editor-preview")
async def get_editor_preview(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    session_id: str = Depends(require_session)
):
    """Get paginated rows for the manual data editor."""
    df = _get_editor_dataframe(session_id)

    total_rows = len(df)
    total_pages = max(1, math.ceil(total_rows / page_size)) if page_size > 0 else 1
    current_page = min(page, total_pages)
    start = (current_page - 1) * page_size
    end = start + page_size

    rows = []
    for row_id, (_, row) in enumerate(df.iloc[start:end].iterrows(), start=start):
        rows.append({
            "row_id": row_id,
            "values": {
                column: _serialize_editor_value(value)
                for column, value in row.items()
            },
        })

    return {
        "page": current_page,
        "page_size": page_size,
        "total_rows": total_rows,
        "total_pages": total_pages,
        "columns": df.columns.tolist(),
        "rows": rows,
    }


@router.post("/editor/commit")
async def commit_editor_changes(
    request: EditorCommitRequest,
    session_id: str = Depends(require_session),
    db: Session = Depends(get_db),
):
    """Apply manual editor changes to the session dataframe."""
    df = _get_editor_dataframe(session_id)
    previous_df = df.copy(deep=True)

    valid_columns = set(df.columns)
    max_row_id = len(df) - 1

    def ensure_valid_row(row_id: int):
        if row_id < 0 or row_id > max_row_id:
            raise HTTPException(status_code=400, detail=f"Invalid row id: {row_id}")

    def ensure_valid_column(column: str):
        if column not in valid_columns:
            raise HTTPException(status_code=400, detail=f"Invalid column: {column}")

    for column in request.trim_columns:
        ensure_valid_column(column)

    for cell in request.cleared_cells:
        ensure_valid_row(cell.row_id)
        ensure_valid_column(cell.column)

    for cell in request.updated_cells:
        ensure_valid_row(cell.row_id)
        ensure_valid_column(cell.column)

    rename_map: dict[str, str] = {}
    for item in request.renamed_columns:
        ensure_valid_column(item.column)
        next_name = item.new_name.strip()
        if not next_name:
            raise HTTPException(status_code=400, detail="Column names cannot be empty")
        rename_map[item.column] = next_name

    deleted_row_ids = sorted(set(request.deleted_row_ids))
    for row_id in deleted_row_ids:
        ensure_valid_row(row_id)

    final_column_names = [rename_map.get(column, column) for column in df.columns]
    if len(set(final_column_names)) != len(final_column_names):
        raise HTTPException(status_code=400, detail="Column names must be unique")

    for column in request.trim_columns:
        df[column] = df[column].map(lambda value: value.strip() if isinstance(value, str) else value)

    for cell in request.cleared_cells:
        df.at[cell.row_id, cell.column] = _empty_cell_value(df[cell.column])

    for cell in request.updated_cells:
        df.at[cell.row_id, cell.column] = cell.value

    if deleted_row_ids:
        df = df.drop(index=deleted_row_ids).reset_index(drop=True)

    if rename_map:
        df = df.rename(columns=rename_map)

    session_manager.set_dataframe(session_id, df)
    session = session_manager.get_session(session_id)
    if session:
        session["original_data"] = df.copy(deep=True)

    _clear_downstream_timeline(session_id)
    _append_timeline_event(
        session_id,
        category="editor",
        action="manual_edit_commit",
        title="Veri düzenleme kaydedildi",
        description="Manuel veri düzenleme değişiklikleri veri setine uygulandı.",
        undoable=True,
        metadata={
            "updated_cells": len(request.updated_cells),
            "cleared_cells": len(request.cleared_cells),
            "deleted_rows": len(deleted_row_ids),
            "trimmed_columns": len(request.trim_columns),
            "renamed_columns": len(request.renamed_columns),
            "trim_columns": request.trim_columns,
            "renamed_column_names": [
                {"column": item.column, "new_name": item.new_name}
                for item in request.renamed_columns
            ],
        },
        snapshot_df=previous_df,
    )
    _clear_downstream_metadata(session_id)

    editor_commits = session_manager.get_metadata(session_id, "editor_commits") or []
    editor_commits.append({
        "action": "manual_edit_commit",
        "updated_cells": len(request.updated_cells),
        "cleared_cells": len(request.cleared_cells),
        "deleted_rows": len(deleted_row_ids),
        "trim_columns": request.trim_columns,
        "renamed_columns": request.renamed_columns,
    })
    session_manager.set_metadata(session_id, "editor_commits", editor_commits)
    persist_session(session_id, db)
    logger.info(
        "Manual editor commit applied for session %s: updated=%s cleared=%s deleted=%s trimmed=%s renamed=%s",
        session_id,
        len(request.updated_cells),
        len(request.cleared_cells),
        len(deleted_row_ids),
        len(request.trim_columns),
        len(request.renamed_columns),
    )

    return {
        "success": True,
        "rows": len(df),
        "columns": len(df.columns),
        "updated_cells": len(request.updated_cells),
        "cleared_cells": len(request.cleared_cells),
        "deleted_rows": len(deleted_row_ids),
        "trimmed_columns": len(request.trim_columns),
        "renamed_columns": len(request.renamed_columns),
    }


def _generate_sample_data(dataset_name: str) -> Optional[pd.DataFrame]:
    """Load real sample datasets from files"""
    
    # Dataset mapping
    datasets = {
        "iris": "IRIS.csv",
        "titanic": "Titanic-Dataset.csv",
        "diamonds": "diamonds.csv",
        "planets": "planets.csv",
    }
    
    if dataset_name.lower() not in datasets:
        return None
    
    # Get the sample datasets directory
    sample_dir = os.path.join(
        os.path.dirname(__file__), 
        '..', '..', 'modules', 'data_upload', 'sample_datasets'
    )
    
    filepath = os.path.join(sample_dir, datasets[dataset_name.lower()])
    
    if not os.path.exists(filepath):
        return None
    
    try:
        df = pd.read_csv(filepath)
        return df
    except Exception:
        logger.exception("Sample dataset file could not be read: %s", filepath)
        return None


@router.delete("/reset")
async def reset_upload(
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
):
    """Clear/reset the current session data"""
    try:
        # Clear the dataframe from session
        memory_session = session_manager.get_session(session_id)
        owner_user_id = memory_session.get("owner_user_id") if memory_session else None
        if owner_user_id:
            delete_persisted_session(session_id, owner_user_id, db)
        session_manager.delete_session(session_id)
        
        return {
            "success": True,
            "message": "Session data cleared successfully"
        }
    except Exception as e:
        logger.exception("Upload reset failed for session %s", session_id)
        raise HTTPException(status_code=500, detail="Oturum verisi temizlenirken hata oluştu") from e
