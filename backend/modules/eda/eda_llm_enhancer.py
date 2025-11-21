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
                                        "description": "Bu önerinin analiz seviyesi (Temel, Orta, Gelişmiş)",
                                        "enum": ["Temel", "Orta", "Gelişmiş"]
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
        analysis_level: Analysis level ('Temel', 'Orta', 'Gelişmiş')
        
    Returns:
        Dictionary with visualization suggestions
    """
    if not LLM_ENABLED or not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return {
            'suggestions': [],
            'error': 'LLM is not enabled or not available'
        }
    
    try:
        # Get function declaration (data_upload modülündeki gibi)
        function_declaration = get_function_declaration()
        
        # Initialize model with function calling
        try:
            logger.info(f"🔧 Initializing model with function declaration...")
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config={
                    "temperature": LLM_TEMPERATURE,
                },
                tools=[function_declaration]
            )
            logger.info("✅ Model initialized successfully with function declarations")
        except Exception as init_error:
            error_type = type(init_error).__name__
            error_msg = str(init_error)
            logger.error(f"❌ Model initialization failed!")
            logger.error(f"   Error Type: {error_type}")
            logger.error(f"   Error Message: {error_msg}")
            logger.error(f"   Error Repr: {repr(init_error)}")
            
            # Check if it's a schema validation error
            if "minItems" in error_msg or "Schema" in error_msg or "schema" in error_msg.lower():
                logger.error(f"   🔍 DETECTED: Schema validation error!")
                logger.error(f"   📋 Function declaration structure:")
                try:
                    logger.error(f"      {json.dumps(function_declaration, indent=6, ensure_ascii=False)}")
                except:
                    logger.error(f"      (Could not serialize)")
            
            import traceback
            logger.error(f"   Traceback:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    logger.error(f"      {line}")
            
            return {
                'suggestions': [],
                'error': f'Model initialization failed: {error_type}: {error_msg}'
            }
        
        # Prepare prompt
        user_prompt = get_visualization_suggestion_prompt(
            data_summary,
            numeric_columns,
            categorical_columns,
            analysis_level
        )
        full_prompt = f"{EDA_SYSTEM_PROMPT}\n\n{user_prompt}"
        logger.debug(f"Prompt length: {len(full_prompt)} characters")
        
        # Retry mechanism (1 retry = 2 total attempts)
        last_error = None
        for attempt in range(LLM_MAX_RETRIES + 1):
            try:
                # Call API
                logger.info(f"🔄 Calling LLM for visualization suggestions (level: {analysis_level}) - Attempt {attempt + 1}/{LLM_MAX_RETRIES + 1}")
                logger.debug(f"   Model: {GEMINI_MODEL}, Temperature: {LLM_TEMPERATURE}, Timeout: {LLM_TIMEOUT}s")
                
                response = model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": LLM_TEMPERATURE,
                    }
                )
                logger.debug(f"✅ API call successful, response received")
                
                # Extract function call (data_upload modülündeki gibi)
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
                
                if function_call and function_call.name == "suggest_visualizations":
                    args = function_call.args
                    suggestions = args.get("suggestions", [])
                    
                    # RADIKAL TEMİZLEME: Backend'de HTML tag'lerini temizle
                    for suggestion in suggestions:
                        if 'reason' in suggestion and suggestion['reason']:
                            suggestion['reason'] = clean_html_from_text(suggestion['reason'])
                    
                    logger.info(f"✅ Received {len(suggestions)} visualization suggestions")
                    return {
                        'suggestions': suggestions,
                        'error': None
                    }
                else:
                    # Debug: Log response details if no function call
                    logger.warning(f"⚠️ No function call detected on attempt {attempt + 1}")
                    try:
                        # Try to get text response for debugging
                        response_text = None
                        if hasattr(response, 'text'):
                            response_text = response.text[:500] if response.text else "No text"
                        elif hasattr(response, 'candidates') and response.candidates:
                            candidate = response.candidates[0]
                            if hasattr(candidate, 'content') and candidate.content:
                                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                    for part in candidate.content.parts:
                                        if hasattr(part, 'text') and part.text:
                                            response_text = part.text[:500]
                                            break
                        
                        if response_text:
                            logger.warning(f"   📝 Response text (first 500 chars): {response_text}")
                        else:
                            logger.warning(f"   📝 No text response found")
                            
                        # Check finish_reason
                        if hasattr(response, 'candidates') and response.candidates:
                            candidate = response.candidates[0]
                            finish_reason = getattr(candidate, 'finish_reason', None)
                            logger.warning(f"   🔍 Finish reason: {finish_reason}")
                            
                    except Exception as debug_e:
                        logger.warning(f"   ❌ Could not extract response details: {debug_e}")
                    
                    if attempt < LLM_MAX_RETRIES:
                        logger.warning(f"   Retrying...")
                        time.sleep(1)  # Short delay before retry
                        continue
                    else:
                        logger.warning("⚠️ No function call detected after all attempts")
                        return {
                            'suggestions': [],
                            'error': 'Function call not detected'
                        }
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e)
                error_repr = repr(e)
                
                logger.error(f"❌ Attempt {attempt + 1} failed!")
                logger.error(f"   Error Type: {error_type}")
                logger.error(f"   Error Message: {error_msg}")
                logger.error(f"   Error Repr: {error_repr}")
                
                # Detailed traceback
                import traceback
                tb_lines = traceback.format_exc().split('\n')
                logger.error(f"   Traceback:")
                for line in tb_lines:
                    if line.strip():
                        logger.error(f"      {line}")
                
                # Check for specific error types
                if "minItems" in error_msg or "Schema" in error_msg:
                    logger.error(f"   🔍 DETECTED: Schema validation error (minItems issue)")
                    logger.error(f"   💡 This might be a Gemini API function declaration format issue")
                    logger.error(f"   📋 Function declaration structure:")
                    try:
                        logger.error(f"      {json.dumps(function_declaration, indent=6, ensure_ascii=False)}")
                    except:
                        logger.error(f"      (Could not serialize function declaration)")
                
                if attempt < LLM_MAX_RETRIES:
                    logger.warning(f"   ⏳ Retrying in 1 second...")
                    time.sleep(1)  # Short delay before retry
                    continue
                else:
                    raise
            
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
                            for part in candidate.content.parts:
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
                        logger.warning(f"⚠️ No function call detected on attempt {attempt + 1}, retrying...")
                        time.sleep(1)  # Short delay before retry
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
                    logger.warning(f"   ⏳ Retrying...")
                    time.sleep(1)
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
                            for part in candidate.content.parts:
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
                        logger.warning(f"⚠️ No function call detected on attempt {attempt + 1}, retrying...")
                        time.sleep(1)  # Short delay before retry
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
                    logger.warning(f"   ⏳ Retrying...")
                    time.sleep(1)
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

