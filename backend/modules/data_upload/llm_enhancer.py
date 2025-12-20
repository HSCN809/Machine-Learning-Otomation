"""LLM enhancement module for validation reports using Google Gemini."""

import time
import json
import re
import logging
from typing import Dict, List, Optional
import pandas as pd

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from backend.modules.config.settings import (
    LLM_ENABLED,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_TIMEOUT,
    LLM_MAX_RETRIES
)
from backend.prompts.validation_prompts import (
    VALIDATION_SYSTEM_PROMPT,
    get_validation_user_prompt
)

logger = logging.getLogger(__name__)

# Initialize Gemini if available
if GEMINI_AVAILABLE and LLM_ENABLED and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Gemini API key configuration failed: {e}")


def get_function_declaration():
    """Get Gemini function declaration for validation enhancement."""
    return {
        "function_declarations": [
            {
                "name": "enhance_validation_suggestion",
                "description": "Veri kalitesi sorunu için KISA öneri üretir. Maksimum 2-4 cümle.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "enhanced_suggestion": {
                            "type": "string",
                            "description": "KISACA öner: 2 çözüm + 2 etki cümlesi."
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["yüksek", "orta", "düşük"],
                            "description": "Öncelik seviyesi"
                        }
                    },
                    "required": ["enhanced_suggestion", "priority"]
                }
            }
        ]
    }


def get_column_statistics(df: pd.DataFrame, column: Optional[str]) -> Optional[Dict]:
    """Get statistics for a specific column."""
    if not column or column not in df.columns:
        return None
    
    col_data = df[column]
    stats = {
        "data_type": str(col_data.dtype),
        "total_values": len(col_data),
        "non_null_count": col_data.notna().sum(),
        "null_count": col_data.isna().sum(),
        "null_percentage": (col_data.isna().sum() / len(col_data)) * 100
    }
    
    # Numeric statistics
    if pd.api.types.is_numeric_dtype(col_data):
        stats.update({
            "mean": float(col_data.mean()) if col_data.notna().any() else None,
            "median": float(col_data.median()) if col_data.notna().any() else None,
            "std": float(col_data.std()) if col_data.notna().any() else None,
            "min": float(col_data.min()) if col_data.notna().any() else None,
            "max": float(col_data.max()) if col_data.notna().any() else None,
            "unique_count": int(col_data.nunique())
        })
    else:
        # Categorical statistics
        stats.update({
            "unique_count": int(col_data.nunique()),
            "most_frequent": str(col_data.mode().iloc[0]) if not col_data.mode().empty else None
        })
    
    return stats


def _extract_text_from_response(response) -> str:
    """Extract text from Gemini API response - handles MAX_TOKENS case."""
    # Check finish_reason first
    finish_reason = None
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        finish_reason = getattr(candidate, 'finish_reason', None)
        logger.debug(f"Finish reason: {finish_reason}")
        
        # If MAX_TOKENS and parts is empty, response is cut off
        if finish_reason == 2:  # MAX_TOKENS
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts'):
                    parts = candidate.content.parts
                    if not parts or len(parts) == 0:
                        raise Exception(
                            f"Response hit max tokens limit ({LLM_MAX_TOKENS}). "
                            f"Response was cut off before any text was generated. "
                            f"Please increase LLM_MAX_TOKENS in .env file or reduce prompt size."
                        )
    
    # Method 1: Try response.parts (direct access)
    try:
        if hasattr(response, 'parts') and response.parts:
            for part in response.parts:
                if hasattr(part, 'text') and part.text:
                    logger.debug("Extracted text using response.parts")
                    return part.text.strip()
    except Exception as e:
        logger.debug(f"response.parts failed: {e}")
    
    # Method 2: Try response.text (normal case)
    try:
        if hasattr(response, 'text'):
            text = response.text
            if text:
                logger.debug("Extracted text using response.text")
                return text.strip()
    except Exception as e:
        logger.debug(f"response.text failed: {e}")
    
    # Method 3: Try candidates[0].content.parts[0].text
    try:
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    for i, part in enumerate(candidate.content.parts):
                        if hasattr(part, 'text') and part.text:
                            logger.debug(f"Extracted text using candidates[0].content.parts[{i}].text")
                            return part.text.strip()
    except Exception as e:
        logger.debug(f"candidates[0].content.parts failed: {e}")
    
    # Method 4: Try candidates[0].content.text (if exists)
    try:
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'text'):
                    text = candidate.content.text
                    if text:
                        logger.debug("Extracted text using candidates[0].content.text")
                        return text.strip()
    except Exception as e:
        logger.debug(f"candidates[0].content.text failed: {e}")
    
    # If all methods fail
    error_msg = "Could not extract text from response"
    if finish_reason == 2:
        error_msg += f" - MAX_TOKENS limit reached ({LLM_MAX_TOKENS}). Increase LLM_MAX_TOKENS in .env"
    
    raise Exception(error_msg)


def _parse_json_response(response_text: str) -> Optional[Dict]:
    """Parse JSON from LLM response."""
    # Try direct JSON parse
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON object in response
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    return None


def enhance_issue_with_llm(
    issue: Dict,
    data_summary: Dict,
    df: Optional[pd.DataFrame] = None
) -> Optional[Dict]:
    """
    Enhance a single validation issue using LLM.
    
    Args:
        issue: Issue dictionary
        data_summary: Data summary dictionary
        df: Optional DataFrame for column statistics
        
    Returns:
        Enhanced issue dictionary with llm_enhanced fields, or None if failed
    """
    # Check LLM availability
    if not LLM_ENABLED:
        logger.debug("LLM_ENABLED is False - skipping enhancement")
        return None
    if not GEMINI_AVAILABLE:
        logger.error("google-generativeai package not available")
        return None
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is empty - check .env file")
        return None
    
    logger.debug(f"Enhancing issue: {issue.get('type', 'unknown')}")
    logger.info(f"🔧 Using GEMINI_MODEL: {GEMINI_MODEL}")  # INFO level so it's always visible
    
    try:
        # Get column statistics if needed
        column_stats = None
        if df is not None and issue.get('column'):
            column_stats = get_column_statistics(df, issue['column'])
        
        # Prepare prompt
        user_prompt = get_validation_user_prompt(issue, data_summary, column_stats)
        full_prompt = f"{VALIDATION_SYSTEM_PROMPT}\n\n{user_prompt}"
        
        # Initialize model with function calling
        logger.debug(f"Initializing model with name: {GEMINI_MODEL}")
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": LLM_TEMPERATURE,
            },
            tools=[get_function_declaration()]
        )
        
        # Make API call with retry
        last_error = None
        for attempt in range(LLM_MAX_RETRIES + 1):
            try:
                logger.debug(f"API call attempt {attempt + 1}/{LLM_MAX_RETRIES + 1}")
                
                # Make API call with function calling
                response = model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": LLM_TEMPERATURE,
                    }
                )
                
                # Check for function call in response
                function_call = None
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'function_call'):
                                    function_call = part.function_call
                                    logger.info("✅ Function call detected in response")
                                    break
                
                # If function call exists, extract structured data
                if function_call:
                    if function_call.name == "enhance_validation_suggestion":
                        # Extract function arguments
                        args = function_call.args
                        
                        enhanced_suggestion = args.get("enhanced_suggestion", "")
                        priority = args.get("priority", "orta")
                        
                        # Validate and set defaults
                        if not enhanced_suggestion or not enhanced_suggestion.strip():
                            logger.warning("⚠️ enhanced_suggestion is empty from function call")
                            enhanced_suggestion = "Öneri oluşturulamadı."
                        if priority not in ["yüksek", "orta", "düşük"]:
                            logger.warning(f"⚠️ Invalid priority '{priority}', defaulting to 'orta'")
                            priority = "orta"
                        
                        # impact_analysis artık enhanced_suggestion içinde
                        impact_analysis = ""  # Artık kullanılmıyor
                        
                        logger.info(f"✅ Function call successful - enhanced_suggestion: {len(enhanced_suggestion)} chars, priority: {priority}")
                    else:
                        logger.warning(f"⚠️ Unknown function call: {function_call.name}")
                        enhanced_suggestion = "Bilinmeyen fonksiyon çağrısı."
                        impact_analysis = ""
                        priority = "orta"
                else:
                    # Fallback: Try to extract text and parse JSON (for backward compatibility)
                    logger.warning("⚠️ No function call detected, falling back to JSON parsing")
                    try:
                        response_text = response.text.strip()
                    except:
                        if hasattr(response, 'candidates') and response.candidates:
                            candidate = response.candidates[0]
                            if hasattr(candidate, 'content') and candidate.content:
                                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                    response_text = candidate.content.parts[0].text.strip()
                                else:
                                    response_text = str(response)
                            else:
                                response_text = str(response)
                        else:
                            response_text = str(response)
                    
                    # Try JSON parse as fallback
                    result = None
                    try:
                        if response_text.strip().startswith('{'):
                            result = json.loads(response_text)
                            logger.info("✅ Fallback JSON parse successful")
                    except json.JSONDecodeError:
                        pass
                    
                    if result:
                        enhanced_suggestion = result.get("enhanced_suggestion", response_text)
                        priority = result.get("priority", "orta")
                    else:
                        enhanced_suggestion = response_text
                        priority = "orta"
                
                # Create enhanced issue
                enhanced_issue = issue.copy()
                enhanced_issue["llm_enhanced_suggestion"] = enhanced_suggestion
                enhanced_issue["llm_priority"] = priority
                # impact_analysis artık kullanılmıyor - enhanced_suggestion içinde
                
                logger.info(f"✅ LLM enhancement successful - llm_impact_analysis set: {bool(enhanced_issue.get('llm_impact_analysis'))}, llm_priority: {enhanced_issue.get('llm_priority')}")
                return enhanced_issue
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                logger.warning(f"API call failed (attempt {attempt + 1}): {error_msg}")
                
                if attempt < LLM_MAX_RETRIES:
                    wait_time = 2 ** attempt
                    logger.debug(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        # All retries failed
        logger.error(f"All retry attempts failed: {last_error}")
        return None
        
    except Exception as e:
        logger.error(f"LLM enhancement failed: {e}")
        return None


def enhance_validation_report_with_llm(
    validation_report: Dict,
    data_summary: Dict,
    df: Optional[pd.DataFrame] = None
) -> Dict:
    """
    Enhance all issues in validation report with LLM suggestions.
    
    Args:
        validation_report: Validation report dictionary
        data_summary: Data summary dictionary
        df: Optional DataFrame for column statistics
        
    Returns:
        Enhanced validation report
    """
    # Check LLM availability
    if not LLM_ENABLED or not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        logger.debug("LLM not available, returning original report")
        return validation_report
    
    issues = validation_report.get('issues', [])
    logger.info(f"Enhancing {len(issues)} issues with LLM")
    
    enhanced_issues = []
    for issue in issues:
        enhanced_issue = enhance_issue_with_llm(issue, data_summary, df)
        
        if enhanced_issue:
            enhanced_issues.append(enhanced_issue)
        else:
            # Keep original issue if enhancement failed
            enhanced_issues.append(issue)
    
    # Update report
    enhanced_report = validation_report.copy()
    enhanced_report['issues'] = enhanced_issues
    
    # Re-categorize by severity
    enhanced_report['issues_by_severity'] = {
        'kritik': [i for i in enhanced_issues if i['severity'] == 'kritik'],
        'uyarı': [i for i in enhanced_issues if i['severity'] == 'uyarı'],
        'bilgi': [i for i in enhanced_issues if i['severity'] == 'bilgi']
    }
    
    return enhanced_report
