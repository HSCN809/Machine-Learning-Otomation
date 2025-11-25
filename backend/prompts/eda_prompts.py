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
        analysis_level: Analysis level ('Temel', 'Orta')
        
    Returns:
        Formatted prompt string
    """
    # Detaylı veri bilgisi
    missing_info = data_summary.get('missing_values', {})
    missing_pct = missing_info.get('missing_percentage', 0)
    missing_cols = missing_info.get('columns_with_missing', 0)
    
    duplicate_rows = data_summary.get('duplicate_rows', 0)
    duplicate_pct = (duplicate_rows / data_summary.get('shape', {}).get('rows', 1) * 100) if data_summary.get('shape', {}).get('rows', 0) > 0 else 0
    
    # Sütun listelerini hazırla
    all_numeric = ', '.join(numeric_columns) if numeric_columns else 'Yok'
    all_categorical = ', '.join(categorical_columns) if categorical_columns else 'Yok'
    
    prompt = f"""VERİ SETİ BİLGİLERİ:
- Satır: {data_summary.get('shape', {}).get('rows', 0):,}
- Sütun: {data_summary.get('shape', {}).get('columns', 0)}
- Sayısal Sütunlar ({len(numeric_columns)} adet): {all_numeric}
- Kategorik Sütunlar ({len(categorical_columns)} adet): {all_categorical}
- Eksik Değer: %{missing_pct:.1f} ({missing_cols} sütunda)
- Tekrar Eden Satır: {duplicate_rows} (%{duplicate_pct:.1f})
- Analiz Seviyesi: {analysis_level}

VERİ KALİTESİ:
- Eksik değer oranı: {'Yüksek' if missing_pct > 20 else ('Orta' if missing_pct > 5 else 'Düşük')}
- Veri temizliği: {'İyi' if duplicate_pct < 5 and missing_pct < 5 else ('Orta' if duplicate_pct < 10 and missing_pct < 10 else 'Dikkat Gerekli')}

GÖREV: Bu veri seti için HER SÜTUN İÇİN basic görselleştirme önerisi sun. MUTLAKA suggest_visualizations fonksiyonunu kullan.

KRİTİK KURALLAR:
1. HER SAYISAL SÜTUN İÇİN en az 1 öneri: Histogram veya Box Plot
2. HER KATEGORİK SÜTUN İÇİN en az 1 öneri: Bar Chart veya Pie Chart
3. Toplam öneri sayısı = (Sayısal sütun sayısı × 1) + (Kategorik sütun sayısı × 1) + (İlişkisel analizler için 1-2 ek öneri)
4. Her öneride MUTLAKA column parametresini belirt (hangi sütun için olduğunu)

KURALLAR:
1. visualization_type: SADECE İngilizce (örn: "Histogram", "Box Plot", "Scatter Plot", "Correlation Matrix", "Bar Chart", "Pie Chart")
2. reason: SADECE düz Türkçe metin, HTML/Markdown YOK
3. analysis_level: "Temel" veya "Orta" (Gelişmiş seviye önerileri VERME)
4. column: MUTLAKA ilgili sütun adını belirt (her öneri bir sütun için olmalı)
5. Sayısal sütunlar için: Histogram (dağılım için), Box Plot (outlier için) öner
6. Kategorik sütunlar için: Bar Chart (frekans için), Pie Chart (oran için) öner
7. İlişkisel analizler için: Scatter Plot (2 sayısal sütun arası), Correlation Matrix (tüm sayısal sütunlar) öner

ÖRNEK: Eğer 5 sayısal ve 3 kategorik sütun varsa, en az 8 öneri ver (her sütun için 1).

ŞİMDİ suggest_visualizations FONKSİYONUNU ÇAĞIR ve HER SÜTUN İÇİN ÖNERİ VER.
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

