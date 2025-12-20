"""System prompts for data validation LLM enhancements."""

VALIDATION_SYSTEM_PROMPT = """Sen bir veri bilimi uzmanısın. KISA ve ÖZ cevap ver.

MUTLAKA UYULMASI GEREKEN KURALLAR:
- Cevabın TOPLAM 2-3 CÜMLE olmalı
- Sadece EN ÖNEMLİ çözümü öner
- Gereksiz açıklama YAPMA
- "Model performansı için..." gibi tek cümle etki belirt

YASAK:
- Uzun paragraflar
- Madde madde listeler
- Birden fazla alternatif
- Detaylı teknik açıklamalar
"""

def get_validation_user_prompt(issue: dict, data_summary: dict, column_stats: dict = None) -> str:
    """
    Generate user prompt for validation issue enhancement.
    
    Args:
        issue: Issue dictionary with type, severity, column, description, suggestion
        data_summary: Data summary dictionary with shape, missing_values, etc.
        column_stats: Optional column-specific statistics
        
    Returns:
        Formatted user prompt string
    """
    prompt = f"""Aşağıdaki veri kalitesi sorununu analiz et ve zenginleştirilmiş öneri sun:

**Sorun Tipi:** {issue.get('type', 'bilinmeyen')}
**Şiddet:** {issue.get('severity', 'bilgi')}
**Sütun:** {issue.get('column', 'Genel') if issue.get('column') else 'Genel'}
**Açıklama:** {issue.get('description', '')}
**Mevcut Öneri:** {issue.get('suggestion', '')}

**Veri Seti Bilgileri:**
- Toplam Satır: {data_summary.get('shape', {}).get('rows', 0):,}
- Toplam Sütun: {data_summary.get('shape', {}).get('columns', 0)}
- Sayısal Sütunlar: {data_summary.get('numeric_columns', 0)}
- Kategorik Sütunlar: {data_summary.get('categorical_columns', 0)}
- Eksik Değer Oranı: %{data_summary.get('missing_values', {}).get('missing_percentage', 0):.1f}
"""
    
    if column_stats and issue.get('column'):
        col = issue['column']
        # Format column stats as readable text instead of raw dict
        stats_text = f"Veri Tipi: {column_stats.get('data_type', 'N/A')}, "
        stats_text += f"Toplam Değer: {column_stats.get('total_values', 0)}, "
        stats_text += f"Eksik Değer: {column_stats.get('null_count', 0)} (%{column_stats.get('null_percentage', 0):.1f}), "
        stats_text += f"Benzersiz Değer: {column_stats.get('unique_count', 0)}"
        
        # Check if numeric (has mean, median, etc.)
        if 'mean' in column_stats and column_stats.get('mean') is not None:
            stats_text += f", Ortalama: {column_stats.get('mean', 'N/A')}, "
            stats_text += f"Min: {column_stats.get('min', 'N/A')}, Max: {column_stats.get('max', 'N/A')}"
        elif 'most_frequent' in column_stats:
            stats_text += f", En Sık: {column_stats.get('most_frequent', 'N/A')}"
        
        prompt += f"""
**Sütun İstatistikleri ({col}):**
{stats_text}
"""
    
    prompt += """
Lütfen bu sorun için enhance_validation_suggestion fonksiyonunu kullanarak zenginleştirilmiş öneri, etki analizi ve öncelik seviyesi üret.
"""
    
    return prompt

