"""LLM enhancement functions for outlier handling step."""

import time
import json
import re
import logging
from typing import Dict, List, Optional

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
from backend.prompts.preprocessing_prompts import (
    PREPROCESSING_SYSTEM_PROMPT,
    get_preprocessing_suggestion_prompt
)

logger = logging.getLogger(__name__)

# Initialize Gemini if available
if GEMINI_AVAILABLE and LLM_ENABLED and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Gemini API key configuration failed: {e}")


def get_function_declaration():
    """Get Gemini function declaration for preprocessing suggestions."""
    return {
        "function_declarations": [
            {
                "name": "suggest_preprocessing_steps",
                "description": "Veri ön işleme adımları için öneriler üretir. Her sütun için ayrı öneri oluşturmalı.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "suggestions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "preprocessing_type": {
                                        "type": "string",
                                        "enum": ["missing_values", "encoding", "scaling", "outlier", "feature_engineering"],
                                        "description": "Ön işleme adımı tipi"
                                    },
                                    "method": {
                                        "type": "string",
                                        "description": "Kullanılacak yöntem (İngilizce teknik terim)"
                                    },
                                    "columns": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "İşlenecek sütun adları (her öneride SADECE 1 sütun olmalı)"
                                    },
                                    "reason": {
                                        "type": "string",
                                        "description": "Önerinin nedeni (SADECE düz Türkçe metin, HTML/Markdown YOK)"
                                    },
                                    "priority": {
                                        "type": "string",
                                        "enum": ["yüksek", "orta", "düşük"],
                                        "description": "Önerinin öncelik seviyesi"
                                    },
                                    "analysis_level": {
                                        "type": "string",
                                        "enum": ["Temel", "Orta", "Gelişmiş"],
                                        "description": "Analiz seviyesi"
                                    }
                                },
                                "required": ["preprocessing_type", "method", "columns", "reason", "priority", "analysis_level"]
                            },
                            "description": "Ön işleme önerileri listesi (her sütun için ayrı öneri)"
                        }
                    },
                    "required": ["suggestions"]
                }
            }
        ]
    }


def suggest_outlier_steps(
    data_summary: dict,
    numeric_columns: list,
    categorical_columns: list,
    analysis_level: str = 'Temel',
    detection_method: str = 'iqr'
) -> Dict:
    """
    Get LLM suggestions for outlier handling step.
    
    Args:
        data_summary: Data summary dictionary
        numeric_columns: List of numeric column names
        categorical_columns: List of categorical column names
        analysis_level: Analysis level ('Temel', 'Orta', 'Gelişmiş')
        detection_method: Detection method ('iqr', 'zscore')
        
    Returns:
        Dictionary with outlier handling suggestions
    """
    # Check LLM availability
    if not LLM_ENABLED:
        logger.debug("LLM_ENABLED is False - skipping enhancement")
        return {"suggestions": []}
    if not GEMINI_AVAILABLE:
        logger.error("google-generativeai package not available")
        return {"suggestions": []}
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is empty - check .env file")
        return {"suggestions": []}
    
    logger.info(f"🔧 Using GEMINI_MODEL: {GEMINI_MODEL}")
    logger.debug(f"Getting preprocessing suggestions for outlier, analysis_level: {analysis_level}")
    
    try:
        # Prepare prompt
        user_prompt = get_preprocessing_suggestion_prompt(
            data_summary,
            numeric_columns,
            categorical_columns,
            'outlier',
            analysis_level,
            detection_method
        )
        full_prompt = f"{PREPROCESSING_SYSTEM_PROMPT}\n\n{user_prompt}"
        
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
                    if function_call.name == "suggest_preprocessing_steps":
                        # Extract function arguments
                        args = function_call.args
                        suggestions = args.get("suggestions", [])
                        
                        logger.info(f"✅ Function call successful - {len(suggestions)} suggestions received")
                        return {"suggestions": suggestions}
                    else:
                        logger.warning(f"⚠️ Unknown function call: {function_call.name}")
                        return {"suggestions": []}
                else:
                    # Fallback: Try to extract text and parse JSON
                    logger.warning("⚠️ No function call detected, falling back to JSON parsing")
                    response_text = _extract_text_from_response(response)
                    parsed = _parse_json_response(response_text)
                    if parsed and "suggestions" in parsed:
                        logger.info(f"✅ JSON parsing successful - {len(parsed['suggestions'])} suggestions")
                        return parsed
                    else:
                        logger.warning("⚠️ Could not parse JSON from response")
                        return {"suggestions": []}
                
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ API call attempt {attempt + 1} failed: {e}")
                if attempt < LLM_MAX_RETRIES:
                    time.sleep(1)  # Wait before retry
                else:
                    logger.error(f"❌ All {LLM_MAX_RETRIES + 1} attempts failed")
        
        # If all retries failed
        if last_error:
            logger.error(f"❌ Failed to get preprocessing suggestions: {last_error}", exc_info=True)
        return {"suggestions": []}
        
    except Exception as e:
        logger.error(f"❌ Error getting preprocessing suggestions: {e}", exc_info=True)
        return {"suggestions": []}


def _extract_text_from_response(response) -> str:
    """Extract text from Gemini API response."""
    # Method 1: Try response.text (normal case)
    try:
        if hasattr(response, 'text'):
            text = response.text
            if text:
                logger.debug("Extracted text using response.text")
                return text.strip()
    except Exception as e:
        logger.debug(f"response.text failed: {e}")
    
    # Method 2: Try candidates[0].content.parts[0].text
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
    
    raise Exception("Could not extract text from response")


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
