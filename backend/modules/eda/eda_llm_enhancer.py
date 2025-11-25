"""LLM enhancement module for EDA using Google Gemini."""

import time
import json
import re
import logging
import html as html_module
from typing import Dict, List, Optional, Any
import pandas as pd


def clean_html_from_text(text: str) -> str:
    """
    Radikal HTML temizleme fonksiyonu.
    Tüm HTML tag'lerini, entity'leri ve formatlamayı kaldırır.
    """
    if not text:
        return ''
    
    # Önce HTML entity'leri decode et (Python'un html modülü ile)
    try:
        # HTML entity'leri decode et (ama tag'leri koruma)
        text = html_module.unescape(text)
    except:
        # Fallback: Manuel decode
        text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
        text = text.replace('&apos;', "'").replace('&mdash;', '—').replace('&ndash;', '–')
    
    # Tüm HTML tag'lerini kaldır (önce özel tag'ler, sonra genel)
    # Önce açılış tag'lerini (attribute'larıyla birlikte) kaldır
    text = re.sub(r'<[^>]+>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Kapanış tag'leri de kaldır (eğer kaldıysa)
    text = re.sub(r'</[^>]+>', '', text, flags=re.IGNORECASE)
    
    # Self-closing tag'leri kaldır
    text = re.sub(r'<[^>]+/>', '', text, flags=re.IGNORECASE)
    
    # Tekrar entity decode (eğer tag'ler içinde entity varsa)
    try:
        text = html_module.unescape(text)
    except:
        pass
    
    # Fazla boşlukları, newline'ları ve tab'ları temizle
    text = ' '.join(text.split())
    
    # Trim ve son kontrol
    text = text.strip()
    
    # Son bir kontrol: Eğer hala HTML tag'leri varsa (nested veya eksik kapanış)
    if '<' in text or '>' in text:
        # Tüm < ve > karakterlerini kontrol et
        # Eğer tag benzeri bir yapı varsa, sadece içeriği al
        text = re.sub(r'<[^>]*', '', text)  # Açılış tag'leri
        text = re.sub(r'[^<]*>', '', text)  # Kapanış tag'leri
        text = ' '.join(text.split()).strip()
    
    return text

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
    LLM_TIMEOUT,
    LLM_MAX_RETRIES
)
from backend.prompts.eda_prompts import (
    EDA_SYSTEM_PROMPT,
    get_visualization_suggestion_prompt,
    get_analysis_interpretation_prompt,
    get_next_steps_prompt
)

logger = logging.getLogger(__name__)

# Initialize Gemini if available
if GEMINI_AVAILABLE and LLM_ENABLED and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Gemini API key configuration failed: {e}")


def get_function_declaration():
    """
    EDA modülü için Gemini function declaration.
    data_upload modülündeki çalışan formatı referans alarak oluşturuldu.
    """
    return {
        "function_declarations": [
            {
                "name": "suggest_visualizations",
                "description": "Veri seti için görselleştirme önerileri sun. En az 8 öneri ver.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "suggestions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "visualization_type": {
                                        "type": "string",
                                        "description": "Görselleştirme tipi"
                                    },
                                    "column": {
                                        "type": "string",
                                        "description": "İlgili sütun adı (opsiyonel - bazı görselleştirmeler için sütun gerekmez, örn: Correlation Matrix)"
                                    },
                                    "reason": {
                                        "type": "string",
                                        "description": "Bu görselleştirmenin neden önerildiği"
                                    },
                                    "analysis_level": {
                                        "type": "string",
                                        "description": "Bu önerinin analiz seviyesi (Temel, Orta). Gelişmiş seviye önerileri VERME.",
                                        "enum": ["Temel", "Orta"]
                                    }
                                },
                                "required": ["visualization_type", "reason", "analysis_level"]
                            }
                        }
                    },
                    "required": ["suggestions"]
                }
            }
        ]
    }


def suggest_visualizations(
    data_summary: dict,
    numeric_columns: list,
    categorical_columns: list,
    analysis_level: str = 'Temel'
) -> Dict:
    """
    Get LLM suggestions for visualizations.
    
    Args:
        data_summary: Data summary dictionary
        numeric_columns: List of numeric column names
        categorical_columns: List of categorical column names
        analysis_level: Analysis level ('Temel', 'Orta')
        
    Returns:
        Dictionary with visualization suggestions
    """
    if not LLM_ENABLED or not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return {
            'suggestions': [],
            'error': 'LLM is not enabled or not available'
        }
    
    logger.info(f"🔧 Using GEMINI_MODEL: {GEMINI_MODEL}")
    logger.debug(f"Getting visualization suggestions, analysis_level: {analysis_level}")
    
    try:
        # Prepare prompt - ensure analysis_level is not "Gelişmiş"
        safe_analysis_level = analysis_level if analysis_level != 'Gelişmiş' else 'Orta'
        user_prompt = get_visualization_suggestion_prompt(
            data_summary,
            numeric_columns,
            categorical_columns,
            safe_analysis_level
        )
        full_prompt = f"{EDA_SYSTEM_PROMPT}\n\n{user_prompt}"
        logger.debug(f"Prompt length: {len(full_prompt)} characters")
        logger.info(f"📊 Requesting visualizations for {len(numeric_columns)} numeric and {len(categorical_columns)} categorical columns")
        
        # Initialize model with function calling (veri ön işleme modülündeki gibi)
        logger.debug(f"Initializing model with name: {GEMINI_MODEL}")
        function_declaration = get_function_declaration()
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": LLM_TEMPERATURE,
            },
            tools=[function_declaration]
        )
        
        # Make API call with retry (veri ön işleme modülündeki gibi)
        last_error = None
        for attempt in range(LLM_MAX_RETRIES + 1):
            try:
                logger.info(f"🔄 Calling LLM for visualization suggestions (level: {safe_analysis_level}) - Attempt {attempt + 1}/{LLM_MAX_RETRIES + 1}")
                logger.debug(f"   Model: {GEMINI_MODEL}, Temperature: {LLM_TEMPERATURE}, Timeout: {LLM_TIMEOUT}s")
                
                # Make API call with function calling
                response = model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": LLM_TEMPERATURE,
                    }
                )
                logger.debug(f"✅ API call successful, response received")
                
                # Check for function call in response (veri ön işleme modülündeki gibi)
                function_call = None
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            # PARTS'ı listeye dönüştür (RepeatedComposite sorunu için)
                            parts_list = list(candidate.content.parts) if candidate.content.parts else []
                            logger.debug(f"📋 Response parts count: {len(parts_list)}")
                            for i, part in enumerate(parts_list):
                                logger.debug(f"   Part {i}: type={type(part).__name__}, has_function_call={hasattr(part, 'function_call')}")
                                if hasattr(part, 'function_call') and part.function_call:
                                    function_call = part.function_call
                                    logger.info("✅ Function call detected in response")
                                    break
                
                # If function call exists, extract structured data (veri ön işleme modülündeki gibi)
                if function_call:
                    if function_call.name == "suggest_visualizations":
                        # Extract function arguments
                        args = function_call.args
                        raw_suggestions = args.get("suggestions", [])
                        
                        logger.info(f"✅ Function call successful - {len(raw_suggestions)} suggestions received")
                        
                        # Process suggestions (filter, add missing columns, etc.)
                        result = _process_suggestions(raw_suggestions, numeric_columns, categorical_columns)
                        return result
                    else:
                        logger.warning(f"⚠️ Unknown function call: {function_call.name}")
                        if attempt < LLM_MAX_RETRIES:
                            wait_time = 3 * (attempt + 1)  # Exponential backoff: 3s, 6s, 9s
                            logger.warning(f"   ⏳ Waiting {wait_time} seconds before retry...")
                            time.sleep(wait_time)
                            continue
                        else:
                            return {
                                'suggestions': [],
                                'error': f'Unknown function call: {function_call.name}'
                            }
                else:
                    # Fallback: Try to extract text and parse JSON (veri ön işleme modülündeki gibi)
                    logger.warning("⚠️ No function call detected, falling back to JSON parsing")
                    try:
                        response_text = _extract_text_from_response(response)
                        parsed = _parse_json_response(response_text)
                        if parsed and "suggestions" in parsed:
                            logger.info(f"✅ JSON parsing successful - {len(parsed['suggestions'])} suggestions")
                            raw_suggestions = parsed['suggestions']
                            # Process suggestions same as function call path
                            return _process_suggestions(raw_suggestions, numeric_columns, categorical_columns)
                        else:
                            logger.warning("⚠️ Could not parse JSON from response")
                    except Exception as parse_error:
                        logger.warning(f"⚠️ JSON parsing failed: {parse_error}")
                    
                    if attempt < LLM_MAX_RETRIES:
                        time.sleep(1)  # Wait before retry (veri ön işleme modülündeki gibi)
                        continue
                    else:
                        logger.warning("⚠️ No function call detected after all attempts")
                        return {
                            'suggestions': [],
                            'error': 'Function call not detected'
                        }
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ API call attempt {attempt + 1} failed: {e}")
                if attempt < LLM_MAX_RETRIES:
                    time.sleep(1)  # Wait before retry (veri ön işleme modülündeki gibi)
                else:
                    logger.error(f"❌ All {LLM_MAX_RETRIES + 1} attempts failed")
        
        # If all retries failed
        if last_error:
            logger.error(f"❌ Failed to get visualization suggestions: {last_error}", exc_info=True)
        return {"suggestions": []}
        
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        error_repr = repr(e)
        
        logger.error(f"❌❌❌ LLM visualization suggestion FAILED ❌❌❌")
        logger.error(f"   Error Type: {error_type}")
        logger.error(f"   Error Message: {error_msg}")
        logger.error(f"   Error Repr: {error_repr}")
        
        # Full traceback
        import traceback
        logger.error(f"   Full Traceback:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                logger.error(f"      {line}")
        
        # Additional context
        logger.error(f"   Context:")
        logger.error(f"      - LLM Enabled: {LLM_ENABLED}")
        logger.error(f"      - Gemini Available: {GEMINI_AVAILABLE}")
        logger.error(f"      - API Key Set: {bool(GEMINI_API_KEY)}")
        logger.error(f"      - Model: {GEMINI_MODEL}")
        
        return {
            'suggestions': [],
            'error': f'{error_type}: {error_msg}'
        }


def _process_suggestions(
    raw_suggestions: List[Dict],
    numeric_columns: List[str],
    categorical_columns: List[str]
) -> Dict:
    """
    Process raw suggestions: filter complex ones, clean HTML, and add missing column suggestions.
    (veri ön işleme modülündeki yaklaşıma benzer)
    """
    logger.info("=" * 80)
    logger.info(f"📥 LLM RAW RESPONSE: {len(raw_suggestions)} suggestions received from LLM")
    
    # RADIKAL TEMİZLEME: Backend'de HTML tag'lerini temizle ve complex suggestions'ı filtrele
    filtered_suggestions = []
    complex_count = 0
    for suggestion in raw_suggestions:
        if 'reason' in suggestion and suggestion['reason']:
            suggestion['reason'] = clean_html_from_text(suggestion['reason'])
        # Filter out complex suggestions (Gelişmiş level)
        if suggestion.get('analysis_level', '').lower() == 'gelişmiş':
            complex_count += 1
        else:
            filtered_suggestions.append(suggestion)
    
    if complex_count > 0:
        logger.info(f"🚫 FILTERED OUT: {complex_count} complex (Gelişmiş) suggestions removed")
    logger.info(f"✅ AFTER FILTERING: {len(filtered_suggestions)} valid suggestions remaining")
    
    # Her sütun için grafik kontrolü - eksik sütunlar için otomatik öneriler ekle
    total_columns = len(numeric_columns) + len(categorical_columns)
    suggested_columns = set()
    for suggestion in filtered_suggestions:
        col = suggestion.get('column', '')
        if col and col in numeric_columns + categorical_columns:
            suggested_columns.add(col)
    
    logger.info(f"📊 COLUMN COVERAGE: LLM covered {len(suggested_columns)}/{total_columns} columns")
    
    # Eksik sayısal sütunlar için otomatik Histogram önerisi ekle
    missing_numeric = [col for col in numeric_columns if col not in suggested_columns]
    auto_added_count = 0
    if missing_numeric:
        logger.info(f"➕ AUTO-ADDING: {len(missing_numeric)} Histogram suggestions for missing numeric columns")
        logger.info(f"   Columns: {', '.join(missing_numeric[:10])}{'...' if len(missing_numeric) > 10 else ''}")
        for col in missing_numeric:
            filtered_suggestions.append({
                'visualization_type': 'Histogram',
                'column': col,
                'reason': f'{col} sütununun dağılımını görselleştirmek için histogram önerilir.',
                'analysis_level': 'Temel'
            })
            auto_added_count += 1
    
    # Eksik kategorik sütunlar için otomatik Bar Chart önerisi ekle
    missing_categorical = [col for col in categorical_columns if col not in suggested_columns]
    if missing_categorical:
        logger.info(f"➕ AUTO-ADDING: {len(missing_categorical)} Bar Chart suggestions for missing categorical columns")
        logger.info(f"   Columns: {', '.join(missing_categorical[:10])}{'...' if len(missing_categorical) > 10 else ''}")
        for col in missing_categorical:
            filtered_suggestions.append({
                'visualization_type': 'Bar Chart',
                'column': col,
                'reason': f'{col} sütununun değer dağılımını görselleştirmek için bar chart önerilir.',
                'analysis_level': 'Temel'
            })
            auto_added_count += 1
    
    logger.info("=" * 80)
    logger.info(f"✅ FINAL RESULT: {len(filtered_suggestions)} total suggestions")
    logger.info(f"   - {len(raw_suggestions)} from LLM")
    logger.info(f"   - {auto_added_count} auto-added for missing columns")
    logger.info(f"   - {complex_count} complex suggestions filtered out")
    logger.info(f"📊 COMPLETE COVERAGE: All {total_columns} columns now have visualization suggestions")
    logger.info("=" * 80)
    
    return {
        'suggestions': filtered_suggestions,
        'error': None
    }


def _extract_text_from_response(response) -> str:
    """Extract text from Gemini API response. (veri ön işleme modülündeki gibi)"""
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
                    # PARTS'ı listeye dönüştür (RepeatedComposite sorunu için)
                    parts_list = list(candidate.content.parts) if candidate.content.parts else []
                    logger.debug(f"📋 Extracting text from {len(parts_list)} parts")
                    for i, part in enumerate(parts_list):
                        if hasattr(part, 'text') and part.text:
                            logger.debug(f"Extracted text using candidates[0].content.parts[{i}].text")
                            return part.text.strip()
    except Exception as e:
        logger.debug(f"candidates[0].content.parts failed: {e}")
        logger.error(f"❌ Error details: {type(e).__name__}: {str(e)}")
    
    raise Exception("Could not extract text from response")


def _parse_json_response(response_text: str) -> Optional[Dict]:
    """Parse JSON from LLM response. (veri ön işleme modülündeki gibi)"""
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


def interpret_analysis(
    visualization_type: str,
    column_name: str,
    data_summary: dict,
    statistics: dict = None
) -> Dict:
    """
    Get LLM interpretation of a visualization.
    
    Args:
        visualization_type: Type of visualization
        column_name: Column name
        data_summary: Data summary dictionary
        statistics: Optional statistics dictionary
        
    Returns:
        Dictionary with interpretation
    """
    if not LLM_ENABLED or not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return {
            'interpretation': '',
            'key_findings': [],
            'recommendations': [],
            'error': 'LLM is not enabled or not available'
        }
    
    try:
        # Get function declaration
        function_declaration = get_function_declaration()
        
        # Initialize model with function calling
        try:
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config={
                    "temperature": LLM_TEMPERATURE,
                },
                tools=[function_declaration]
            )
            logger.info("✅ Model initialized successfully for interpretation")
        except Exception as init_error:
            logger.error(f"❌ Model initialization failed: {type(init_error).__name__}: {str(init_error)}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return {
                'interpretation': '',
                'key_findings': [],
                'recommendations': [],
                'error': f'Model initialization failed: {str(init_error)}'
            }
        
        # Prepare prompt
        user_prompt = get_analysis_interpretation_prompt(
            visualization_type,
            column_name,
            data_summary,
            statistics
        )
        full_prompt = f"{EDA_SYSTEM_PROMPT}\n\n{user_prompt}"
        
        # Retry mechanism (1 retry = 2 total attempts)
        last_error = None
        for attempt in range(LLM_MAX_RETRIES + 1):
            try:
                # Call API
                logger.info(f"🔄 Calling LLM for analysis interpretation ({visualization_type}, {column_name}) - Attempt {attempt + 1}/{LLM_MAX_RETRIES + 1}")
                response = model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": LLM_TEMPERATURE,
                    }
                )
                
                # Extract function call (data_upload modülündeki gibi)
                function_call = None
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            # PARTS'ı listeye dönüştür (RepeatedComposite sorunu için)
                            parts_list = list(candidate.content.parts) if candidate.content.parts else []
                            for part in parts_list:
                                if hasattr(part, 'function_call'):
                                    function_call = part.function_call
                                    logger.info("✅ Function call detected in response")
                                    break
                
                if function_call and function_call.name == "interpret_analysis":
                    args = function_call.args
                    interpretation = args.get("interpretation", "")
                    key_findings = args.get("key_findings", [])
                    recommendations = args.get("recommendations", [])
                    
                    # RADIKAL TEMİZLEME: HTML tag'lerini temizle
                    interpretation = clean_html_from_text(interpretation)
                    key_findings = [clean_html_from_text(finding) for finding in key_findings if finding]
                    recommendations = [clean_html_from_text(rec) for rec in recommendations if rec]
                    
                    logger.info(f"✅ Received interpretation with {len(key_findings)} findings")
                    return {
                        'interpretation': interpretation,
                        'key_findings': key_findings,
                        'recommendations': recommendations,
                        'error': None
                    }
                else:
                    if attempt < LLM_MAX_RETRIES:
                        wait_time = 3 * (attempt + 1)  # Exponential backoff: 3s, 6s, 9s
                        logger.warning(f"⚠️ No function call detected on attempt {attempt + 1}, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.warning("⚠️ No function call detected after all attempts")
                        return {
                            'interpretation': '',
                            'key_findings': [],
                            'recommendations': [],
                            'error': 'Function call not detected'
                        }
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e)
                
                logger.error(f"❌ Interpretation attempt {attempt + 1} failed: {error_type}: {error_msg}")
                if "minItems" in error_msg or "Schema" in error_msg:
                    logger.error(f"   🔍 DETECTED: Schema validation error")
                
                if attempt < LLM_MAX_RETRIES:
                    wait_time = 3 * (attempt + 1)  # Exponential backoff: 3s, 6s, 9s
                    logger.warning(f"   ⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.error(f"❌ LLM analysis interpretation FAILED: {error_type}: {error_msg}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        
        return {
            'interpretation': '',
            'key_findings': [],
            'recommendations': [],
            'error': f'{error_type}: {error_msg}'
        }


def suggest_next_steps_analysis(
    completed_analyses: list,
    data_summary: dict,
    numeric_columns: list,
    categorical_columns: list
) -> Dict:
    """
    Get LLM suggestions for next analysis steps.
    
    Args:
        completed_analyses: List of completed analysis types
        data_summary: Data summary dictionary
        numeric_columns: List of numeric column names
        categorical_columns: List of categorical column names
        
    Returns:
        Dictionary with next steps suggestions
    """
    if not LLM_ENABLED or not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return {
            'next_steps': [],
            'error': 'LLM is not enabled or not available'
        }
    
    try:
        # Get function declaration
        function_declaration = get_function_declaration()
        
        # Initialize model with function calling
        try:
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config={
                    "temperature": LLM_TEMPERATURE,
                },
                tools=[function_declaration]
            )
            logger.info("✅ Model initialized successfully for next steps")
        except Exception as init_error:
            logger.error(f"❌ Model initialization failed: {type(init_error).__name__}: {str(init_error)}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return {
                'next_steps': [],
                'error': f'Model initialization failed: {str(init_error)}'
            }
        
        # Prepare prompt
        user_prompt = get_next_steps_prompt(
            completed_analyses,
            data_summary,
            numeric_columns,
            categorical_columns
        )
        full_prompt = f"{EDA_SYSTEM_PROMPT}\n\n{user_prompt}"
        
        # Retry mechanism (1 retry = 2 total attempts)
        last_error = None
        for attempt in range(LLM_MAX_RETRIES + 1):
            try:
                # Call API
                logger.info(f"🔄 Calling LLM for next steps suggestions - Attempt {attempt + 1}/{LLM_MAX_RETRIES + 1}")
                response = model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": LLM_TEMPERATURE,
                    }
                )
                
                # Extract function call (data_upload modülündeki gibi)
                function_call = None
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            # PARTS'ı listeye dönüştür (RepeatedComposite sorunu için)
                            parts_list = list(candidate.content.parts) if candidate.content.parts else []
                            for part in parts_list:
                                if hasattr(part, 'function_call'):
                                    function_call = part.function_call
                                    logger.info("✅ Function call detected in response")
                                    break
                
                if function_call and function_call.name == "suggest_next_steps":
                    args = function_call.args
                    next_steps = args.get("next_steps", [])
                    
                    # RADIKAL TEMİZLEME: HTML tag'lerini temizle
                    for step in next_steps:
                        if 'step' in step and step['step']:
                            step['step'] = clean_html_from_text(step['step'])
                    
                    logger.info(f"✅ Received {len(next_steps)} next steps suggestions")
                    return {
                        'next_steps': next_steps,
                        'error': None
                    }
                else:
                    if attempt < LLM_MAX_RETRIES:
                        wait_time = 3 * (attempt + 1)  # Exponential backoff: 3s, 6s, 9s
                        logger.warning(f"⚠️ No function call detected on attempt {attempt + 1}, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.warning("⚠️ No function call detected after all attempts")
                        return {
                            'next_steps': [],
                            'error': 'Function call not detected'
                        }
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e)
                
                logger.error(f"❌ Next steps attempt {attempt + 1} failed: {error_type}: {error_msg}")
                if "minItems" in error_msg or "Schema" in error_msg:
                    logger.error(f"   🔍 DETECTED: Schema validation error")
                    import traceback
                    logger.error(f"   Traceback: {traceback.format_exc()}")
                
                if attempt < LLM_MAX_RETRIES:
                    wait_time = 3 * (attempt + 1)  # Exponential backoff: 3s, 6s, 9s
                    logger.warning(f"   ⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.error(f"❌ LLM next steps suggestion FAILED: {error_type}: {error_msg}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        
        return {
            'next_steps': [],
            'error': f'{error_type}: {error_msg}'
        }

