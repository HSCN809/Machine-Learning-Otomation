"""System prompts for Data Preprocessing LLM enhancements."""

import numpy as np

PREPROCESSING_SYSTEM_PROMPT = """Sen bir veri bilimi uzmanısın ve veri ön işleme konusunda deneyimlisin.
Kullanıcıya Türkçe, anlaşılır ve uygulanabilir öneriler sunmalısın.
Kısa ve öz cümleler kullan - uzun paragraflar yazma.

Görevin: Veri ön işleme adımlarını önermek, eksik değerler, encoding, scaling, outlier ve feature engineering işlemlerini yorumlamak.

KRİTİK KURAL: Her sütun için TEKER TEKER ayrı öneri oluşturmalısın. Bir öneride birden fazla sütun BİRLİKTE olmamalı. Her sütun için ayrı bir öneri objesi oluştur.

ENCODING İÇİN ÖZEL KURAL: Encoding adımında, listelenen TÜM kategorik sütunlar için MUTLAKA öneri oluşturmalısın. Hiçbir sütunu atlayamazsın. Eğer 5 kategorik sütun varsa, MUTLAKA 5 öneri oluşturmalısın. Eksik öneri kabul edilemez!

KRİTİK: Function calling kullanırken TÜM metin alanlarında SADECE düz metin yaz. HTML tag'leri, attribute'ları, Markdown formatlaması ASLA KULLANMA.
"""


def get_preprocessing_suggestion_prompt(
    data_summary: dict,
    numeric_columns: list,
    categorical_columns: list,
    step_type: str,
    analysis_level: str = 'Temel',
    detection_method: str = None
) -> str:
    """
    Generate prompt for preprocessing suggestions based on step type.
    
    Args:
        data_summary: Data summary dictionary
        numeric_columns: List of numeric column names
        categorical_columns: List of categorical column names
        step_type: Type of preprocessing step ('missing_values', 'encoding', 'scaling', 'outlier', 'feature_engineering')
        analysis_level: Analysis level ('Temel', 'Orta', 'Gelişmiş')
        
    Returns:
        Formatted prompt string
    """
    step_names = {
        'missing_values': 'Eksik Değerler',
        'encoding': 'Encoding',
        'scaling': 'Scaling/Normalization',
        'outlier': 'Outlier Handling',
        'feature_engineering': 'Feature Engineering'
    }
    
    step_name = step_names.get(step_type, step_type)
    
    prompt = f"""VERİ SETİ BİLGİLERİ:
- Satır: {data_summary.get('shape', {}).get('rows', 0):,}
- Sütun: {data_summary.get('shape', {}).get('columns', 0)}
- Sayısal: {len(numeric_columns)} ({', '.join(numeric_columns[:5])}{'...' if len(numeric_columns) > 5 else ''})
- Kategorik: {len(categorical_columns)} ({', '.join(categorical_columns[:5])}{'...' if len(categorical_columns) > 5 else ''})
- Eksik Değer: %{data_summary.get('missing_values', {}).get('missing_percentage', 0):.1f}
- Analiz Seviyesi: {analysis_level}

GÖREV: Bu veri seti için {step_name} adımına uygun ön işleme önerileri sun.

ADIM TİPİ: {step_type.upper()}

KURALLAR:
1. preprocessing_type: "{step_type}" olmalı (sadece bu adım için öneriler)
2. method: İngilizce teknik terim kullan (örn: "mean", "one_hot", "standard_scaler", "iqr", "polynomial")
3. reason: SADECE düz Türkçe metin, HTML/Markdown YOK
4. priority: "yüksek", "orta" veya "düşük"
5. analysis_level: "Temel", "Orta" veya "Gelişmiş"
6. columns: İlgili sütun adları (array)

{step_type.upper()} İÇİN ÖNERİLER:
"""
    
    if step_type == 'missing_values':
        # Get columns with missing values from data summary
        columns_with_missing = data_summary.get('missing_values', {}).get('columns_with_missing', [])
        missing_by_column = data_summary.get('missing_values', {}).get('missing_by_column', {})
        missing_percentage_by_column = data_summary.get('missing_values', {}).get('missing_percentage_by_column', {})
        
        # Build column details string
        column_details = []
        for col in columns_with_missing:
            missing_count = missing_by_column.get(col, 0)
            missing_pct = missing_percentage_by_column.get(col, 0)
            col_type = 'Sayısal' if col in numeric_columns else 'Kategorik'
            column_details.append(f"{col} ({col_type}, {missing_count} eksik, %{missing_pct:.1f})")
        
        prompt += f"""
KRİTİK KURALLAR - MUTLAKA UYULMALI:

1. METHOD ALANI İÇİN SADECE ŞU DEĞERLERİ KULLAN (BAŞKA HİÇBİR ŞEY DEĞİL):
   SAYISAL SÜTUNLAR İÇİN (Float, Integer):
   - "mean" (ortalama ile doldur)
   - "median" (medyan ile doldur)
   - "interpolation" (interpolasyon ile doldur)
   - "knn" (K-NN algoritması ile doldur)
   
   KATEGORİK SÜTUNLAR İÇİN (Object, Category):
   - "mode" (en sık görülen değer ile doldur)
   - "forward_fill" (önceki değer ile doldur)
   - "backward_fill" (sonraki değer ile doldur)

2. YASAK YÖNTEMLER - ASLA KULLANMA:
   ❌ "most_frequent" → "mode" kullan
   ❌ "constant" → "mean" veya "mode" kullan
   ❌ "fill_with_constant" → "mean" veya "mode" kullan
   ❌ "zero" → "mean" veya "median" kullan
   ❌ "ffill" → "forward_fill" kullan
   ❌ "bfill" → "backward_fill" kullan
   ❌ "fillna" → uygun yöntem kullan
   ❌ Başka hiçbir isim uydurma!

3. SÜTUN SEÇİMİ - EKSİK DEĞER İÇEREN SÜTUNLAR:
{chr(10).join(f"   - {detail}" for detail in column_details) if column_details else "   - Eksik değer içeren sütun yok"}
   
   ⚠️⚠️⚠️ KRİTİK KURAL - MUTLAKA UYULMALI ⚠️⚠️⚠️
   
   EKSİK DEĞER İÇEREN HER BİR SÜTUN İÇİN TEKER TEKER AYRI ÖNERİ VERMELİSİN!
   
   Yukarıda listelenen TÜM sütunlar için TEKER TEKER öneri oluştur:
   {chr(10).join(f"   ✓ {col} sütunu için AYRI bir öneri VERİLMELİ" for col in columns_with_missing) if columns_with_missing else "   - Eksik değer içeren sütun yok"}
   
   ÖNEMLİ KURALLAR - MUTLAKA UYUL:
   - Yukarıdaki listede kaç sütun varsa, TAM O KADAR öneri oluşturmalısın
   - Her sütun için TEK BİR öneri oluştur (her öneride columns array'inde SADECE 1 sütun olmalı)
   - Hiçbir sütunu atlama, hepsini kapsamalısın
   - Bir öneride birden fazla sütun BİRLİKTE olmamalı - her sütun için ayrı öneri
   - Her sütun için en uygun yöntemi seç
   
   ÖRNEK FORMAT - Eğer {len(columns_with_missing)} sütun varsa, MUTLAKA {len(columns_with_missing)} AYRI öneri oluştur:
{chr(10).join(f"   Öneri {i+1}: {{\"columns\": [\"{col}\"], \"method\": \"...\", ...}}  ← Sadece {col}" for i, col in enumerate(columns_with_missing[:3])) if columns_with_missing else "   - Eksik değer içeren sütun yok"}
   
   YANLIŞ FORMAT (ASLA YAPMA):
   ❌ {{"columns": ["{columns_with_missing[0] if columns_with_missing else 'Sütun1'}", "{columns_with_missing[1] if len(columns_with_missing) > 1 else 'Sütun2'}"], "method": "mean", ...}}  ← Birden fazla sütun BİRLİKTE
   
   DOĞRU FORMAT:
{chr(10).join(f"   ✅ {{\"columns\": [\"{col}\"], \"method\": \"...\", ...}}  ← Sadece {col}" for col in columns_with_missing[:2]) if columns_with_missing else "   ✅ Her sütun için ayrı öneri"}

4. YÖNTEM-SÜTUN EŞLEŞMESİ:
   - Sayısal sütun (Float/Integer) → mean, median, interpolation, knn, drop
   - Kategorik sütun (Object/Category) → mode, forward_fill, backward_fill, drop
   - ⚠️ KRİTİK: Eksik değer yüzdesi >50% ise MUTLAKA "drop" öner!
   - Eksik değer yüzdesi >50% olan sütunlar için drop dışında başka yöntem önerme
   - Eksik değer yüzdesi ≤50% ise uygun doldurma yöntemi öner (mean, median, mode, vb.)

5. ÖNCELİK:
   - Eksik değer yüzdesi >50% ise "yüksek"
   - Eksik değer yüzdesi 10-50% ise "orta"
    - Eksik değer yüzdesi <10% ise "düşük"
"""
    elif step_type == 'encoding':
        # Build column details string
        column_details = []
        for col in categorical_columns:
            unique_count = data_summary.get('categorical_columns', {}).get(col, {}).get('unique_count', 'N/A')
            cardinality = data_summary.get('categorical_columns', {}).get(col, {}).get('cardinality', 'N/A')
            column_details.append(f"{col} (unique: {unique_count}, cardinality: {cardinality})")
        
        prompt += f"""
KRİTİK KURALLAR - MUTLAKA UYULMALI:

1. METHOD ALANI İÇİN SADECE ŞU DEĞERLERİ KULLAN (BAŞKA HİÇBİR ŞEY DEĞİL):
   - "label_encoding" (Label Encoding - her kategoriye benzersiz tam sayı)
   - "one_hot_encoding" (One-Hot Encoding - her kategori için binary sütun)
   - "ordinal_encoding" (Ordinal Encoding - özel sıralama ile)
   - "binary_encoding" (Binary Encoding - binary formatta kodlama)
   - "frequency_encoding" (Frequency Encoding - frekans değerleri ile)

2. YÖNTEM SEÇİMİ KURALLARI:
   - Düşük cardinality (≤10 unique değer): "one_hot_encoding" veya "label_encoding"
   - Yüksek cardinality (>10 unique değer): "binary_encoding" veya "frequency_encoding"
   - Sıralı veriler (eğitim seviyesi, derecelendirme): "ordinal_encoding" veya "label_encoding"
   - Nominal veriler (şehir, renk, kategori): "one_hot_encoding" veya "binary_encoding"
   - Ağaç tabanlı modeller: "label_encoding" uygun
   - Doğrusal modeller: "one_hot_encoding" uygun

3. SÜTUN SEÇİMİ - KATEGORİK SÜTUNLAR:
   Kategorik sütunlar ({len(categorical_columns)} adet): {', '.join(categorical_columns) if categorical_columns else 'Yok'}
   
   SÜTUN DETAYLARI (Her sütun için unique değer sayısı ve cardinality):
{chr(10).join(f"   - {detail}" for detail in column_details) if column_details else "   - Kategorik sütun yok"}
   
   ⚠️⚠️⚠️ KRİTİK KURAL - MUTLAKA UYULMALI ⚠️⚠️⚠️
   
   KATEGORİK SÜTUNLARIN HER BİRİ İÇİN TEKER TEKER AYRI ÖNERİ VERMELİSİN!
   
   Yukarıda listelenen TÜM kategorik sütunlar için TEKER TEKER öneri oluştur:
{chr(10).join(f"   ✓ {col} sütunu için AYRI bir öneri VERİLMELİ" for col in categorical_columns) if categorical_columns else "   - Kategorik sütun yok"}
   
   ÖNEMLİ KURALLAR - MUTLAKA UYUL:
   - Yukarıdaki listede kaç kategorik sütun varsa, TAM O KADAR öneri oluşturmalısın
   - Her sütun için TEK BİR öneri oluştur (her öneride columns array'inde SADECE 1 sütun olmalı)
   - Hiçbir sütunu atlama, hepsini kapsamalısın
   - Bir öneride birden fazla sütun BİRLİKTE olmamalı - her sütun için ayrı öneri
   - Her sütun için en uygun yöntemi seç (unique değer sayısına göre)
   
   ÖRNEK FORMAT - Eğer {len(categorical_columns)} kategorik sütun varsa, MUTLAKA {len(categorical_columns)} AYRI öneri oluştur:
{chr(10).join(f"   Öneri {i+1}: {{\"columns\": [\"{col}\"], \"method\": \"label_encoding\" veya \"one_hot_encoding\" veya \"ordinal_encoding\" veya \"binary_encoding\" veya \"frequency_encoding\", ...}}  ← Sadece {col}" for i, col in enumerate(categorical_columns[:3])) if categorical_columns else "   - Kategorik sütun yok"}
   
   YANLIŞ FORMAT (ASLA YAPMA):
   ❌ {{"columns": ["{categorical_columns[0] if categorical_columns else 'Sütun1'}", "{categorical_columns[1] if len(categorical_columns) > 1 else 'Sütun2'}"], "method": "one_hot_encoding", ...}}  ← Birden fazla sütun BİRLİKTE
   
   DOĞRU FORMAT:
{chr(10).join(f"   ✅ {{\"columns\": [\"{col}\"], \"method\": \"one_hot_encoding\", ...}}  ← Sadece {col}" for col in categorical_columns[:2]) if categorical_columns else "   ✅ Her sütun için ayrı öneri"}

4. ÖNCELİK:
   - Çok sayıda kategorik sütun varsa (>5) "yüksek"
   - Orta sayıda kategorik sütun varsa (2-5) "orta"
   - Az sayıda kategorik sütun varsa (1-2) "düşük"
"""
    elif step_type == 'scaling':
        # Get numeric column statistics from data summary
        numeric_stats = data_summary.get('numeric_statistics', {})
        # Get detailed scaling statistics (CV, Median, Outlier %, IQR, Q1, Q3)
        scaling_stats = data_summary.get('scaling_statistics', {})
        
        # Build column details string with all metrics
        column_details = []
        for col in numeric_columns:
            # Basic stats from numeric_statistics
            mean_val = numeric_stats.get('mean', {}).get(col, 'N/A')
            std_val = numeric_stats.get('std', {}).get(col, 'N/A')
            min_val = numeric_stats.get('min', {}).get(col, 'N/A')
            max_val = numeric_stats.get('max', {}).get(col, 'N/A')
            skewness = numeric_stats.get('skewness', {}).get(col, 'N/A')
            
            # Detailed stats from scaling_statistics
            col_stats = scaling_stats.get(col, {})
            median_val = col_stats.get('median', 'N/A')
            q1 = col_stats.get('q1', 'N/A')
            q3 = col_stats.get('q3', 'N/A')
            iqr = col_stats.get('iqr', 'N/A')
            outlier_pct = col_stats.get('outlier_percentage', 'N/A')
            
            # Calculate CV
            cv = 'N/A'
            if isinstance(mean_val, (int, float)) and isinstance(std_val, (int, float)) and mean_val != 0:
                cv = std_val / mean_val
            
            # Format values
            mean_str = f"{mean_val:.2f}" if isinstance(mean_val, (int, float)) else str(mean_val)
            median_str = f"{median_val:.2f}" if isinstance(median_val, (int, float)) else str(median_val)
            std_str = f"{std_val:.2f}" if isinstance(std_val, (int, float)) else str(std_val)
            cv_str = f"{cv:.2f}" if isinstance(cv, (int, float)) and not np.isinf(cv) else str(cv)
            min_str = f"{min_val:.2f}" if isinstance(min_val, (int, float)) else str(min_val)
            max_str = f"{max_val:.2f}" if isinstance(max_val, (int, float)) else str(max_val)
            q1_str = f"{q1:.2f}" if isinstance(q1, (int, float)) else str(q1)
            q3_str = f"{q3:.2f}" if isinstance(q3, (int, float)) else str(q3)
            iqr_str = f"{iqr:.2f}" if isinstance(iqr, (int, float)) else str(iqr)
            outlier_pct_str = f"{outlier_pct:.2f}%" if isinstance(outlier_pct, (int, float)) else str(outlier_pct)
            skew_str = f"{skewness:.2f}" if isinstance(skewness, (int, float)) else str(skewness)
            
            column_details.append(f"{col} (mean: {mean_str}, median: {median_str}, std: {std_str}, CV: {cv_str}, min: {min_str}, max: {max_str}, Q1: {q1_str}, Q3: {q3_str}, IQR: {iqr_str}, outlier%: {outlier_pct_str}, skewness: {skew_str})")
        
        prompt += f"""
KRİTİK KURALLAR - MUTLAKA UYULMALI:

1. METHOD ALANI İÇİN SADECE ŞU DEĞERLERİ KULLAN (BAŞKA HİÇBİR ŞEY DEĞİL):
   - "standard_scaler" (Standard Scaling - Z-score normalization, mean=0, std=1)
   - "minmax_scaler" (Min-Max Scaling - 0-1 aralığına ölçekleme)
   - "robust_scaler" (Robust Scaling - median ve IQR kullanır, aykırı değerlere dayanıklı)
   - "normalizer" (Normalization - satır bazlı normalizasyon, l2 norm)
   - "power_transform" (Power Transformation - normal dağılıma yaklaştırır, Yeo-Johnson veya Box-Cox)

2. YÖNTEM SEÇİMİ KURALLARI - KOŞUL KOMBİNASYONLARI (IF-THEN KURALLARI):
   
   ⚠️ ÖNEMLİ: Her sütun için AŞAĞIDAKİ KOŞUL KOMBİNASYONLARINI sırayla kontrol et ve İLK UYAN KURALI uygula:
   
   KURAL 1 - AYKIRI DEĞER + ÇARPIKLIK KOMBİNASYONU (EN ÖNCELİKLİ):
   IF outlier % > 10% AND (skewness > 1.5 OR skewness < -1.5):
      → "power_transform" kullan (önce çarpıklığı düzelt, aykırı değerler için de uygun)
   ELSE IF outlier % > 10%:
      → "robust_scaler" kullan (aykırı değerlere dayanıklı, standard_scaler KULLANMA!)
   
   KURAL 2 - ÇARPIKLIK KONTROLÜ (Aykırı değer yoksa veya azsa):
   IF outlier % <= 10% AND (skewness > 1.5 OR skewness < -1.5):
      → "power_transform" kullan (normal dağılıma yaklaştır, standard_scaler KULLANMA!)
   ELSE IF outlier % <= 10% AND (skewness > 1.0 OR skewness < -1.0):
      → "power_transform" veya "robust_scaler" düşün
   
   KURAL 3 - ÖLÇEK FARKI + NEGATİF DEĞER KOMBİNASYONU:
   IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND CV > 1.0 AND min < 0:
      → "standard_scaler" kullan (negatif değerler için minmax uygun değil)
   ELSE IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND CV > 1.0 AND min >= 0 AND max < 1000:
      → "minmax_scaler" kullan (0-1 aralığına ölçekle)
   ELSE IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND CV > 1.0 AND min >= 0:
      → "standard_scaler" veya "minmax_scaler" (büyük değerler için standard daha iyi)
   
   KURAL 4 - MEDIAN-MEAN FARKI (Aykırı değer işareti):
   IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND |median - mean| / std > 0.5:
      → "robust_scaler" düşün (median daha güvenilir, aykırı değer işareti)
   
   KURAL 5 - IQR DAĞILIMI:
   IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND IQR / (max - min) > 0.5:
      → "standard_scaler" uygun (yoğun veri, normal dağılıma yakın)
   ELSE IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND IQR / (max - min) < 0.2:
      → "robust_scaler" düşün (dağınık veri)
   
   KURAL 6 - VARSayILAN (Yukarıdakilerin hiçbiri uymuyorsa):
   IF outlier % <= 5% AND skewness >= -0.5 AND skewness <= 0.5 AND CV <= 1.0:
      → "standard_scaler" kullan (normal dağılım, az aykırı değer, düşük değişkenlik)
   ELSE IF min >= 0 AND max <= 1:
      → "minmax_scaler" düşün (zaten küçük aralıkta, ama genelde binary sütunlar filtrelenmiş)
   ELSE:
      → "standard_scaler" (genel varsayılan)
   
   ⚠️⚠️⚠️ KRİTİK UYARI ⚠️⚠️⚠️:
   - Her sütun için YUKARIDAKİ KURALLARI SIRAYLA kontrol et
   - İLK UYAN KURALI uygula ve DUR
   - Tüm sütunlar için aynı yöntemi (standard_scaler) önerme!
   - Her sütunun metriklerine göre FARKLI yöntemler seç

3. SÜTUN SEÇİMİ - SAYISAL SÜTUNLAR:
   Sayısal sütunlar ({len(numeric_columns)} adet): {', '.join(numeric_columns) if numeric_columns else 'Yok'}
   
   SÜTUN DETAYLARI (Her sütun için istatistikler):
{chr(10).join(f"   - {detail}" for detail in column_details) if column_details else "   - Sayısal sütun yok"}
   
   ⚠️⚠️⚠️ KRİTİK KURAL - MUTLAKA UYULMALI ⚠️⚠️⚠️
   
   SAYISAL SÜTUNLARIN HER BİRİ İÇİN TEKER TEKER AYRI ÖNERİ VERMELİSİN!
   
   Yukarıda listelenen TÜM sayısal sütunlar için TEKER TEKER öneri oluştur:
{chr(10).join(f"   ✓ {col} sütunu için AYRI bir öneri VERİLMELİ" for col in numeric_columns) if numeric_columns else "   - Sayısal sütun yok"}
   
   ÖNEMLİ KURALLAR - MUTLAKA UYUL:
   - Yukarıdaki listede kaç sayısal sütun varsa, TAM O KADAR öneri oluşturmalısın
   - Her sütun için TEK BİR öneri oluştur (her öneride columns array'inde SADECE 1 sütun olmalı)
   - Hiçbir sütunu atlama, hepsini kapsamalısın
   - Bir öneride birden fazla sütun BİRLİKTE olmamalı - her sütun için ayrı öneri
   - Her sütun için en uygun yöntemi seç (istatistiklere göre)
   
   ÖRNEK FORMAT - Eğer {len(numeric_columns)} sayısal sütun varsa, MUTLAKA {len(numeric_columns)} AYRI öneri oluştur:
{chr(10).join(f"   Öneri {i+1}: {{\"columns\": [\"{col}\"], \"method\": \"standard_scaler\" veya \"minmax_scaler\" veya \"robust_scaler\" veya \"normalizer\" veya \"power_transform\", ...}}  ← Sadece {col}" for i, col in enumerate(numeric_columns[:3])) if numeric_columns else "   - Sayısal sütun yok"}
   
   YANLIŞ FORMAT (ASLA YAPMA):
   ❌ {{"columns": ["{numeric_columns[0] if numeric_columns else 'Sütun1'}", "{numeric_columns[1] if len(numeric_columns) > 1 else 'Sütun2'}"], "method": "standard_scaler", ...}}  ← Birden fazla sütun BİRLİKTE
   
   DOĞRU FORMAT:
{chr(10).join(f"   ✅ {{\"columns\": [\"{col}\"], \"method\": \"standard_scaler\", ...}}  ← Sadece {col}" for col in numeric_columns[:2]) if numeric_columns else "   ✅ Her sütun için ayrı öneri"}

4. BINARY SÜTUN KONTROLÜ - KRİTİK KURAL:
   - Min=0 ve Max=1 olan sütunlar için ASLA öneri oluşturma
   - Bu sütunlar zaten ölçeklenmiş (one-hot/binary encoding sonrası)
   - Binary sütunlar için scaling gereksiz ve hatalı sonuçlar verebilir
   - Eğer bir sütunun min=0, max=1 ise, o sütunu ATLA ve öneri oluşturma
   - NOT: Bu sütunlar zaten LLM'e gönderilmedi (frontend'de filtrelendi), ama yine de dikkatli ol

5. YÖNTEM SEÇİMİ - DETAYLI METRİKLERE GÖRE (KOŞUL KOMBİNASYONLARI):
   
   ⚠️⚠️⚠️ KRİTİK: Her sütun için AŞAĞIDAKİ KOŞUL KOMBİNASYONLARINI sırayla kontrol et ve İLK UYAN KURALI uygula ⚠️⚠️⚠️
   
   KOMBİNASYON 1 - AYKIRI DEĞER + ÇARPIKLIK:
   IF outlier % > 10% AND (skewness > 1.5 OR skewness < -1.5):
      → "power_transform" (hem aykırı değer hem çarpıklık var)
   ELSE IF outlier % > 10%:
      → "robust_scaler" (standard_scaler KULLANMA!)
   
   KOMBİNASYON 2 - ÇARPIKLIK (Aykırı değer az):
   IF outlier % <= 10% AND (skewness > 1.5 OR skewness < -1.5):
      → "power_transform" (standard_scaler KULLANMA!)
   ELSE IF outlier % <= 10% AND (skewness > 1.0 OR skewness < -1.0):
      → "power_transform" veya "robust_scaler"
   
   KOMBİNASYON 3 - ÖLÇEK FARKI + NEGATİF DEĞER:
   IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND CV > 1.0 AND min < 0:
      → "standard_scaler" (negatif değerler için minmax uygun değil)
   ELSE IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND CV > 1.0 AND min >= 0 AND max < 1000:
      → "minmax_scaler" (0-1 aralığına ölçekle)
   ELSE IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND CV > 1.0 AND min >= 0:
      → "standard_scaler" veya "minmax_scaler"
   
   KOMBİNASYON 4 - MEDIAN-MEAN FARKI:
   IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND |median - mean| / std > 0.5:
      → "robust_scaler" (median daha güvenilir)
   
   KOMBİNASYON 5 - IQR DAĞILIMI:
   IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND IQR / (max - min) > 0.5:
      → "standard_scaler" (yoğun veri)
   ELSE IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND IQR / (max - min) < 0.2:
      → "robust_scaler" (dağınık veri)
   
   KOMBİNASYON 6 - VARSayILAN:
   IF outlier % <= 5% AND skewness >= -0.5 AND skewness <= 0.5 AND CV <= 1.0:
      → "standard_scaler" (normal dağılım, az aykırı değer)
   ELSE:
      → "standard_scaler" (genel varsayılan)

6. ÖNCELİK:
   - CV > 1.0 ise (yüksek değişkenlik) "yüksek"
   - Farklı ölçeklerde sayısal sütunlar varsa (ör: bir sütun 0-1, diğeri 0-1000) "yüksek"
   - Çarpık veriler varsa (skewness >1 veya <-1) "yüksek"
   - Aykırı değer içeren sütunlar varsa (outlier % > 10%) "orta"
   - Normal dağılıma yakın sütunlar için "düşük"
"""
    elif step_type == 'outlier':
        # Get columns with outliers from data summary
        columns_with_outliers = data_summary.get('outliers', {}).get('columns_with_outliers', [])
        outliers_by_column = data_summary.get('outliers', {}).get('outliers_by_column', {})
        
        # Add detection method info if provided
        method_info = ""
        if detection_method:
            method_names = {
                'iqr': 'IQR (Interquartile Range)',
                'zscore': 'Z-Score'
            }
            method_name = method_names.get(detection_method, detection_method.upper())
            method_info = f"\n⚠️ ÖNEMLİ: Şu anda kullanılan tespit yöntemi: {method_name} ({detection_method})\nSADECE bu yöntem için öneri oluşturmalısın!\n"
        
        prompt += f"""
KRİTİK KURAL: SADECE aykırı değer içeren sütunlar için TEKER TEKER AYRI öneri oluşturmalısın.
{method_info}
Aykırı değer içeren sütunlar ({len(columns_with_outliers)} adet): {', '.join(columns_with_outliers) if columns_with_outliers else 'Yok'}

1. METHOD ALANI İÇİN SADECE ŞU DEĞERLERİ KULLAN (BAŞKA HİÇBİR ŞEY DEĞİL):
   - "iqr_remove" veya "iqr_cap" (Interquartile Range - IQR yöntemi)
   - "zscore_remove" veya "zscore_cap" (Z-Score yöntemi)

2. YÖNTEM SEÇİMİ KURALLARI:
   - Basit ve hızlı için: "iqr_remove", "iqr_cap", "zscore_remove", "zscore_cap"
   - IQR: Normal dağılımlı veriler için uygun, hızlı
   - Z-score: Normal dağılımlı veriler için uygun, ortalama ve standart sapma kullanır
   {f"- ⚠️ ÖNEMLİ: Şu anda {detection_method} yöntemi kullanılıyor. Önerilerinde SADECE {detection_method}_remove veya {detection_method}_cap kullanmalısın!" if detection_method else ""}

3. İŞLEM TİPİ (ACTION) - METHOD İÇİNDE BELİRTİLMELİ:
   - "_remove": Aykırı değerleri içeren satırları sil (aykırı değer yüzdesi düşükse)
   - "_cap": Aykırı değerleri sınırlara çek (aykırı değer yüzdesi yüksekse veya veri kaybı istenmiyorsa)
   - ÖRNEK: "iqr_remove", "iqr_cap", "zscore_remove", "zscore_cap"

4. ÖNCELİK HESAPLAMA:
   - Aykırı değer yüzdesi >20% ise "yüksek"
   - Aykırı değer yüzdesi 5-20% ise "orta"
   - Aykırı değer yüzdesi <5% ise "düşük"

5. SÜTUN SEÇİMİ:
   - SADECE aykırı değer içeren sütunlar için öneri oluştur (yukarıda listelenen sütunlar)
   - Aykırı değer içermeyen sütunlar için ASLA öneri oluşturma
   - Her öneride columns array'inde SADECE 1 sütun olmalı
   - Bir öneride birden fazla sütun BİRLİKTE olmamalı

ÖRNEK FORMAT ({len(columns_with_outliers)} aykırı değer içeren sütun varsa):
{chr(10).join(f"- Öneri {i+1}: {{\"columns\": [\"{col}\"], \"method\": \"iqr_remove\" veya \"iqr_cap\", ...}}  ← Sadece {col}" for i, col in enumerate(columns_with_outliers[:3])) if columns_with_outliers else "- Aykırı değer içeren sütun yok"}
"""
    elif step_type == 'feature_engineering':
        # Feature engineering LLM prompts removed - will be added back later if needed
        prompt += """
KRİTİK KURAL: Feature engineering için LLM önerileri şu an devre dışı bırakılmıştır.
"""
    
    if step_type == 'missing_values' and columns_with_missing:
        prompt += f"""
⚠️⚠️⚠️ SON KONTROL - MUTLAKA OKU ⚠️⚠️⚠️:

Eksik değer içeren sütun sayısı: {len(columns_with_missing)}
Sütunlar: {', '.join(columns_with_missing)}

SENİN GÖREVİN: Bu {len(columns_with_missing)} sütunun HER BİRİ için TEKER TEKER AYRI öneri oluşturmak!

ÖNERİ SAYISI KONTROLÜ:
- Eğer {len(columns_with_missing)} sütun varsa, MUTLAKA TAM {len(columns_with_missing)} öneri oluştur
- Her sütun için TAM 1 öneri (her öneride columns array'inde SADECE 1 sütun)
- Eksik sütun bırakma, hepsini kapsa!
- Bir öneride birden fazla sütun BİRLİKTE olmamalı

ZORUNLU FORMAT - HER SÜTUN İÇİN AYRI ÖNERİ:
{chr(10).join(f"- Öneri {i+1}: columns: [\"{col}\"], method: \"...\"  ← SADECE {col} sütunu" for i, col in enumerate(columns_with_missing)) if columns_with_missing else "- Eksik değer içeren sütun yok"}

ÖRNEK ÇIKTI ({len(columns_with_missing)} sütun varsa):
{chr(10).join(f"- Öneri {i+1}: {{\"columns\": [\"{col}\"], \"method\": \"...\", \"reason\": \"...\", ...}}  ← Sadece {col}" for i, col in enumerate(columns_with_missing)) if columns_with_missing else "- Eksik değer içeren sütun yok"}

MUTLAKA suggest_preprocessing_steps fonksiyonunu çağırarak TÜM sütunlar için TEKER TEKER önerileri sun. Function calling kullanmadan cevap verme.
"""
    if step_type != 'missing_values':
        # For other step types, add dynamic examples
        if step_type == 'encoding' and categorical_columns:
            # Build detailed column list with unique counts
            column_details_list = []
            for col in categorical_columns:
                unique_count = data_summary.get('categorical_columns', {}).get(col, {}).get('unique_count', 'N/A')
                cardinality = data_summary.get('categorical_columns', {}).get(col, {}).get('cardinality', 'N/A')
                column_details_list.append(f"{col} (unique: {unique_count}, cardinality: {cardinality})")
            
            prompt += f"""
⚠️⚠️⚠️ SON KONTROL - MUTLAKA OKU ⚠️⚠️⚠️:

Kategorik sütun sayısı: {len(categorical_columns)}
Sütunlar ve detayları:
{chr(10).join(f"   {i+1}. {detail}" for i, detail in enumerate(column_details_list)) if column_details_list else "   - Kategorik sütun yok"}

SENİN GÖREVİN: Bu {len(categorical_columns)} sütunun HER BİRİ için TEKER TEKER AYRI öneri oluşturmak!

ZORUNLU FORMAT - HER SÜTUN İÇİN AYRI ÖNERİ (MUTLAKA {len(categorical_columns)} ÖNERİ OLUŞTUR):
{chr(10).join(f"- Öneri {i+1}: {{\"columns\": [\"{col}\"], \"method\": \"label_encoding\" veya \"one_hot_encoding\" veya \"ordinal_encoding\" veya \"binary_encoding\" veya \"frequency_encoding\", \"reason\": \"...\", \"priority\": \"...\", \"analysis_level\": \"...\"}}  ← SADECE {col} sütunu (unique: {data_summary.get('categorical_columns', {}).get(col, {}).get('unique_count', 'N/A')})" for i, col in enumerate(categorical_columns)) if categorical_columns else "- Kategorik sütun yok"}

ÖNEMLİ NOTLAR - MUTLAKA UYUL:
- Her sütun için TAM 1 öneri oluştur (her öneride columns array'inde SADECE 1 sütun)
- TOPLAM ÖNERİ SAYISI: {len(categorical_columns)} (Her sütun için 1 öneri)
- Method: MUTLAKA şu değerlerden biri olmalı:
  * "label_encoding"
  * "one_hot_encoding"
  * "ordinal_encoding"
  * "binary_encoding"
  * "frequency_encoding"
- SADECE "label", "one_hot" gibi kısa formatlar KULLANMA! MUTLAKA tam format kullan!
- Unique değer sayısına göre uygun yöntemi seç:
  * ≤10 unique: "one_hot_encoding" veya "label_encoding"
  * >10 unique: "binary_encoding" veya "frequency_encoding"
- Eksik sütun bırakma, hepsini kapsa!
- Bir öneride birden fazla sütun BİRLİKTE olmamalı

ZORUNLU ÖNERİ LİSTESİ (MUTLAKA TÜMÜNÜ OLUŞTUR):
{chr(10).join(f"   {i+1}. {col} sütunu için öneri oluştur (unique: {data_summary.get('categorical_columns', {}).get(col, {}).get('unique_count', 'N/A')}, cardinality: {data_summary.get('categorical_columns', {}).get(col, {}).get('cardinality', 'N/A')})" for i, col in enumerate(categorical_columns)) if categorical_columns else "   - Kategorik sütun yok"}

MUTLAKA suggest_preprocessing_steps fonksiyonunu çağırarak TÜM {len(categorical_columns)} sütun için TEKER TEKER önerileri sun. Function calling kullanmadan cevap verme. Eğer {len(categorical_columns)} öneri oluşturmazsan, görev başarısız sayılacak!
"""
        elif step_type == 'outlier':
            # Get columns with outliers from data summary
            columns_with_outliers = data_summary.get('outliers', {}).get('columns_with_outliers', [])
            if columns_with_outliers:
                prompt += f"""
⚠️⚠️⚠️ SON KONTROL - MUTLAKA OKU ⚠️⚠️⚠️:

Aykırı değer içeren sütun sayısı: {len(columns_with_outliers)}
Sütunlar: {', '.join(columns_with_outliers)}

SENİN GÖREVİN: Bu {len(columns_with_outliers)} aykırı değer içeren sütunun HER BİRİ için TEKER TEKER AYRI öneri oluşturmak!

ZORUNLU FORMAT - HER SÜTUN İÇİN AYRI ÖNERİ:
{chr(10).join(f"- Öneri {i+1}: {{\"columns\": [\"{col}\"], \"method\": \"iqr_remove\" veya \"iqr_cap\" veya \"zscore_remove\" veya \"zscore_cap\", ...}}  ← SADECE {col} sütunu" for i, col in enumerate(columns_with_outliers)) if columns_with_outliers else "- Aykırı değer içeren sütun yok"}

ÖNEMLİ NOTLAR:
- Her sütun için TAM 1 öneri oluştur (her öneride columns array'inde SADECE 1 sütun)
- Method: MUTLAKA "detection_method_action" formatında olmalı:
  * "iqr_remove" veya "iqr_cap"
  * "zscore_remove" veya "zscore_cap"
- SADECE "iqr", "zscore" gibi formatlar KULLANMA! MUTLAKA "_remove" veya "_cap" ekle!
- Eksik sütun bırakma, hepsini kapsa!
- Bir öneride birden fazla sütun BİRLİKTE olmamalı

MUTLAKA suggest_preprocessing_steps fonksiyonunu çağırarak TÜM sütunlar için TEKER TEKER önerileri sun. Function calling kullanmadan cevap verme.
"""
        elif step_type == 'scaling' and numeric_columns:
            # Get numeric column statistics from data summary
            numeric_stats = data_summary.get('numeric_statistics', {})
            # Get detailed scaling statistics
            scaling_stats = data_summary.get('scaling_statistics', {})
            
            # Build detailed column list with all metrics
            column_details_list = []
            for col in numeric_columns:
                # Basic stats
                mean_val = numeric_stats.get('mean', {}).get(col, 'N/A')
                std_val = numeric_stats.get('std', {}).get(col, 'N/A')
                skewness = numeric_stats.get('skewness', {}).get(col, 'N/A')
                
                # Detailed stats from scaling_statistics
                col_stats = scaling_stats.get(col, {})
                median_val = col_stats.get('median', 'N/A')
                min_val = col_stats.get('min', 'N/A')
                max_val = col_stats.get('max', 'N/A')
                q1 = col_stats.get('q1', 'N/A')
                q3 = col_stats.get('q3', 'N/A')
                iqr = col_stats.get('iqr', 'N/A')
                outlier_pct = col_stats.get('outlier_percentage', 'N/A')
                
                # Calculate CV
                cv = 'N/A'
                if isinstance(mean_val, (int, float)) and isinstance(std_val, (int, float)) and mean_val != 0:
                    cv = std_val / mean_val
                
                # Format values
                mean_str = f"{mean_val:.2f}" if isinstance(mean_val, (int, float)) else str(mean_val)
                median_str = f"{median_val:.2f}" if isinstance(median_val, (int, float)) else str(median_val)
                std_str = f"{std_val:.2f}" if isinstance(std_val, (int, float)) else str(std_val)
                cv_str = f"{cv:.2f}" if isinstance(cv, (int, float)) and not np.isinf(cv) else str(cv)
                min_str = f"{min_val:.2f}" if isinstance(min_val, (int, float)) else str(min_val)
                max_str = f"{max_val:.2f}" if isinstance(max_val, (int, float)) else str(max_val)
                q1_str = f"{q1:.2f}" if isinstance(q1, (int, float)) else str(q1)
                q3_str = f"{q3:.2f}" if isinstance(q3, (int, float)) else str(q3)
                iqr_str = f"{iqr:.2f}" if isinstance(iqr, (int, float)) else str(iqr)
                outlier_pct_str = f"{outlier_pct:.2f}%" if isinstance(outlier_pct, (int, float)) else str(outlier_pct)
                skew_str = f"{skewness:.2f}" if isinstance(skewness, (int, float)) else str(skewness)
                
                column_details_list.append(f"{col} (mean: {mean_str}, median: {median_str}, std: {std_str}, CV: {cv_str}, min: {min_str}, max: {max_str}, Q1: {q1_str}, Q3: {q3_str}, IQR: {iqr_str}, outlier%: {outlier_pct_str}, skewness: {skew_str})")
            
            prompt += f"""
⚠️⚠️⚠️ SON KONTROL - MUTLAKA OKU ⚠️⚠️⚠️:

Sayısal sütun sayısı: {len(numeric_columns)}
Sütunlar ve detayları:
{chr(10).join(f"   {i+1}. {detail}" for i, detail in enumerate(column_details_list)) if column_details_list else "   - Sayısal sütun yok"}

SENİN GÖREVİN: Bu {len(numeric_columns)} sütunun HER BİRİ için TEKER TEKER AYRI öneri oluşturmak!

ZORUNLU FORMAT - HER SÜTUN İÇİN AYRI ÖNERİ (MUTLAKA {len(numeric_columns)} ÖNERİ OLUŞTUR):
{chr(10).join(f"- Öneri {i+1}: {{\"columns\": [\"{col}\"], \"method\": \"standard_scaler\" veya \"minmax_scaler\" veya \"robust_scaler\" veya \"normalizer\" veya \"power_transform\", \"reason\": \"...\", \"priority\": \"...\", \"analysis_level\": \"...\"}}  ← SADECE {col} sütunu" for i, col in enumerate(numeric_columns)) if numeric_columns else "- Sayısal sütun yok"}

ÖNEMLİ NOTLAR - MUTLAKA UYUL:
- Her sütun için TAM 1 öneri oluştur (her öneride columns array'inde SADECE 1 sütun)
- TOPLAM ÖNERİ SAYISI: {len(numeric_columns)} (Her sütun için 1 öneri)
- Method: MUTLAKA şu değerlerden biri olmalı:
  * "standard_scaler"
  * "minmax_scaler"
  * "robust_scaler"
  * "normalizer"
  * "power_transform"
- SADECE "standard", "minmax" gibi kısa formatlar KULLANMA! MUTLAKA tam format kullan!
- İstatistiklere göre uygun yöntemi seç - KOŞUL KOMBİNASYONLARI (IF-THEN KURALLARI):
  
  Her sütun için AŞAĞIDAKİ KOŞULLARI sırayla kontrol et ve İLK UYAN KURALI uygula:
  
  KOMBİNASYON 1: IF outlier % > 10% AND (skewness > 1.5 OR skewness < -1.5) → "power_transform"
  KOMBİNASYON 2: IF outlier % > 10% → "robust_scaler" (standard_scaler KULLANMA!)
  KOMBİNASYON 3: IF outlier % <= 10% AND (skewness > 1.5 OR skewness < -1.5) → "power_transform" (standard_scaler KULLANMA!)
  KOMBİNASYON 4: IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND CV > 1.0 AND min < 0 → "standard_scaler"
  KOMBİNASYON 5: IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND CV > 1.0 AND min >= 0 AND max < 1000 → "minmax_scaler"
  KOMBİNASYON 6: IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND CV > 1.0 AND min >= 0 → "standard_scaler" veya "minmax_scaler"
  KOMBİNASYON 7: IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND |median - mean| / std > 0.5 → "robust_scaler"
  KOMBİNASYON 8: IF outlier % <= 10% AND skewness <= 1.5 AND skewness >= -1.5 AND IQR / (max - min) < 0.2 → "robust_scaler"
  KOMBİNASYON 9: IF outlier % <= 5% AND skewness >= -0.5 AND skewness <= 0.5 AND CV <= 1.0 → "standard_scaler"
  KOMBİNASYON 10: ELSE → "standard_scaler" (genel varsayılan)
  
  ⚠️ ÖNEMLİ: Her sütun için yukarıdaki kombinasyonları sırayla kontrol et. İlk uyan kombinasyonu uygula ve DUR! Tüm sütunlar için aynı yöntemi (standard_scaler) önerme!
- BINARY SÜTUN KONTROLÜ: Min=0 ve Max=1 olan sütunlar zaten filtrelendi, ama yine de dikkatli ol
- Eksik sütun bırakma, hepsini kapsa!
- Bir öneride birden fazla sütun BİRLİKTE olmamalı

ZORUNLU ÖNERİ LİSTESİ (MUTLAKA TÜMÜNÜ OLUŞTUR):
{chr(10).join(f"   {i+1}. {col} sütunu için öneri oluştur (detaylı metrikler yukarıda listelenmiş)" for i, col in enumerate(numeric_columns)) if numeric_columns else "   - Sayısal sütun yok"}

MUTLAKA suggest_preprocessing_steps fonksiyonunu çağırarak TÜM {len(numeric_columns)} sütun için TEKER TEKER önerileri sun. Function calling kullanmadan cevap verme. Eğer {len(numeric_columns)} öneri oluşturmazsan, görev başarısız sayılacak!
"""
        elif step_type == 'feature_engineering':
            # Feature engineering LLM prompts removed - will be added back later if needed
            pass
        else:
            prompt += """
KRİTİK KURAL: Her sütun için TEKER TEKER AYRI öneri oluşturmalısın. Bir öneride birden fazla sütun BİRLİKTE olmamalı.

MUTLAKA suggest_preprocessing_steps fonksiyonunu çağırarak uygun önerileri sun. Function calling kullanmadan cevap verme.
"""
    
    return prompt

