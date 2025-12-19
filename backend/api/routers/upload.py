"""
Upload Router - File upload and data loading endpoints
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import Optional
import pandas as pd
import io
import os
import sys

# Add parent paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ..dependencies import session_manager, get_session_id, require_session

router = APIRouter()


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Depends(get_session_id)
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
            df = pd.read_excel(io.BytesIO(content))
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
        
        # Return summary
        return {
            "success": True,
            "session_id": session_id,
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sample/{dataset_name}")
async def load_sample_dataset(
    dataset_name: str,
    session_id: str = Depends(get_session_id)
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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate")
async def validate_upload(session_id: str = Depends(require_session)):
    """Validate uploaded data with LLM-enhanced suggestions"""
    df = session_manager.get_dataframe(session_id)
    if df is None:
        raise HTTPException(status_code=400, detail="No data loaded")
    
    try:
        # Import LLM enhancer
        from backend.modules.data_upload.llm_enhancer import enhance_validation_report_with_llm
        
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
                    "description": f"{col} sütununda %{missing_pct:.1f} eksik değer var",
                    "suggestion": "Ortalama, medyan veya mod ile doldurulabilir"
                })
                issue_id += 1
        
        # Check for duplicates
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            issues.append({
                "id": f"duplicates_{issue_id}",
                "type": "duplicate_rows",
                "severity": "info",
                "description": f"{dup_count} tekrarlayan satır tespit edildi",
                "suggestion": "Tekrarlayan satırları kaldırabilirsiniz"
            })
            issue_id += 1
        
        # Build data summary for LLM context
        data_summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object', 'category']).columns.tolist(),
            "missing_total": int(df.isnull().sum().sum()),
        }
        
        # Build initial validation report
        validation_report = {
            "is_valid": len([i for i in issues if i["severity"] == "critical"]) == 0,
            "issues": issues,
            "summary": data_summary
        }
        
        # Enhance with LLM suggestions
        enhanced_report = enhance_validation_report_with_llm(
            validation_report, 
            data_summary, 
            df
        )
        
        # Map backend keys to frontend expected keys
        for issue in enhanced_report.get("issues", []):
            if "llm_enhanced_suggestion" in issue:
                issue["llmSuggestion"] = issue.pop("llm_enhanced_suggestion")
            if "llm_priority" in issue:
                priority_map = {"yüksek": "high", "orta": "medium", "düşük": "low"}
                issue["priority"] = priority_map.get(issue.pop("llm_priority"), "medium")
        
        return enhanced_report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        return None


@router.delete("/reset")
async def reset_upload(session_id: str = Depends(get_session_id)):
    """Clear/reset the current session data"""
    try:
        # Clear the dataframe from session
        session_manager.delete_session(session_id)
        
        return {
            "success": True,
            "message": "Session data cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
