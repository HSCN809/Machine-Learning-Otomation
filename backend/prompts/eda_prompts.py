"""System prompts for EDA LLM enhancements."""

EDA_SYSTEM_PROMPT = """Sen bir veri bilimi uzmanısın. Veri görselleştirme önerileri sunuyorsun.

KRİTİK KURAL: Her zaman sağlanan fonksiyonları kullanarak cevap ver. Function calling kullanmadan cevap verme.

Kurallar:
- Tüm metin alanlarında SADECE düz metin kullan (HTML/Markdown YOK)
- visualization_type: SADECE İngilizce
- reason: SADECE düz Türkçe metin
"""


def get_visualization_suggestion_prompt(
    data_summary: dict,
    numeric_columns: list,
    categorical_columns: list,
    analysis_level: str = 'Temel'
) -> str:
    """
    Generate prompt for visualization suggestions.
    
    Args:
        data_summary: Data summary dictionary
        numeric_columns: List of numeric column names
        categorical_columns: List of categorical column names
        analysis_level: Analysis level ('Temel', 'Orta', 'Gelişmiş')
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""VERİ SETİ BİLGİLERİ:
- Satır: {data_summary.get('shape', {}).get('rows', 0):,}
- Sütun: {data_summary.get('shape', {}).get('columns', 0)}
- Sayısal: {len(numeric_columns)} ({', '.join(numeric_columns[:5])}{'...' if len(numeric_columns) > 5 else ''})
- Kategorik: {len(categorical_columns)} ({', '.join(categorical_columns[:5])}{'...' if len(categorical_columns) > 5 else ''})
- Eksik Değer: %{data_summary.get('missing_values', {}).get('missing_percentage', 0):.1f}
- Analiz Seviyesi: {analysis_level}

GÖREV: Bu veri seti için EN AZ 8 görselleştirme önerisi sun. MUTLAKA suggest_visualizations fonksiyonunu kullan.

KURALLAR:
1. visualization_type: SADECE İngilizce (örn: "Histogram", "Box Plot", "Scatter Plot", "Correlation Matrix", "Grouped Bar Chart")
2. reason: SADECE düz Türkçe metin, HTML/Markdown YOK
3. analysis_level: "Temel", "Orta" veya "Gelişmiş"
4. column: İlgili sütun adı (varsa)

ŞİMDİ suggest_visualizations FONKSİYONUNU ÇAĞIR.
"""
    return prompt


def get_analysis_interpretation_prompt(
    visualization_type: str,
    column_name: str,
    data_summary: dict,
    statistics: dict = None
) -> str:
    """
    Generate prompt for interpreting a visualization.
    
    Args:
        visualization_type: Type of visualization (histogram, box_plot, etc.)
        column_name: Column name being visualized
        data_summary: Data summary dictionary
        statistics: Optional statistics dictionary
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""Aşağıdaki görselleştirmeyi yorumla:

**Görselleştirme Tipi:** {visualization_type}
**Sütun:** {column_name}

**Veri Seti Bilgileri:**
- Toplam Satır: {data_summary.get('shape', {}).get('rows', 0):,}
- Toplam Sütun: {data_summary.get('shape', {}).get('columns', 0)}
"""
    
    if statistics:
        prompt += f"""
**İstatistikler:**
"""
        for key, value in statistics.items():
            if isinstance(value, float):
                prompt += f"- {key}: {value:.4f}\n"
            else:
                prompt += f"- {key}: {value}\n"
    
    prompt += """
Lütfen interpret_analysis fonksiyonunu kullanarak bu görselleştirmeyi yorumla ve önemli bulguları açıkla.
"""
    return prompt


def get_next_steps_prompt(
    completed_analyses: list,
    data_summary: dict,
    numeric_columns: list,
    categorical_columns: list
) -> str:
    """
    Generate prompt for suggesting next analysis steps.
    
    Args:
        completed_analyses: List of completed analysis types
        data_summary: Data summary dictionary
        numeric_columns: List of numeric column names
        categorical_columns: List of categorical column names
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""Aşağıdaki analizler tamamlandı:
{', '.join(completed_analyses) if completed_analyses else 'Henüz analiz yapılmadı'}

**Veri Seti Bilgileri:**
- Toplam Satır: {data_summary.get('shape', {}).get('rows', 0):,}
- Toplam Sütun: {data_summary.get('shape', {}).get('columns', 0)}
- Sayısal Sütunlar: {len(numeric_columns)}
- Kategorik Sütunlar: {len(categorical_columns)}

Lütfen suggest_next_steps fonksiyonunu kullanarak sonraki analiz adımlarını öner.
"""
    return prompt

