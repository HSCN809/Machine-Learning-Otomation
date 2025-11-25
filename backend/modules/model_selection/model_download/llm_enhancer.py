"""LLM enhancement functions for model download step."""

import time
import json
import logging
from typing import Dict, Optional, List

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

logger = logging.getLogger(__name__)

# Initialize Gemini if available
if GEMINI_AVAILABLE and LLM_ENABLED and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Gemini API key configuration failed: {e}")


def get_model_recommendation_prompt(
    model_results: Dict,
    problem_type: str,
    feature_importance_data: Optional[Dict] = None,
    permutation_importance_data: Optional[Dict] = None,
    shap_data: Optional[Dict] = None
) -> str:
    """
    Create a prompt for LLM to recommend which model to download.
    
    Args:
        model_results: Dictionary containing model results with metrics
        problem_type: Problem type (binary_classification, multiclass_classification, regression)
        feature_importance_data: Feature importance data for models
        permutation_importance_data: Permutation importance data
        shap_data: SHAP values data
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""Sen bir makine öğrenmesi uzmanısın. Kullanıcıya hangi modeli indirmesi gerektiği konusunda tavsiye vermelisin.

Problem Tipi: {problem_type}

Model Performans Metrikleri:
"""
    
    # Metrik önceliklendirmesi tanımla
    if problem_type in ['binary_classification', 'multiclass_classification']:
        primary_metrics = ['accuracy', 'f1_score', 'precision', 'recall']
        secondary_metrics = ['roc_auc', 'precision_macro', 'precision_weighted', 
                            'recall_macro', 'recall_weighted', 'f1_score_macro', 'f1_score_weighted']
        excluded_metrics = ['confusion_matrix', 'error']
    elif problem_type == 'regression':
        primary_metrics = ['r2_score', 'rmse', 'mae']
        secondary_metrics = ['adjusted_r2', 'mse', 'mape']
        excluded_metrics = ['error']
    else:
        primary_metrics = []
        secondary_metrics = []
        excluded_metrics = ['error', 'confusion_matrix']
    
    # Add model metrics with prioritization
    for model_name, model_data in model_results.items():
        metrics = model_data.get('metrics', {})
        prompt += f"\n{model_name}:\n"
        
        # Önce öncelikli metrikleri ekle
        if primary_metrics:
            prompt += "  [ÖNEMLİ METRİKLER]\n"
            # Accuracy'yi önce ve özel olarak göster (classification için)
            if problem_type in ['binary_classification', 'multiclass_classification'] and 'accuracy' in metrics and metrics['accuracy'] is not None:
                accuracy_value = metrics['accuracy']
                if isinstance(accuracy_value, (int, float)):
                    prompt += f"  - ⭐ ACCURACY (EN ÖNEMLİ): {accuracy_value:.4f}\n"
                else:
                    prompt += f"  - ⭐ ACCURACY (EN ÖNEMLİ): {accuracy_value}\n"
            
            # Diğer öncelikli metrikleri ekle (accuracy hariç)
            for metric_name in primary_metrics:
                if metric_name == 'accuracy' and problem_type in ['binary_classification', 'multiclass_classification']:
                    continue  # Accuracy zaten eklendi
                if metric_name in metrics and metrics[metric_name] is not None:
                    metric_value = metrics[metric_name]
                    if isinstance(metric_value, (int, float)):
                        prompt += f"  - {metric_name}: {metric_value:.4f}\n"
                    else:
                        prompt += f"  - {metric_name}: {metric_value}\n"
        
        # Sonra ikincil metrikleri ekle
        if secondary_metrics:
            prompt += "  [DİĞER METRİKLER]\n"
            for metric_name in secondary_metrics:
                if metric_name in metrics and metrics[metric_name] is not None:
                    metric_value = metrics[metric_name]
                    if isinstance(metric_value, (int, float)):
                        prompt += f"  - {metric_name}: {metric_value:.4f}\n"
                    else:
                        prompt += f"  - {metric_name}: {metric_value}\n"
        
        # Son olarak diğer metrikleri ekle (önceliklendirilmemiş)
        other_metrics = {k: v for k, v in metrics.items() 
                        if k not in primary_metrics + secondary_metrics + excluded_metrics 
                        and v is not None}
        if other_metrics:
            prompt += "  [DİĞER BİLGİLER]\n"
            for metric_name, metric_value in other_metrics.items():
                if isinstance(metric_value, (int, float)):
                    prompt += f"  - {metric_name}: {metric_value:.4f}\n"
                else:
                    prompt += f"  - {metric_name}: {metric_value}\n"
    
    # Add feature importance data if available
    if feature_importance_data:
        prompt += "\n\nFeature Importance Sonuçları:\n"
        for model_name, importance in feature_importance_data.items():
            if importance:
                top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
                prompt += f"\n{model_name} - En Önemli 5 Özellik:\n"
                for feature, value in top_features:
                    prompt += f"  - {feature}: {value:.4f}\n"
    
    # Add permutation importance if available
    if permutation_importance_data:
        prompt += "\n\nPermutation Importance Sonuçları:\n"
        for model_name, perm_data in permutation_importance_data.items():
            if perm_data:
                top_features = sorted(perm_data.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
                prompt += f"\n{model_name} - En Önemli 5 Özellik:\n"
                for feature, value in top_features:
                    prompt += f"  - {feature}: {value:.4f}\n"
    
    # Add SHAP data if available
    if shap_data:
        prompt += "\n\nSHAP Değerleri Sonuçları:\n"
        for model_name, shap_result in shap_data.items():
            if shap_result and 'mean_abs_shap' in shap_result:
                mean_shap = shap_result['mean_abs_shap']
                if mean_shap:
                    top_features = sorted(mean_shap.items(), key=lambda x: abs(x[1]) if isinstance(x[1], (int, float)) else 0, reverse=True)[:5]
                    prompt += f"\n{model_name} - En Önemli 5 Özellik:\n"
                    for feature, value in top_features:
                        if isinstance(value, (int, float)):
                            prompt += f"  - {feature}: {value:.4f}\n"
    
    prompt += """
\nLütfen aşağıdaki kriterlere göre hangi modelin indirilmesi gerektiğini öner:

1. **Model Performans Metrikleri** (Öncelik sırası):
"""
    
    if problem_type in ['binary_classification', 'multiclass_classification']:
        prompt += """   - ⭐ ACCURACY: Genel doğruluk oranı (EN ÖNCELİKLİ METRİK - Model seçiminde en önemli kriter)
   - F1 Score: Precision ve Recall dengesi (çok önemli)
   - Precision: Pozitif tahminlerin doğruluğu
   - Recall: Gerçek pozitiflerin yakalanma oranı
   - ROC AUC: Sınıflandırma kalitesi (binary classification için)"""
    elif problem_type == 'regression':
        prompt += """   - R² Score: Model açıklama gücü (en önemli)
   - RMSE: Hata büyüklüğü (çok önemli)
   - MAE: Ortalama mutlak hata (önemli)
   - Adjusted R²: Özellik sayısına göre düzeltilmiş R²"""
    
    prompt += """
2. Model yorumlanabilirliği (feature importance, permutation importance, SHAP)
3. Model karmaşıklığı ve kullanım kolaylığı
4. Production ortamı için uygunluk

Türkçe olarak, kısa ve öz bir şekilde, hangi modeli önerdiğini ve nedenlerini açıkla.
ÖNEMLİ: Classification problemlerinde Accuracy metriklerinin en öncelikli olduğunu unutma. Önce Accuracy'ye bak, sonra diğer metrikleri değerlendir.
Regression problemlerinde R² ve RMSE'yi önceliklendir.
"""
    
    return prompt


def get_model_recommendation(
    model_results: Dict,
    problem_type: str,
    feature_importance_data: Optional[Dict] = None,
    permutation_importance_data: Optional[Dict] = None,
    shap_data: Optional[Dict] = None
) -> Optional[str]:
    """
    Get LLM recommendation for which model to download.
    
    Args:
        model_results: Dictionary containing model results with metrics
        problem_type: Problem type
        feature_importance_data: Feature importance data for models
        permutation_importance_data: Permutation importance data
        shap_data: SHAP values data
        
    Returns:
        Recommendation text or None if failed
    """
    # Check LLM availability
    if not LLM_ENABLED:
        logger.debug("LLM_ENABLED is False - skipping recommendation")
        return None
    if not GEMINI_AVAILABLE:
        logger.error("google-generativeai package not available")
        return None
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is empty - check .env file")
        return None
    
    logger.info(f"🔧 Getting model recommendation using GEMINI_MODEL: {GEMINI_MODEL}")
    
    try:
        # Prepare prompt
        prompt = get_model_recommendation_prompt(
            model_results,
            problem_type,
            feature_importance_data,
            permutation_importance_data,
            shap_data
        )
        
        # Initialize model
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": LLM_TEMPERATURE,
                "max_output_tokens": LLM_MAX_TOKENS,
            }
        )
        
        # Make API call with retry
        last_error = None
        for attempt in range(LLM_MAX_RETRIES + 1):
            try:
                logger.debug(f"API call attempt {attempt + 1}/{LLM_MAX_RETRIES + 1}")
                
                response = model.generate_content(prompt)
                
                # Extract text from response
                if hasattr(response, 'text'):
                    recommendation = response.text.strip()
                elif hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            recommendation = candidate.content.parts[0].text.strip()
                        elif hasattr(candidate.content, 'text'):
                            recommendation = candidate.content.text.strip()
                        else:
                            recommendation = str(response)
                    else:
                        recommendation = str(response)
                else:
                    recommendation = str(response)
                
                logger.info(f"✅ LLM recommendation received: {len(recommendation)} chars")
                return recommendation
                
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
        logger.error(f"LLM recommendation failed: {e}")
        return None

