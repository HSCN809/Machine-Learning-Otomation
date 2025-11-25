"""Streamlit page for Model Selection - Step-by-step wizard approach."""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import logging
from datetime import datetime
import re
import plotly.graph_objects as go
import plotly.express as px
from sklearn.metrics import confusion_matrix, roc_curve, auc
import json
import pickle
import io

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Model selection imports
from backend.modules.model_selection.problem_detection import (
    detect_problem_type,
    analyze_target_variable,
    get_problem_type_info,
    validate_target_variable
)

from backend.modules.model_selection.model_recommendation import (
    recommend_models,
    get_model_descriptions,
    analyze_data_for_recommendation
)

from backend.modules.model_selection.model_training import (
    train_model,
    train_multiple_models,
    split_data,
    analyze_training_data,
    check_data_quality
)

from backend.modules.model_selection.model_evaluation import (
    evaluate_classification_model,
    evaluate_regression_model,
    calculate_metrics,
    get_confusion_matrix,
    get_metric_explanations
)

from backend.modules.model_selection.model_interpretation import (
    get_feature_importance,
    calculate_shap_values,
    get_permutation_importance,
    analyze_feature_importance
)

from backend.modules.model_selection.model_comparison import (
    compare_models,
    get_best_model,
    create_comparison_table,
    analyze_model_rankings
)

from backend.modules.model_selection.model_interpretation import (
    get_feature_importance,
    calculate_shap_values,
    get_permutation_importance,
    analyze_feature_importance
)

from backend.modules.data_upload.data_validator import get_data_summary

# Logger setup
logger = logging.getLogger(__name__)

# Hyperparameter optimization removed

# Helper function for parameter descriptions (Markdown format)
def _get_parameter_description(model_name, param_name):
    """Get detailed markdown description for a model parameter."""
    descriptions = {
        'C': """
**Regularization Parametresi**

- **Açıklama:** Modelin overfitting'e karşı ne kadar korunacağını kontrol eder
- **Düşük değerler (örn: 0.001, 0.01):** Daha fazla regularizasyon, daha basit model, daha az overfitting
- **Yüksek değerler (örn: 10, 100):** Daha az regularizasyon, daha karmaşık model, overfitting riski
- **Öneri:** Genellikle logaritmik aralıkta denemek iyidir: [0.001, 0.01, 0.1, 1, 10, 100]
        """,
        'penalty': """
**Regularizasyon Tipi**

- **L1 (Lasso):** Özellik seçimi yapar, bazı katsayıları sıfırlar
- **L2 (Ridge):** Tüm özellikleri tutar, katsayıları küçültür
- **Elastic Net:** L1 ve L2'yi birleştirir
- **Öneri:** L2 genellikle daha iyi performans verir, L1 feature selection gerektiğinde kullanılır
        """,
        'solver': """
**Optimizasyon Algoritması**

- **liblinear:** Küçük veri setleri için, L1/L2 penalty ile uyumlu
- **lbfgs:** Büyük veri setleri için, sadece L2 penalty
- **sag/saga:** Çok büyük veri setleri için
- **Öneri:** Küçük veri için liblinear, büyük veri için lbfgs
        """,
        'n_estimators': """
**Estimator (Ağaç) Sayısı**

- **Açıklama:** Ensemble modelinde kaç ağaç/estimator kullanılacağını belirler
- **Düşük değerler (örn: 50, 100):** Hızlı eğitim ama düşük performans
- **Yüksek değerler (örn: 200, 500):** Daha iyi performans ama yavaş eğitim
- **Öneri:** 100-200 arası genellikle iyi bir denge sağlar
        """,
        'max_depth': """
**Maksimum Ağaç Derinliği**

- **Açıklama:** Ağacın ne kadar derine inebileceğini kontrol eder
- **Düşük değerler (örn: 5, 10):** Basit model, daha az overfitting
- **Yüksek değerler (örn: 20, None):** Karmaşık model, overfitting riski
- **None:** Sınırsız derinlik
- **Öneri:** 10-20 arası genellikle yeterlidir, None yerine sınırlı değer daha iyi
        """,
        'min_samples_split': """
**Minimum Split Örnek Sayısı**

- **Açıklama:** Bir düğümün bölünmesi için gereken minimum örnek sayısı
- **Düşük değerler (örn: 2):** Daha fazla bölünme, karmaşık model
- **Yüksek değerler (örn: 10, 20):** Daha az bölünme, basit model
- **Öneri:** 2-10 arası deneyin, büyük veri setleri için daha yüksek değerler
        """,
        'min_samples_leaf': """
**Minimum Leaf Örnek Sayısı**

- **Açıklama:** Yaprak düğümünde (leaf) olması gereken minimum örnek sayısı
- **Düşük değerler (örn: 1):** Çok detaylı model, overfitting riski
- **Yüksek değerler (örn: 4, 5):** Daha genel model, daha az overfitting
- **Öneri:** 1-5 arası deneyin
        """,
        'learning_rate': """
**Öğrenme Hızı**

- **Açıklama:** Her iterasyonda modelin ne kadar güncelleneceğini kontrol eder
- **Düşük değerler (örn: 0.01):** Yavaş öğrenme, daha iyi sonuçlar, daha fazla iterasyon gerekir
- **Yüksek değerler (örn: 0.3):** Hızlı öğrenme, ama optimum değeri kaçırabilir
- **Öneri:** 0.01-0.3 arası logaritmik aralıkta deneyin
        """,
        'subsample': """
**Alt Örnekleme Oranı**

- **Açıklama:** Her ağaç için kullanılacak verinin yüzdesi
- **Düşük değerler (örn: 0.6, 0.8):** Daha çeşitli ağaçlar, overfitting önleme
- **Yüksek değerler (örn: 1.0):** Tüm veriyi kullanır
- **Öneri:** 0.8-1.0 arası genellikle iyi sonuç verir
        """,
        'kernel': """
**Kernel Tipi (SVM)**

- **linear:** Doğrusal sınırlar çizer, hızlı
- **rbf (Radial Basis Function):** Non-linear sınırlar, genellikle en iyi performans
- **poly (Polynomial):** Polinom sınırlar, yüksek derece ile karmaşık
- **sigmoid:** S-tipi sınırlar
- **Öneri:** Önce rbf deneyin, linear ile karşılaştırın
        """,
        'gamma': """
**Gamma Parametresi (SVM)**

- **Açıklama:** Kernel'in etki alanını kontrol eder
- **'scale'/'auto':** Otomatik hesaplama (önerilen)
- **Düşük değerler (örn: 0.001):** Geniş etki alanı, daha genel model
- **Yüksek değerler (örn: 0.1, 1.0):** Dar etki alanı, daha karmaşık sınırlar
- **Öneri:** 'scale' ile başlayın, gerekirse manuel değerler deneyin
        """,
        'n_neighbors': """
**Komşu Sayısı (KNN)**

- **Açıklama:** Tahmin yaparken kullanılacak en yakın komşu sayısı
- **Düşük değerler (örn: 3, 5):** Daha lokal, noise'a hassas
- **Yüksek değerler (örn: 15, 20):** Daha smooth, genel ama detay kaybı
- **Öneri:** Genellikle 5-15 arası iyi sonuç verir, sqrt(n_samples) değeri başlangıç için iyi
        """,
        'var_smoothing': """
**Varyans Yumuşatma (Naive Bayes)**

- **Açıklama:** Olasılık hesaplamalarında varyans yumuşatma
- **Düşük değerler (örn: 1e-9):** Daha hassas, küçük veri setlerinde overfitting
- **Yüksek değerler (örn: 1e-3):** Daha genel, stabil model
- **Öneri:** 1e-9 ile 1e-3 arası logaritmik aralıkta deneyin
        """,
        'alpha': """
**Regularization Gücü**

- **Açıklama:** L1/L2 regularizasyonunun ne kadar güçlü olacağını kontrol eder
- **Düşük değerler (örn: 0.001, 0.01):** Az regularizasyon, daha karmaşık model
- **Yüksek değerler (örn: 10, 100):** Çok regularizasyon, daha basit model
- **Öneri:** Logaritmik aralıkta deneyin: [0.001, 0.01, 0.1, 1, 10, 100]
        """,
        'l1_ratio': """
**L1/L2 Oranı (Elastic Net)**

- **Açıklama:** L1 ve L2 regularizasyonunun karışım oranı
- **0.0:** Sadece L2 (Ridge)
- **0.5:** Eşit karışım
- **1.0:** Sadece L1 (Lasso)
- **Öneri:** 0.1-0.9 arası deneyin, genellikle 0.5 civarı iyi çalışır
        """,
        'fit_intercept': """
**Sabit Terim (Intercept)**

- **True:** Model sabit terim (intercept) içerir
- **False:** Model orijinden geçer (sabit terim yok)
- **Öneri:** Genellikle True daha iyi sonuç verir, False sadece özel durumlarda
        """,
        'normalize': """
**Normalizasyon**

- **True:** Veriler normalize edilir (artık deprecated)
- **False:** Normalizasyon yapılmaz
- **Not:** Scikit-learn'in yeni versiyonlarında normalize parametresi deprecated
- **Öneri:** False kullanın, verileri eğitim öncesi manuel normalize edin
        """
    }
    return descriptions.get(param_name, '**Açıklama:** Bu parametre model performansını etkiler.')

# Page configuration
st.set_page_config(
    page_title="Model Seçimi",
    page_icon="🤖",
    layout="wide"
)

# Hide default page navigation
st.markdown("""
<style>
    /* Streamlit varsayılan sayfa navigasyon menüsünü gizle */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Sayfa navigasyon dropdown'unu da gizle */
    [data-testid="stSidebarNav"] ul {
        display: none !important;
    }
    
    /* Sidebar'daki sayfa listesini gizle */
    section[data-testid="stSidebar"] > div:nth-child(2) > div > div > div > div > div > div > nav {
        display: none !important;
    }
    
    /* Tüm sidebar navigasyon elementlerini gizle */
    .css-1d391kg {
        display: none !important;
    }
    
    /* Streamlit widget uyarılarını gizle (default value + session state uyarısı) */
    .stAlert {
        display: none !important;
    }
    
    /* Widget uyarı mesajlarını gizle */
    [data-testid="stAlert"] {
        display: none !important;
    }
    
    /* Console uyarılarını gizle (browser console'da görünen) */
    /* Not: Bu CSS sadece görsel uyarıları gizler, console uyarıları için JavaScript gerekir */
    
    /* Metric Card Styles */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: white;
        text-align: center;
        margin: 10px 0;
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    .metric-card-label {
        font-size: 0.9em;
        opacity: 0.9;
        margin-bottom: 8px;
        font-weight: 500;
    }
    
    .metric-card-value {
        font-size: 2em;
        font-weight: bold;
        margin: 0;
    }
    
    /* Info Card Style */
    .info-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin: 20px 0;
    }
    
    .info-card-text {
        color: #2d3748;
        font-size: 1.1em;
        margin: 0;
        line-height: 1.6;
    }
    
    /* Section Header Style */
    .section-header {
        text-align: center;
        padding: 20px;
        margin: 30px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: white;
    }
    
    .section-header h3 {
        color: white;
        margin: 0;
        font-size: 1.5em;
        font-weight: 600;
    }
    
    /* Info Card Style for Target Variable Info */
    .info-box-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin: 15px 0;
        height: 100%;
        display: flex;
        flex-direction: column;
        min-height: 280px;
        flex: 1;
    }
    
    /* Sınıf Dengesi kartı için özel yükseklik */
    .info-box-card.balance-card {
        min-height: 306px;
    }
    
    /* Ensure columns stretch to equal height */
    [data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
    }
    
    [data-testid="stColumn"] {
        display: flex !important;
        flex-direction: column !important;
    }
    
    .info-box-card h4 {
        color: #2d3748;
        margin: 0 0 15px 0;
        font-size: 1.2em;
        font-weight: 600;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 10px;
    }
    
    .info-box-card ul {
        margin: 0;
        padding-left: 20px;
        color: #4a5568;
    }
    
    .info-box-card li {
        margin: 8px 0;
        font-size: 1em;
        line-height: 1.6;
    }
    
    /* Flip Card Style for Problem Type */
    .flip-card-container {
        perspective: 1000px;
        width: 100%;
        height: 200px;
        margin: 20px 0;
    }
    
    .flip-card-inner {
        position: relative;
        width: 100%;
        height: 100%;
        text-align: center;
        transition: transform 0.6s;
        transform-style: preserve-3d;
    }
    
    .flip-card-container:hover .flip-card-inner {
        transform: rotateY(180deg);
    }
    
    .flip-card-front, .flip-card-back {
        position: absolute;
        width: 100%;
        height: 100%;
        backface-visibility: hidden;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 25px;
    }
    
    .flip-card-front {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .flip-card-back {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        color: white;
        transform: rotateY(180deg);
    }
    
    .flip-card-front-icon {
        font-size: 3em;
        margin-bottom: 15px;
    }
    
    .flip-card-front-title {
        font-size: 1.5em;
        font-weight: 600;
        margin: 10px 0;
        color: white;
    }
    
    .flip-card-back-icon {
        font-size: 4em;
        margin-bottom: 15px;
    }
    
    .flip-card-back-title {
        font-size: 2em;
        font-weight: 700;
        color: white;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }
    
    .flip-card-back-subtitle {
        font-size: 1.2em;
        opacity: 0.9;
        color: white;
    }
    
    /* Model Selection Cards */
    .model-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 2px solid #e2e8f0;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .model-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: #667eea;
        transform: scaleY(0);
        transition: transform 0.3s ease;
    }
    
    .model-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2);
        border-color: #667eea;
    }
    
    .model-card:hover::before {
        transform: scaleY(1);
    }
    
    .model-card.selected {
        border-color: #667eea;
        background: linear-gradient(135deg, #f0f4ff 0%, #e8f0ff 100%);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .model-card.selected::before {
        transform: scaleY(1);
        background: #667eea;
    }
    
    .model-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    
    .model-card-icon {
        font-size: 2.5em;
        margin-right: 15px;
    }
    
    .model-card-title {
        font-size: 1.3em;
        font-weight: 600;
        color: #2d3748;
        margin: 0;
        flex: 1;
    }
    
    .model-card-checkbox {
        width: 24px;
        height: 24px;
        border: 2px solid #cbd5e0;
        border-radius: 6px;
        position: relative;
        transition: all 0.3s ease;
        flex-shrink: 0;
    }
    
    .model-card.selected .model-card-checkbox {
        background: #667eea;
        border-color: #667eea;
    }
    
    .model-card.selected .model-card-checkbox::after {
        content: '✓';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: white;
        font-weight: bold;
        font-size: 14px;
    }
    
    .model-card-description {
        color: #4a5568;
        font-size: 0.95em;
        line-height: 1.6;
        margin-top: 10px;
    }
    
    /* Model Category Colors */
    .model-card.linear {
        border-left-color: #4299e1;
    }
    
    .model-card.linear:hover {
        border-color: #4299e1;
        box-shadow: 0 8px 20px rgba(66, 153, 225, 0.2);
    }
    
    .model-card.tree {
        border-left-color: #48bb78;
    }
    
    .model-card.tree:hover {
        border-color: #48bb78;
        box-shadow: 0 8px 20px rgba(72, 187, 120, 0.2);
    }
    
    .model-card.ensemble {
        border-left-color: #9f7aea;
    }
    
    .model-card.ensemble:hover {
        border-color: #9f7aea;
        box-shadow: 0 8px 20px rgba(159, 122, 234, 0.2);
    }
    
    .model-card.regularization {
        border-left-color: #ed8936;
    }
    
    .model-card.regularization:hover {
        border-color: #ed8936;
        box-shadow: 0 8px 20px rgba(237, 137, 54, 0.2);
    }
    
    /* Selection Summary */
    .selection-summary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .selection-summary-title {
        font-size: 1.2em;
        font-weight: 600;
        margin-bottom: 10px;
    }
    
    .selection-summary-count {
        font-size: 2em;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .selection-summary-models {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
    }
    
    .selection-badge {
        background: rgba(255,255,255,0.2);
        padding: 5px 12px;
        border-radius: 15px;
        font-size: 0.9em;
    }
    
    /* Hide default Streamlit checkboxes in model cards */
    .model-card + div [data-testid="stCheckbox"] {
        display: none;
    }
    
    /* Make model cards interactive */
    .model-card {
        pointer-events: auto;
    }
    
</style>
""", unsafe_allow_html=True)

# JavaScript to equalize card heights
st.markdown("""
<script>
function equalizeCardHeights() {
    // Find all horizontal blocks with columns
    const horizontalBlocks = document.querySelectorAll('[data-testid="stHorizontalBlock"]');
    
    horizontalBlocks.forEach(block => {
        const columns = block.querySelectorAll('[data-testid="stColumn"]');
        if (columns.length < 2) return;
        
        const cards = [];
        columns.forEach(col => {
            const card = col.querySelector('.info-box-card');
            if (card) {
                cards.push(card);
            }
        });
        
        if (cards.length < 2) return;
        
        // Reset heights to auto to get natural height (except balance-card)
        cards.forEach(card => {
            if (!card.classList.contains('balance-card')) {
                card.style.height = 'auto';
            }
        });
        
        // Find the maximum height (excluding balance-card)
        let maxHeight = 0;
        cards.forEach(card => {
            // Skip balance-card from height calculation
            if (card.classList.contains('balance-card')) {
                return;
            }
            const height = card.offsetHeight;
            if (height > maxHeight) maxHeight = height;
        });
        
        // Set all cards to the same height (except balance-card)
        if (maxHeight > 0) {
            cards.forEach(card => {
                // Don't override balance-card height - let it use its min-height
                if (!card.classList.contains('balance-card')) {
                    card.style.height = maxHeight + 'px';
                }
            });
        }
    });
}

// Run immediately
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(equalizeCardHeights, 100);
        setTimeout(equalizeCardHeights, 500);
        setTimeout(equalizeCardHeights, 1000);
    });
} else {
    setTimeout(equalizeCardHeights, 100);
    setTimeout(equalizeCardHeights, 500);
    setTimeout(equalizeCardHeights, 1000);
}

// Run when DOM changes (Streamlit reruns)
const observer = new MutationObserver(() => {
    setTimeout(equalizeCardHeights, 100);
    setTimeout(equalizeCardHeights, 500);
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Also run on window resize
window.addEventListener('resize', () => {
    setTimeout(equalizeCardHeights, 100);
});
</script>
""", unsafe_allow_html=True)

# Update session state for current page
st.session_state.page = 'Model Seçimi'

st.title("🤖 Model Seçimi - Adım Adım Rehber")
st.markdown("---")

# Sidebar navigation
with st.sidebar:
    st.title("🤖 ML Automation")
    st.markdown("---")
    
    # Status indicator
    preprocessed_data = st.session_state.get('preprocessed_data')
    uploaded_data = st.session_state.get('uploaded_data')
    
    if preprocessed_data is not None:
        # Veri ön işleme yapılmış mı kontrol et
        # Eğer preprocessed_data ve uploaded_data aynıysa, işlenmemiş demektir
        if uploaded_data is not None:
            # Shape ve içerik karşılaştırması
            if (preprocessed_data.shape == uploaded_data.shape and 
                preprocessed_data.equals(uploaded_data)):
                # Veri işlenmemiş, ham veri göster
                st.info("ℹ️ Ham veri mevcut")
                df = uploaded_data
            else:
                # Veri işlenmiş
                st.success("✅ İşlenmiş veri mevcut")
                df = preprocessed_data
        else:
            # Sadece preprocessed_data var (nadir durum)
            st.success("✅ İşlenmiş veri mevcut")
            df = preprocessed_data
        
        if df is not None:
            st.caption(f"📊 {len(df):,} satır × {len(df.columns)} sütun")
    elif uploaded_data is not None:
        st.info("ℹ️ Ham veri mevcut")
        df = uploaded_data
        if df is not None:
            st.caption(f"📊 {len(df):,} satır × {len(df.columns)} sütun")
    else:
        st.warning("⚠️ Veri yüklenmedi")
        st.info("💡 Önce 'Veri Yükleme' sayfasından veri yükleyin")
    
    st.markdown("---")
    st.markdown("### 🧭 Navigasyon")
    
    if st.button("🏠 Ana Sayfa", width='stretch'):
        st.switch_page("app.py")
    
    if st.button("📊 Veri Yükleme", width='stretch'):
        st.switch_page("pages/data_upload.py")
    
    if st.button("🔍 EDA", width='stretch'):
        st.switch_page("pages/eda.py")
    
    if st.button("🔧 Veri Ön İşleme", width='stretch'):
        st.switch_page("pages/data_preprocessing.py")
    
    if st.button("🤖 Model Seçimi", width='stretch', type="primary"):
        pass  # Already on this page
    
    st.markdown("---")
    st.markdown("### ℹ️ Hakkında")
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 15px; 
                border-radius: 10px; 
                margin: 10px 0;
                color: white;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
    <p style='margin: 0; font-size: 0.9em; line-height: 1.6; color: white;'>
    Model Seçimi modülü, verilerinize uygun makine öğrenmesi modellerini önerir, eğitir ve değerlendirir.
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("💡 Sol menüden sayfalar arasında geçiş yapabilirsiniz")

# Check if data is loaded
df = None
if st.session_state.get('preprocessed_data') is not None:
    df = st.session_state.get('preprocessed_data').copy()
elif st.session_state.get('uploaded_data') is not None:
    df = st.session_state.get('uploaded_data').copy()
else:
    st.markdown("### ⚠️ Veri yüklenmedi!")
    st.info("💡 Lütfen önce 'Veri Yükleme' sayfasından veri yükleyin.")
    st.markdown("")  # Boş satır
    if st.button("📊 Veri Yükleme Sayfasına Git", type="primary"):
        st.switch_page("pages/data_upload.py")
    st.stop()

if df is None or df.empty:
    st.error("❌ Veri bulunamadı veya boş!")
    st.stop()

# Initialize session state
if 'model_selection_step' not in st.session_state:
    st.session_state.model_selection_step = 1
if 'target_variable' not in st.session_state:
    st.session_state.target_variable = None
if 'problem_type' not in st.session_state:
    st.session_state.problem_type = None
if 'problem_type_info' not in st.session_state:
    st.session_state.problem_type_info = None
if 'recommended_models' not in st.session_state:
    st.session_state.recommended_models = []
if 'selected_models' not in st.session_state:
    st.session_state.selected_models = []
if 'trained_models' not in st.session_state:
    st.session_state.trained_models = {}
if 'model_results' not in st.session_state:
    st.session_state.model_results = {}
if 'best_model' not in st.session_state:
    st.session_state.best_model = None
if 'X_train' not in st.session_state:
    st.session_state.X_train = None
if 'X_test' not in st.session_state:
    st.session_state.X_test = None
if 'y_train' not in st.session_state:
    st.session_state.y_train = None
if 'y_test' not in st.session_state:
    st.session_state.y_test = None

# Steps definition
steps = [
    {"name": "Hedef Değişken", "icon": "🎯", "key": "target_selection"},
    {"name": "Problem Tipi", "icon": "🔍", "key": "problem_detection"},
    {"name": "Model Önerisi", "icon": "💡", "key": "model_recommendation"},
    {"name": "Model Eğitimi", "icon": "🚀", "key": "model_training"},
    {"name": "Değerlendirme", "icon": "📊", "key": "model_evaluation"},
    {"name": "Karşılaştırma", "icon": "⚖️", "key": "model_comparison"},
    {"name": "Yorumlama", "icon": "🔬", "key": "model_interpretation"},
    {"name": "Model İndirme", "icon": "💾", "key": "model_download"}
]

# Display progress bar
current_step = st.session_state.model_selection_step
st.markdown("### 📍 İlerleme")
progress_cols = st.columns(len(steps))
for i, step in enumerate(steps):
    step_num = i + 1
    step_name = step['name']
    step_icon = step['icon']
    
    with progress_cols[i]:
        if step_num < current_step:
            status = "✓"
            color = "#4CAF50"
            bg_color = "#E8F5E9"
        elif step_num == current_step:
            status = "→"
            color = "#2196F3"
            bg_color = "#E3F2FD"
        else:
            status = "○"
            color = "#9E9E9E"
            bg_color = "#F5F5F5"
        
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 10px;
            background: {bg_color};
            border-radius: 8px;
            border: 2px solid {color};
            margin-bottom: 10px;
        ">
            <div style="font-size: 1.2em; font-weight: bold; color: {color};">
                {step_icon} {status}
            </div>
            <div style="font-size: 0.8em; color: {color}; margin-top: 5px;">
                {step_name}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# STEP 1: Target Variable Selection
if current_step == 1:
    st.header("🎯 Adım 1: Hedef Değişken Seçimi")
    
    # Info card
    st.markdown("""
    <div class="info-card">
        <p class="info-card-text">
            💡 <strong>Model eğitimi için hedef değişkeni seçin.</strong> Hedef değişken, tahmin etmek istediğiniz sütundur.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show data info in cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-label">📊 Satır Sayısı</div>
            <div class="metric-card-value">{len(df):,}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-label">📋 Sütun Sayısı</div>
            <div class="metric-card-value">{len(df.columns)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-label">📈 Toplam Veri</div>
            <div class="metric-card-value">{len(df) * len(df.columns):,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Target variable selection
    all_columns = df.columns.tolist()
    selected_target = st.selectbox(
        "Hedef Değişken Seçin",
        options=all_columns,
        index=0 if st.session_state.target_variable is None else all_columns.index(st.session_state.target_variable) if st.session_state.target_variable in all_columns else 0,
        help="Tahmin etmek istediğiniz değişkeni seçin"
    )
    
    # Show target variable info
    if selected_target:
        st.markdown("### 📋 Hedef Değişken Bilgileri")
        target_analysis = analyze_target_variable(df, selected_target)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="info-box-card">
                <h4>📊 Temel Bilgiler</h4>
                <ul>
                    <li>Veri Tipi: {target_analysis['data_type']}</li>
                    <li>Numeric: {'Evet' if target_analysis['is_numeric'] else 'Hayır'}</li>
                    <li>Unique Değer: {target_analysis['unique_count']}</li>
                    <li>Eksik Değer: {target_analysis['missing_count']} ({target_analysis['missing_percentage']:.2f}%)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if target_analysis['is_numeric']:
                stats = target_analysis.get('numeric_stats', {})
                mean_val = stats.get('mean', None)
                median_val = stats.get('median', None)
                std_val = stats.get('std', None)
                
                mean_str = f"{mean_val:.2f}" if mean_val is not None else "N/A"
                median_str = f"{median_val:.2f}" if median_val is not None else "N/A"
                std_str = f"{std_val:.2f}" if std_val is not None else "N/A"
                
                st.markdown(f"""
                <div class="info-box-card">
                    <h4>📈 Numeric İstatistikler</h4>
                    <ul>
                        <li>Ortalama: {mean_str}</li>
                        <li>Medyan: {median_str}</li>
                        <li>Std: {std_str}</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                stats = target_analysis.get('categorical_stats', {})
                most_freq = stats.get('most_frequent', 'N/A')
                most_freq_count = stats.get('most_frequent_count', 0)
                
                st.markdown(f"""
                <div class="info-box-card">
                    <h4>📊 Kategorik İstatistikler</h4>
                    <ul>
                        <li>En Sık: {most_freq}</li>
                        <li>En Sık Sayısı: {most_freq_count}</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        
        # Validate target variable
        is_valid, error_msg = validate_target_variable(df, selected_target)
        
        if not is_valid:
            st.error(f"❌ {error_msg}")
            st.stop()
        
        # Navigation buttons
        st.markdown("<br>", unsafe_allow_html=True)
        nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
        with nav_col1:
            # Geri butonu ilk adımda yok
            st.empty()
        with nav_col2:
            # Atla butonu (opsiyonel)
            if st.button("⏭️ Atla", width='stretch'):
                st.session_state.model_selection_step = 2
                st.rerun()
        with nav_col3:
            # İleri butonu
            if st.button("İleri →", type="primary", width='stretch'):
                st.session_state.target_variable = selected_target
                st.session_state.model_selection_step = 2
                st.rerun()

# STEP 2: Problem Type Detection
elif current_step == 2:
    st.header("🔍 Adım 2: Problem Tipi Tespiti")
    
    if st.session_state.target_variable is None:
        st.warning("⚠️ Hedef değişken seçilmedi! Lütfen geri dönüp hedef değişkeni seçin.")
        target_col = None
    else:
        target_col = st.session_state.target_variable
    
    if target_col is not None:
        with st.spinner("Problem tipi tespit ediliyor..."):
            problem_type = detect_problem_type(df, target_col)
            problem_type_info = get_problem_type_info(df, target_col)
        
        st.session_state.problem_type = problem_type
        st.session_state.problem_type_info = problem_type_info
    else:
        # Initialize empty if skipped
        if st.session_state.problem_type is None:
            st.session_state.problem_type = None
        if st.session_state.problem_type_info is None:
            st.session_state.problem_type_info = None
        problem_type = st.session_state.problem_type
        problem_type_info = st.session_state.problem_type_info
    
    # Flip card for problem type
    problem_type_display = problem_type.replace('_', ' ').title()
    problem_icon = "📊" if problem_type_info['is_classification'] else "📈"
    problem_description = "Sınıflandırma Problemi" if problem_type_info['is_classification'] else "Regresyon Problemi"
    
    st.markdown(f"""
    <div class="flip-card-container">
        <div class="flip-card-inner">
            <div class="flip-card-front">
                <div class="flip-card-front-icon">🔍</div>
                <div class="flip-card-front-title">Problem Tipi Tespit Edildi</div>
            </div>
            <div class="flip-card-back">
                <div class="flip-card-back-icon">{problem_icon}</div>
                <div class="flip-card-back-title">{problem_description}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Problem Tipi Detayları")
    
    col1, col2 = st.columns(2)
    with col1:
        # Temel Bilgiler kartı
        problem_type_str = problem_type
        is_classification = 'Evet' if problem_type_info['is_classification'] else 'Hayır'
        is_regression = 'Evet' if problem_type_info['is_regression'] else 'Hayır'
        
        # Liste öğelerini oluştur
        list_items = [
            f"<li>Problem Tipi: {problem_type_str}</li>",
            f"<li>Sınıflandırma: {is_classification}</li>",
            f"<li>Regresyon: {is_regression}</li>"
        ]
        
        if problem_type_info['is_classification']:
            is_binary = 'Evet' if problem_type_info['is_binary'] else 'Hayır'
            is_multiclass = 'Evet' if problem_type_info['is_multiclass'] else 'Hayır'
            num_classes = problem_type_info.get('num_classes', 'N/A')
            list_items.extend([
                f"<li>Binary: {is_binary}</li>",
                f"<li>Multiclass: {is_multiclass}</li>",
                f"<li>Sınıf Sayısı: {num_classes}</li>"
            ])
        
        basic_info_html = f"""
        <div class="info-box-card">
            <h4>🔍 Temel Bilgiler</h4>
            <ul>
                {''.join(list_items)}
            </ul>
        </div>
        """
        st.markdown(basic_info_html, unsafe_allow_html=True)
    
    with col2:
        if problem_type_info['is_classification']:
            # Sınıf Dengesi kartı
            if 'class_imbalance' in problem_type_info:
                imbalance = problem_type_info['class_imbalance']
                is_imbalanced = 'Evet' if imbalance['is_imbalanced'] else 'Hayır'
                
                # Liste öğelerini oluştur
                balance_items = [f"<li>Dengesiz: {is_imbalanced}</li>"]
                
                if imbalance['is_imbalanced']:
                    min_prop = imbalance['min_class_proportion']
                    imbalance_ratio = imbalance.get('imbalance_ratio', 'N/A')
                    balance_items.extend([
                        f"<li>Min Sınıf Oranı: {min_prop:.2%}</li>",
                        f"<li>Denge Oranı: {imbalance_ratio}</li>"
                    ])
                else:
                    balance_items.append("<li>Durum: Dengeli</li>")
                
                balance_info_html = f"""
                <div class="info-box-card balance-card">
                    <h4>⚖️ Sınıf Dengesi</h4>
                    <ul>
                        {''.join(balance_items)}
                    </ul>
                </div>
                """
                st.markdown(balance_info_html, unsafe_allow_html=True)
        
        if problem_type_info['is_regression']:
            # Hedef Değişken Aralığı kartı
            if 'target_range' in problem_type_info:
                range_info = problem_type_info['target_range']
                
                range_info_html = f"""
                <div class="info-box-card">
                    <h4>📈 Hedef Değişken İstatistikleri</h4>
                    <ul>
                        <li>Min: {range_info['min']:.2f}</li>
                        <li>Max: {range_info['max']:.2f}</li>
                        <li>Ortalama: {range_info['mean']:.2f}</li>
                        <li>Std: {range_info['std']:.2f}</li>
                    </ul>
                </div>
                """
                st.markdown(range_info_html, unsafe_allow_html=True)
    
    # Navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    with nav_col1:
        if st.button("← Geri", width='stretch'):
            st.session_state.model_selection_step = 1
            st.rerun()
    with nav_col2:
        if st.button("⏭️ Atla", width='stretch'):
            st.session_state.model_selection_step = 3
            st.rerun()
    with nav_col3:
        if st.button("İleri →", type="primary", width='stretch'):
            st.session_state.model_selection_step = 3
            st.rerun()

# STEP 3: Model Selection
elif current_step == 3:
    st.header("💡 Adım 3: Model Seçimi")
    
    if st.session_state.problem_type is None:
        st.warning("⚠️ Problem tipi tespit edilmedi! Lütfen geri dönüp problem tipini tespit edin.")
        problem_type = 'binary_classification'  # Default value
    else:
        problem_type = st.session_state.problem_type
    is_classification = problem_type in ['binary_classification', 'multiclass_classification']
    
    st.markdown("### 🔧 Manuel İşlemler")
    
    # Create a styled container for manual operations (same style as data_preprocessing)
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    '>
    """, unsafe_allow_html=True)
    
    # Define available models first
    if is_classification:
        available_models = {
            "Logistic Regression": "📊 Doğrusal sınıflandırma modeli",
            "Random Forest": "🌲 Ensemble yöntemi, güçlü performans",
            "XGBoost": "⚡ Gradient boosting, yüksek performans",
            "SVM": "🔷 Destek vektör makinesi, karmaşık sınırlar",
            "KNN": "👥 K-en yakın komşu algoritması",
            "Naive Bayes": "📈 Olasılık tabanlı sınıflandırma"
        }
    else:  # Regression
        available_models = {
            "Linear Regression": "📊 Doğrusal regresyon modeli",
            "Random Forest": "🌲 Ensemble yöntemi, güçlü performans",
            "XGBoost": "⚡ Gradient boosting, yüksek performans",
            "SVM": "🔷 Destek vektör makinesi",
            "Ridge": "📈 L2 regularizasyonlu regresyon",
            "Lasso": "📉 L1 regularizasyonlu regresyon",
            "Elastic Net": "🔗 L1+L2 regularizasyonlu regresyon"
        }
    
    # Header with "Select All" and "Deselect All" buttons
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown("#### 📌 Model Seçimi")
        st.markdown("Eğitmek istediğiniz modelleri seçin:")
    with header_col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Vertical spacing
        button_col1, button_col2 = st.columns(2)
        with button_col1:
            if st.button("❌ Tümünü Kaldır", key="deselect_all_models", width='stretch'):
                # Deselect all models
                for model_name in available_models.keys():
                    checkbox_key = f"model_select_{model_name}"
                    st.session_state[checkbox_key] = False
                st.rerun()
        with button_col2:
            if st.button("✅ Tümünü Seç", key="select_all_models", width='stretch'):
                # Select all models
                for model_name in available_models.keys():
                    checkbox_key = f"model_select_{model_name}"
                    st.session_state[checkbox_key] = True
                st.rerun()
    
    # Display model selection checkboxes in 2 columns
    selected_models = []
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    # Split models into two groups
    model_list = list(available_models.items())
    mid_point = len(model_list) // 2 + (len(model_list) % 2)
    
    # First column
    with col1:
        for model_name, description in model_list[:mid_point]:
            checkbox_key = f"model_select_{model_name}"
            # Initialize session state if not exists to avoid default value warning
            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = False
            
            is_selected = st.checkbox(
                f"**{model_name}** - {description}",
                key=checkbox_key
            )
            
            if is_selected:
                selected_models.append(model_name)
    
    # Second column
    with col2:
        for model_name, description in model_list[mid_point:]:
            checkbox_key = f"model_select_{model_name}"
            # Initialize session state if not exists to avoid default value warning
            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = False
            
            is_selected = st.checkbox(
                f"**{model_name}** - {description}",
                key=checkbox_key
            )
            
            if is_selected:
                selected_models.append(model_name)
    
    st.session_state.selected_models = selected_models
    
    # Show selected models info cards
    if selected_models:
        st.markdown("### ✅ Seçilen Modeller")
        
        # Model detayları
        model_details = {
            "Logistic Regression": {
                "icon": "📊",
                "description": "Logistic Regression, sınıflandırma problemlerinde kullanılan doğrusal bir modeldir. Sigmoid fonksiyonu kullanarak olasılık tahmini yapar ve binary veya multiclass sınıflandırma için uygundur. Özellikle doğrusal olarak ayrılabilir veriler için etkilidir.",
                "advantages": "Hızlı eğitim süresi, yüksek yorumlanabilirlik, overfitting'e karşı dayanıklı, küçük veri setlerinde etkili, olasılık tahmini sağlar",
                "disadvantages": "Sadece doğrusal ilişkileri modelleyebilir, non-linear pattern'leri yakalayamaz, feature scaling gerektirir, çok sayıda feature'da performans düşer",
                "use_case": "Binary ve multiclass sınıflandırma problemleri, tıbbi tanı, spam tespiti, kredi riski değerlendirmesi için idealdir"
            },
            "Random Forest": {
                "icon": "🌲",
                "description": "Random Forest, birden fazla karar ağacının birleşiminden oluşan ensemble bir yöntemdir. Her ağaç farklı veri alt kümeleri ve feature'lar üzerinde eğitilir, sonuçlar oylama ile birleştirilir. Bu yaklaşım overfitting'i azaltır ve genel performansı artırır.",
                "advantages": "Aykırı değerlere dayanıklı, feature importance analizi sağlar, overfitting riski düşük, non-linear ilişkileri yakalayabilir, missing value handling yapabilir",
                "disadvantages": "Büyük veri setlerinde yavaş eğitim, yüksek bellek kullanımı, yorumlanabilirlik düşük, hiperparametre optimizasyonu karmaşık",
                "use_case": "Karmaşık veri setleri, feature importance analizi, e-ticaret öneri sistemleri, görüntü sınıflandırma için uygundur"
            },
            "XGBoost": {
                "icon": "⚡",
                "description": "XGBoost (Extreme Gradient Boosting), gradient boosting algoritmasının optimize edilmiş ve geliştirilmiş versiyonudur. Zayıf öğrenicileri (weak learners) sıralı olarak birleştirerek güçlü bir model oluşturur. Paralel işleme ve regularizasyon teknikleri ile yüksek performans sağlar.",
                "advantages": "Yüksek doğruluk oranı, hızlı eğitim (paralel işleme), missing value handling, overfitting kontrolü (regularization), feature importance sağlar",
                "disadvantages": "Hiperparametre optimizasyonu zor, yorumlanabilirlik düşük, overfitting riski (dikkatli kullanım gerekir), büyük veri setlerinde bellek sorunu",
                "use_case": "Yarışmalar (Kaggle), yüksek performans gerektiren projeler, tablo verileri, ranking problemleri için idealdir"
            },
            "SVM": {
                "icon": "🔷",
                "description": "Support Vector Machine (SVM), veri noktalarını optimal bir hiperdüzlem ile ayırmaya çalışan güçlü bir sınıflandırma ve regresyon algoritmasıdır. Kernel trick kullanarak non-linear sınırlar çizebilir ve yüksek boyutlu verilerde etkilidir.",
                "advantages": "Karmaşık non-linear sınırlar çizebilir, yüksek boyutlu verilerde etkili, overfitting'e karşı dayanıklı (margin maximization), memory efficient",
                "disadvantages": "Büyük veri setlerinde yavaş, hiperparametre seçimi kritik, yorumlanabilirlik düşük, probability estimate zayıf",
                "use_case": "Non-linear sınırlar, yüksek boyutlu veriler, metin sınıflandırma, görüntü tanıma için uygundur"
            },
            "KNN": {
                "icon": "👥",
                "description": "K-Nearest Neighbors (KNN), lazy learning algoritmasıdır. Yeni bir veri noktası için, en yakın k komşunun çoğunluk oylamasına göre sınıflandırma yapar. Non-parametric bir yöntemdir ve eğitim aşaması yoktur, tüm hesaplama tahmin sırasında yapılır.",
                "advantages": "Basit ve anlaşılır algoritma, non-parametric (dağılım varsayımı yok), lokal pattern'leri yakalar, çok sınıflı problemlerde etkili",
                "disadvantages": "Büyük veri setlerinde yavaş tahmin, feature scaling kritik, k değeri seçimi zor, gürültülü verilerde performans düşer, yüksek bellek kullanımı",
                "use_case": "Küçük-orta boyutlu veri setleri, lokal pattern'ler, öneri sistemleri, anomaly detection için idealdir"
            },
            "Naive Bayes": {
                "icon": "📈",
                "description": "Naive Bayes, Bayes teoremini kullanan olasılık tabanlı bir sınıflandırma algoritmasıdır. Feature'ların birbirinden bağımsız olduğunu varsayar (naive assumption). Bu varsayım gerçekçi olmasa da, pratikte çok iyi sonuçlar verir, özellikle metin sınıflandırmada.",
                "advantages": "Çok hızlı eğitim ve tahmin, küçük veri setlerinde etkili, text classification için ideal, olasılık tahmini sağlar, missing value handling kolay",
                "disadvantages": "Feature independence varsayımı gerçekçi değil, sürekli değişkenlerde performans düşer, feature correlation'ı göz ardı eder",
                "use_case": "Text classification (spam, sentiment), küçük veri setleri, real-time classification, medical diagnosis için uygundur"
            },
            "Linear Regression": {
                "icon": "📊",
                "description": "Linear Regression, bağımlı değişken ile bağımsız değişkenler arasındaki doğrusal ilişkiyi modelleyen temel bir regresyon algoritmasıdır. En küçük kareler yöntemi ile parametreleri tahmin eder. Baseline model olarak sıklıkla kullanılır ve yorumlanabilirliği yüksektir.",
                "advantages": "Hızlı eğitim, yüksek yorumlanabilirlik, baseline model olarak kullanılır, overfitting riski düşük, basit implementasyon",
                "disadvantages": "Sadece doğrusal ilişkileri modelleyebilir, outlier'lara hassas, multicollinearity sorunu, heteroscedasticity varsayımı",
                "use_case": "Doğrusal ilişkiler, baseline model, fiyat tahmini, trend analizi, basit regresyon problemleri için idealdir"
            },
            "Ridge": {
                "icon": "📈",
                "description": "Ridge Regression, Linear Regression'a L2 regularizasyonu ekleyen bir yöntemdir. Kareli katsayıların toplamını (L2 norm) cezalandırarak overfitting'i önler. Tüm feature'ları korur ancak katsayılarını küçültür, bu sayede multicollinearity sorununu çözer.",
                "advantages": "Overfitting'i önler, multicollinearity sorununu çözer, tüm feature'ları korur, daha stabil tahminler, küçük katsayılar",
                "disadvantages": "Feature selection yapmaz, lambda parametresi seçimi kritik, yorumlanabilirlik biraz düşer, tüm feature'lar modele dahil",
                "use_case": "Çok sayıda feature, multicollinearity durumu, overfitting riski olan problemler için idealdir"
            },
            "Lasso": {
                "icon": "📉",
                "description": "Lasso (Least Absolute Shrinkage and Selection Operator) Regression, Linear Regression'a L1 regularizasyonu ekleyen bir yöntemdir. Mutlak değerli katsayıların toplamını cezalandırarak bazı feature'ların katsayılarını sıfıra indirir, böylece otomatik feature selection yapar.",
                "advantages": "Otomatik feature selection yapar, sparse modeller oluşturur, overfitting'i önler, yorumlanabilirlik artar (az feature), multicollinearity'de etkili",
                "disadvantages": "Lambda parametresi seçimi kritik, correlated feature'larda rastgele seçim yapabilir, n < p durumunda maksimum n feature seçer",
                "use_case": "Feature selection gerektiren problemler, sparse modeller, yüksek boyutlu veriler, interpretability önemli olduğunda idealdir"
            },
            "Elastic Net": {
                "icon": "🔗",
                "description": "Elastic Net Regression, Ridge ve Lasso regresyonlarının avantajlarını birleştiren bir yöntemdir. Hem L1 hem de L2 regularizasyonunu birlikte kullanır. Bu sayede hem feature selection yapar hem de correlated feature'ları birlikte tutar. Ridge ve Lasso'nun en iyi yönlerini birleştirir.",
                "advantages": "Ridge ve Lasso'nun avantajlarını birleştirir, feature selection yapar, correlated feature'ları birlikte tutar, overfitting'i önler, daha stabil",
                "disadvantages": "İki hiperparametre (alpha ve l1_ratio) optimizasyonu gerekir, daha karmaşık, eğitim süresi daha uzun",
                "use_case": "Hem feature selection hem de overfitting önleme gerektiğinde, correlated feature'ların olduğu durumlarda idealdir"
            }
        }
        
        # Initialize carousel index if not exists
        carousel_index_key = 'model_carousel_index'
        if carousel_index_key not in st.session_state:
            st.session_state[carousel_index_key] = 0
        
        # Filter selected models that have details
        models_with_details = [m for m in selected_models if m in model_details]
        
        if models_with_details:
            current_index = st.session_state[carousel_index_key]
            
            # Navigation buttons and model card with Streamlit columns
            # CSS to vertically center buttons in side columns
            st.markdown("""
            <style>
                div[data-testid="column"]:nth-of-type(3) > div[data-testid="stVerticalBlock"] {
                    display: flex !important;
                    flex-direction: column !important;
                    justify-content: center !important;
                    align-items: center !important;
                    margin-top: 50px !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 7, 1], vertical_alignment="center")
            
            with col1:
                if st.button("◀️", key="prev_model_card", disabled=(current_index == 0), width='stretch'):
                    st.session_state[carousel_index_key] = max(0, current_index - 1)
                    st.rerun()
            
            with col2:
                # Display model count info with better styling
                st.markdown(f"""
                <div style='
                    text-align: center; 
                    margin: 20px 0; 
                    padding: 15px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 10px;
                    color: white;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                '>
                    <strong style='font-size: 1.1em;'>{len(models_with_details)} model seçildi</strong> | 
                    <em style='font-size: 1em;'>Model {current_index + 1}/{len(models_with_details)}</em>
                </div>
                """, unsafe_allow_html=True)
                
                # Current model card
                current_model = models_with_details[current_index]
                details = model_details[current_model]
                
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                    padding: 15px;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    border-left: 3px solid #667eea;
                    margin: 15px 0;
                '>
                    <div style='
                        display: flex;
                        align-items: center;
                        margin-bottom: 12px;
                        padding-bottom: 10px;
                        border-bottom: 2px solid #e0e0e0;
                    '>
                        <span style='font-size: 1.5em; margin-right: 10px;'>{details['icon']}</span>
                        <h3 style='
                            color: #2d3748;
                            margin: 0;
                            font-size: 1.3em;
                            font-weight: 700;
                        '>{current_model}</h3>
                    </div>
                    <ul style='
                        list-style: none;
                        padding: 0;
                        margin: 0;
                    '>
                        <li style='
                            margin-bottom: 10px;
                            padding: 10px;
                            background: rgba(102, 126, 234, 0.05);
                            border-radius: 5px;
                            border-left: 3px solid #667eea;
                        '>
                            <strong style='color: #667eea; font-size: 0.95em; display: block; margin-bottom: 4px;'>📝 Açıklama:</strong>
                            <span style='color: #4a5568; line-height: 1.4; font-size: 0.9em;'>{details['description']}</span>
                        </li>
                        <li style='
                            margin-bottom: 10px;
                            padding: 10px;
                            background: rgba(76, 175, 80, 0.05);
                            border-radius: 5px;
                            border-left: 3px solid #4caf50;
                        '>
                            <strong style='color: #4caf50; font-size: 0.95em; display: block; margin-bottom: 4px;'>✅ Avantajlar:</strong>
                            <span style='color: #4a5568; line-height: 1.4; font-size: 0.9em;'>{details['advantages']}</span>
                        </li>
                        <li style='
                            margin-bottom: 10px;
                            padding: 10px;
                            background: rgba(244, 67, 54, 0.05);
                            border-radius: 5px;
                            border-left: 3px solid #f44336;
                        '>
                            <strong style='color: #f44336; font-size: 0.95em; display: block; margin-bottom: 4px;'>❌ Dezavantajlar:</strong>
                            <span style='color: #4a5568; line-height: 1.4; font-size: 0.9em;'>{details['disadvantages']}</span>
                        </li>
                        <li style='
                            margin-bottom: 10px;
                            padding: 10px;
                            background: rgba(255, 152, 0, 0.05);
                            border-radius: 5px;
                            border-left: 3px solid #ff9800;
                        '>
                            <strong style='color: #ff9800; font-size: 0.95em; display: block; margin-bottom: 4px;'>🎯 Kullanım:</strong>
                            <span style='color: #4a5568; line-height: 1.4; font-size: 0.9em;'>{details['use_case']}</span>
                        </li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                if st.button("▶️", key="next_model_card", disabled=(current_index == len(models_with_details) - 1), width='stretch'):
                    st.session_state[carousel_index_key] = min(len(models_with_details) - 1, current_index + 1)
                    st.rerun()
    else:
        st.warning("⚠️ Lütfen en az bir model seçin!")
    
    # Navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    with nav_col1:
        if st.button("← Geri", width='stretch'):
            st.session_state.model_selection_step = 2
            st.rerun()
    with nav_col2:
        if st.button("⏭️ Atla", width='stretch'):
            # If no models selected, set empty list to allow skip
            if not st.session_state.selected_models:
                st.session_state.selected_models = []
            st.session_state.model_selection_step = 4
            st.rerun()
    with nav_col3:
        if st.button("İleri →", type="primary", width='stretch', disabled=not selected_models):
            st.session_state.model_selection_step = 4
            st.rerun()

# STEP 4: Model Training
elif current_step == 4:
    st.header("🚀 Adım 4: Model Eğitimi")
    
    # Initialize selected_models if not exists (for skip functionality)
    if 'selected_models' not in st.session_state:
        st.session_state.selected_models = []
    
    if not st.session_state.selected_models:
        st.warning("⚠️ Model seçilmedi! Lütfen geri dönüp model seçin.")
    
    # Prepare data
    X = df.drop(columns=[st.session_state.target_variable])
    y = df[st.session_state.target_variable]
    
    # Initialize session state for cross validation
    # CV is always enabled - force it to True
    st.session_state.use_cross_validation = True
    if 'cv_folds' not in st.session_state:
        st.session_state.cv_folds = 5
    
    st.markdown("---")
    
    # Test Set Oranı - Her zaman görünür
    st.markdown("### 📊 Test Set Oranı")
    
    # İki sütunlu layout: Test Set Oranı ve Eğitimi Durdur butonu
    col1, col2 = st.columns([3, 1])
    
    with col1:
        test_size = st.slider("Test Set Oranı", 0.1, 0.4, 0.2, 0.05)
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Dikey hizalama için boşluk
        if st.button("⏹️ Eğitimi Durdur", type="secondary", use_container_width=True):
            if 'training_stop_requested' not in st.session_state:
                st.session_state.training_stop_requested = False
            st.session_state.training_stop_requested = True
            logger.warning("⚠️ Kullanıcı eğitimi durdurma isteği gönderdi")
            st.warning("⏹️ Eğitim durduruluyor...")
            st.rerun()
    
    # Eğitimi durdurma flag'ini sıfırla (yeni eğitim başladığında)
    if 'training_stop_requested' not in st.session_state:
        st.session_state.training_stop_requested = False
    
    # Modelleri Eğit butonu
    if st.button("🎯 Modelleri Eğit", type="primary", width='stretch'):
        # Yeni eğitim başladığında durdurma flag'ini sıfırla
        st.session_state.training_stop_requested = False
        logger.info("🚀 Yeni model eğitimi başlatıldı - durdurma flag'i sıfırlandı")
        with st.spinner("Veri bölünüyor..."):
            X_train, X_test, y_train, y_test = split_data(X, y, test_size=test_size)
            st.session_state.X_train = X_train
            st.session_state.X_test = X_test
            st.session_state.y_train = y_train
            st.session_state.y_test = y_test
        
        st.info(f"📊 Veri bölündü: Eğitim={len(X_train):,}, Test={len(X_test):,}")
        
        # Log CV status
        cv_status = "AKTİF" if st.session_state.use_cross_validation else "PASİF"
        cv_folds = st.session_state.cv_folds if st.session_state.use_cross_validation else "N/A"
        logger.info(f"🔍 Cross Validation Durumu: {cv_status} | CV Folds: {cv_folds}")
        logger.info(f"📊 {len(st.session_state.selected_models)} model eğitilecek: {', '.join(st.session_state.selected_models)}")
        
        # Train models
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        trained_models = {}
        training_results = {}
        
        for idx, model_name in enumerate(st.session_state.selected_models):
            # Eğitimi durdurma kontrolü
            if st.session_state.get('training_stop_requested', False):
                logger.warning(f"⏹️ Eğitim durduruldu: {model_name} eğitilmeden önce durduruldu")
                st.warning(f"⏹️ Eğitim durduruldu. {idx}/{len(st.session_state.selected_models)} model eğitildi.")
                progress_bar.progress((idx) / len(st.session_state.selected_models))
                status_text.text("⏹️ Eğitim durduruldu")
                st.session_state.training_stop_requested = False
                break
            
            status_text.text(f"Eğitiliyor: {model_name} ({idx+1}/{len(st.session_state.selected_models)})")
            progress_bar.progress((idx) / len(st.session_state.selected_models))
            
            # Log model training start with CV info
            cv_info = f"CV={st.session_state.cv_folds} fold" if st.session_state.use_cross_validation else "CV=PASİF"
            logger.info(f"🚀 Model eğitimi başlıyor: {model_name} ({idx+1}/{len(st.session_state.selected_models)}) | {cv_info}")
            
            # Model training with automatic hyperparameter optimization
            try:
                # Eğitimi durdurma kontrolü (eğitim öncesi)
                if st.session_state.get('training_stop_requested', False):
                    logger.warning(f"⏹️ Eğitim durduruldu: {model_name} eğitilmeden önce durduruldu")
                    st.warning(f"⏹️ Eğitim durduruldu. {idx}/{len(st.session_state.selected_models)} model eğitildi.")
                    progress_bar.progress((idx) / len(st.session_state.selected_models))
                    status_text.text("⏹️ Eğitim durduruldu")
                    st.session_state.training_stop_requested = False
                    break
                
                status_text.text(f"🔧 {model_name} için GridSearch ile hiperparametre optimizasyonu yapılıyor...")
                logger.info(f"🔧 {model_name} GridSearch ile hiperparametre optimizasyonu başlıyor | CV: {st.session_state.cv_folds} fold")
                logger.info(f"📞 Frontend: train_model fonksiyonu çağrılıyor | Model: {model_name} | Veri: {len(X_train)} örnek, {len(X_train.columns)} özellik")
                result = train_model(
                    model_name,
                    X_train,
                    y_train,
                    st.session_state.problem_type,
                    use_cross_validation=st.session_state.use_cross_validation,
                    cv_folds=st.session_state.cv_folds
                )
                logger.info(f"📥 Frontend: train_model fonksiyonu tamamlandı | Model: {model_name} | Sonuç: {result.get('success', False)} | Optimization: {result.get('optimization_method', 'N/A')}")
                
                # Eğitimi durdurma kontrolü (eğitim sonrası)
                if st.session_state.get('training_stop_requested', False):
                    logger.warning(f"⏹️ Eğitim durduruldu: {model_name} eğitildikten sonra durduruldu")
                    st.warning(f"⏹️ Eğitim durduruldu. {idx+1}/{len(st.session_state.selected_models)} model eğitildi.")
                    progress_bar.progress((idx+1) / len(st.session_state.selected_models))
                    status_text.text("⏹️ Eğitim durduruldu")
                    st.session_state.training_stop_requested = False
                    break
                
                if result['success']:
                    trained_models[model_name] = result['model']
                    training_results[model_name] = result
                    
                    # Check if hyperparameter optimization was used
                    is_optimized = result.get('optimization_method') == 'grid_search'
                    best_params = result.get('best_params', {})
                    best_cv_score = result.get('best_cv_score')
                    n_combinations = result.get('n_param_combinations', 0)
                    
                    cv_used = "EVET" if result.get('cv_scores') is not None else "HAYIR"
                    cv_mean = result.get('cv_mean')
                    cv_info = f"CV: {cv_used}" + (f" (Ortalama: {cv_mean:.4f})" if cv_mean is not None else "")
                    
                    if is_optimized and best_params:
                        opt_info = f" | GridSearch: {n_combinations} kombinasyon test edildi"
                        if best_cv_score is not None:
                            opt_info += f" | En İyi CV Skoru: {best_cv_score:.4f}"
                        logger.info(f"✅ {model_name} GridSearch ile optimize edildi ve eğitildi | Süre: {result['training_time']:.2f}s | {cv_info}{opt_info}")
                        logger.info(f"🎯 {model_name} En iyi parametreler: {best_params}")
                        logger.info(f"📊 {model_name} İlerleme: {idx+1}/{len(st.session_state.selected_models)} model tamamlandı")
                        st.success(f"✅ {model_name} optimize edildi ve eğitildi ({result['training_time']:.2f}s)")
                    else:
                        logger.info(f"✅ {model_name} eğitildi | Süre: {result['training_time']:.2f}s | {cv_info}")
                        logger.info(f"📊 {model_name} İlerleme: {idx+1}/{len(st.session_state.selected_models)} model tamamlandı")
                        st.success(f"✅ {model_name} eğitildi ({result['training_time']:.2f}s)")
                else:
                    logger.error(f"❌ {model_name} eğitilemedi: {result.get('error', 'Bilinmeyen hata')}")
                    st.error(f"❌ {model_name} eğitilemedi: {result['error']}")
            except Exception as e:
                logger.error(f"❌ {model_name} eğitilirken hata: {str(e)}")
                logger.exception(f"❌ {model_name} eğitim hatası detayları:")
                st.error(f"❌ {model_name} eğitilemedi: {str(e)}")
        
        progress_bar.progress(1.0)
        
        # Eğitim durduruldu mu kontrol et
        if st.session_state.get('training_stop_requested', False):
            logger.warning(f"⏹️ Eğitim kullanıcı tarafından durduruldu | {len(trained_models)}/{len(st.session_state.selected_models)} model eğitildi")
            status_text.text(f"⏹️ Eğitim durduruldu ({len(trained_models)}/{len(st.session_state.selected_models)} model eğitildi)")
            st.session_state.training_stop_requested = False
        else:
            logger.info(f"✅ Tüm modeller başarıyla eğitildi | Toplam: {len(trained_models)} model")
            status_text.text("✅ Tüm modeller eğitildi!")
        
        st.session_state.trained_models = trained_models
        st.session_state.training_results = training_results
        
        # Evaluate models
        model_results = {}
        
        for model_name, model in trained_models.items():
            if st.session_state.X_test is not None:
                try:
                    X_test = st.session_state.X_test
                    # Handle missing values
                    if X_test.isnull().any().any():
                        from sklearn.impute import SimpleImputer
                        imputer = SimpleImputer(strategy='mean' if X_test.select_dtypes(include=[np.number]).shape[1] > 0 else 'most_frequent')
                        X_test_imputed = pd.DataFrame(
                            imputer.fit_transform(X_test),
                            columns=X_test.columns,
                            index=X_test.index
                        )
                    else:
                        X_test_imputed = X_test
                    
                    y_pred = model.predict(X_test_imputed)
                    y_pred_proba = None
                    if hasattr(model, 'predict_proba'):
                        try:
                            y_pred_proba = model.predict_proba(X_test_imputed)
                        except:
                            pass
                    
                    # Calculate metrics
                    metrics = calculate_metrics(
                        st.session_state.y_test,
                        pd.Series(y_pred),
                        st.session_state.problem_type,
                        y_pred_proba
                    )
                    
                    model_results[model_name] = {
                        'model': model,
                        'metrics': metrics,
                        'training_info': training_results[model_name],
                        'predictions': y_pred,
                        'predictions_proba': y_pred_proba
                    }
                except Exception as e:
                    st.error(f"❌ {model_name} değerlendirilemedi: {e}")
                    logger.error(f"Error evaluating {model_name}: {e}", exc_info=True)
        
        st.session_state.model_results = model_results
        
        # Find best model
        if model_results:
            best_model = get_best_model(model_results, st.session_state.problem_type)
            st.session_state.best_model = best_model
        
        st.rerun()
    
    # Model Değerlendirme - Her zaman görünür
    st.markdown("### 📊 Model Değerlendirme")
    
    if hasattr(st.session_state, 'model_results') and st.session_state.model_results:
        # Update best model if needed
        if hasattr(st.session_state, 'best_model') and st.session_state.best_model:
            if st.session_state.best_model not in st.session_state.model_results:
                best_model = get_best_model(st.session_state.model_results, st.session_state.problem_type)
                st.session_state.best_model = best_model
        
        # Show best model
        if hasattr(st.session_state, 'best_model') and st.session_state.best_model:
            st.markdown(f"""
            <div style='
                background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                padding: 20px;
                border-radius: 10px;
                margin: 10px 0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-align: center;
            '>
                <h3 style='color: white; margin: 0;'>🏆 En İyi Model: {st.session_state.best_model}</h3>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        '>
            <div style='
                display: flex;
                align-items: center;
                color: #856404;
            '>
                <span style='font-size: 1.5em; margin-right: 10px;'>⚠️</span>
                <strong>Henüz model eğitilmedi.</strong>
            </div>
            <p style='color: #856404; margin: 8px 0 0 0; font-size: 0.95em;'>
                Modelleri eğitmek için yukarıdaki <strong>"Modelleri Eğit"</strong> butonunu kullanın.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Eğitilmiş Modeller - Her zaman görünür
    st.markdown("""
    <style>
        div[data-testid="column"]:first-of-type > div[data-testid="stVerticalBlock"] {
            display: flex !important;
            align-items: center !important;
        }
    </style>
    """, unsafe_allow_html=True)
    header_col1, header_col2 = st.columns([3, 1], vertical_alignment="center")
    with header_col1:
        st.markdown("### ✅ Eğitilmiş Modeller")
    with header_col2:
        if hasattr(st.session_state, 'trained_models') and st.session_state.trained_models:
            if st.button("↶ Tümünü Geri Al", key="undo_all_models", width='stretch', type="secondary"):
                st.session_state.trained_models = {}
                if hasattr(st.session_state, 'training_results'):
                    st.session_state.training_results = {}
                if hasattr(st.session_state, 'model_results'):
                    st.session_state.model_results = {}
                if hasattr(st.session_state, 'best_model'):
                    st.session_state.best_model = None
                st.success("✅ Tüm modeller geri alındı")
                st.rerun()
        else:
            st.empty()
    
    # Display trained models or empty message
    if hasattr(st.session_state, 'trained_models') and st.session_state.trained_models:
        models_list = list(st.session_state.trained_models.keys())
        num_cols = 2
        cols = st.columns(num_cols)
        
        for idx, model_name in enumerate(models_list):
            with cols[idx % num_cols]:
                # Get training info for this model
                training_info = st.session_state.training_results.get(model_name, {}) if hasattr(st.session_state, 'training_results') else {}
                
                # Check if optimized
                is_optimized = training_info.get('optimization_method') == 'grid_search' and training_info.get('best_params')
                
                # Border color and icon
                border_color = "#9c27b0" if is_optimized else "#4caf50"
                icon = "🔧" if is_optimized else "✅"
                
                # Create model card HTML
                if is_optimized:
                    model_card_html = f"""
                    <div style='
                        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                        padding: 12px;
                        border-radius: 8px;
                        box-shadow: 0 3px 8px rgba(0,0,0,0.1);
                        border-left: 3px solid {border_color};
                        margin-bottom: 12px;
                    '>
                        <div style='
                            display: flex;
                            align-items: center;
                            margin-bottom: 5px;
                        '>
                            <span style='font-size: 1.3em; margin-right: 10px;'>{icon}</span>
                            <strong style='color: #2d3748; font-size: 1em;'>{model_name}</strong>
                            <span style='color: #9c27b0; font-size: 0.85em; margin-left: 8px; font-weight: 600;'>(Optimize Edildi)</span>
                        </div>
                    </div>
                    """
                else:
                    model_card_html = f"""
                    <div style='
                        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                        padding: 12px;
                        border-radius: 8px;
                        box-shadow: 0 3px 8px rgba(0,0,0,0.1);
                        border-left: 3px solid {border_color};
                        margin-bottom: 12px;
                    '>
                        <div style='
                            display: flex;
                            align-items: center;
                            margin-bottom: 5px;
                        '>
                            <span style='font-size: 1.3em; margin-right: 10px;'>{icon}</span>
                            <strong style='color: #2d3748; font-size: 1em;'>{model_name}</strong>
                        </div>
                    </div>
                    """
                
                st.markdown(model_card_html, unsafe_allow_html=True)
                
                # Show optimization info if available
                if is_optimized and training_info.get('best_params'):
                    with st.expander(f"🔧 {model_name} - Optimizasyon Detayları", expanded=False):
                        st.markdown("#### 🎯 En İyi Parametreler:")
                        for param_name, param_value in training_info['best_params'].items():
                            st.markdown(f"- **{param_name}**: `{param_value}`")
                        
                        if training_info.get('best_cv_score') is not None:
                            st.markdown(f"**En İyi CV Skoru:** {training_info['best_cv_score']:.4f}")
                        
                        if training_info.get('n_param_combinations'):
                            st.markdown(f"**Test Edilen Kombinasyon:** {training_info['n_param_combinations']}")
                        
                        st.markdown(f"**Optimizasyon Yöntemi:** Grid Search")
                        if training_info.get('cv_folds'):
                            st.markdown(f"**CV Folds:** {training_info.get('cv_folds', st.session_state.cv_folds)}")
                
                if st.button("↶ Geri Al", key=f"undo_model_{model_name}", width='stretch'):
                    if model_name in st.session_state.trained_models:
                        del st.session_state.trained_models[model_name]
                    if hasattr(st.session_state, 'training_results') and model_name in st.session_state.training_results:
                        del st.session_state.training_results[model_name]
                    if hasattr(st.session_state, 'model_results') and model_name in st.session_state.model_results:
                        del st.session_state.model_results[model_name]
                    if hasattr(st.session_state, 'best_model') and st.session_state.best_model == model_name:
                        if st.session_state.model_results:
                            new_best_model = get_best_model(st.session_state.model_results, st.session_state.problem_type)
                            st.session_state.best_model = new_best_model
                        else:
                            st.session_state.best_model = None
                    st.success(f"✅ {model_name} geri alındı")
                    st.rerun()
    else:
        st.markdown("""
        <div style='
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        '>
            <div style='
                display: flex;
                align-items: center;
                color: #856404;
            '>
                <span style='font-size: 1.5em; margin-right: 10px;'>⚠️</span>
                <strong>Henüz model eğitilmedi.</strong>
            </div>
            <p style='color: #856404; margin: 8px 0 0 0; font-size: 0.95em;'>
                Modelleri eğitmek için yukarıdaki <strong>"Modelleri Eğit"</strong> butonunu kullanın.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    with nav_col1:
        if st.button("← Geri", width='stretch'):
            st.session_state.model_selection_step = 3
            st.rerun()
    with nav_col2:
        if st.button("⏭️ Atla", width='stretch'):
            st.session_state.model_selection_step = 5
            st.rerun()
    with nav_col3:
        if st.button("İleri →", type="primary", width='stretch', disabled=not (hasattr(st.session_state, 'model_results') and st.session_state.model_results)):
            st.session_state.model_selection_step = 5
            st.rerun()

# STEP 5: Model Evaluation
elif current_step == 5:
    st.header("📊 Adım 5: Model Değerlendirme")
    
    if not st.session_state.model_results:
        st.warning("⚠️ Model sonuçları bulunamadı! Lütfen geri dönüp modelleri eğitin.")
        model_results = {}
    else:
        model_results = st.session_state.model_results
    
    # Display metrics for each model
    for model_name, results in model_results.items():
        training_info = results.get('training_info', {})
        is_optimized = training_info.get('optimization_method') == 'grid_search' and training_info.get('best_params')
        model_title = f"**{model_name}**" + (" 🔧 (Optimize Edildi)" if is_optimized else "")
        
        with st.expander(f"{model_title} - Metrikler", expanded=(model_name == st.session_state.best_model)):
            metrics = results['metrics']
            
            if st.session_state.problem_type in ['binary_classification', 'multiclass_classification']:
                # Metrikleri mor kartlar içinde göster - 5 sütun (ROC AUC dahil)
                col1, col2, col3, col4, col5 = st.columns(5)
                
                # Accuracy
                with col1:
                    accuracy_val = metrics.get('accuracy', 0)
                    st.markdown(f"""
                    <div style='
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 12px;
                        border-radius: 8px;
                        color: white;
                        text-align: center;
                        margin-bottom: 10px;
                    '>
                        <div style='font-size: 0.75em; opacity: 0.9; margin-bottom: 5px;'>Accuracy</div>
                        <div style='font-size: 1.1em; font-weight: bold;'>{accuracy_val:.4f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Precision
                with col2:
                    precision_val = metrics.get('precision', 0)
                    st.markdown(f"""
                    <div style='
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 12px;
                        border-radius: 8px;
                        color: white;
                        text-align: center;
                        margin-bottom: 10px;
                    '>
                        <div style='font-size: 0.75em; opacity: 0.9; margin-bottom: 5px;'>Precision</div>
                        <div style='font-size: 1.1em; font-weight: bold;'>{precision_val:.4f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Recall
                with col3:
                    recall_val = metrics.get('recall', 0)
                    st.markdown(f"""
                    <div style='
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 12px;
                        border-radius: 8px;
                        color: white;
                        text-align: center;
                        margin-bottom: 10px;
                    '>
                        <div style='font-size: 0.75em; opacity: 0.9; margin-bottom: 5px;'>Recall</div>
                        <div style='font-size: 1.1em; font-weight: bold;'>{recall_val:.4f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # F1 Score
                with col4:
                    f1_val = metrics.get('f1_score', 0)
                    st.markdown(f"""
                    <div style='
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 12px;
                        border-radius: 8px;
                        color: white;
                        text-align: center;
                        margin-bottom: 10px;
                    '>
                        <div style='font-size: 0.75em; opacity: 0.9; margin-bottom: 5px;'>F1 Score</div>
                        <div style='font-size: 1.1em; font-weight: bold;'>{f1_val:.4f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # ROC AUC (binary classification için)
                with col5:
                    if st.session_state.problem_type == 'binary_classification' and 'roc_auc' in metrics:
                        roc_auc_val = metrics.get('roc_auc', 0)
                        st.markdown(f"""
                        <div style='
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 12px;
                            border-radius: 8px;
                            color: white;
                            text-align: center;
                            margin-bottom: 10px;
                        '>
                            <div style='font-size: 0.75em; opacity: 0.9; margin-bottom: 5px;'>ROC AUC</div>
                            <div style='font-size: 1.1em; font-weight: bold;'>{roc_auc_val:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Multiclass için boş bırak veya başka bir metrik göster
                        st.empty()
                
                # Confusion Matrix
                if 'confusion_matrix' in metrics:
                    st.markdown("**Confusion Matrix:**")
                    cm = np.array(metrics['confusion_matrix'])
                    fig = px.imshow(
                        cm,
                        labels=dict(x="Tahmin", y="Gerçek"),
                        x=[f"Class {i}" for i in range(len(cm))],
                        y=[f"Class {i}" for i in range(len(cm))],
                        text_auto=True,
                        aspect="auto"
                    )
                    st.plotly_chart(fig, width='stretch', key=f"confusion_matrix_{model_name}")
            
            else:  # Regression
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("R² Score", f"{metrics.get('r2_score', 0):.4f}")
                with col2:
                    st.metric("RMSE", f"{metrics.get('rmse', 0):.4f}")
                with col3:
                    st.metric("MAE", f"{metrics.get('mae', 0):.4f}")
                with col4:
                    st.metric("Adjusted R²", f"{metrics.get('adjusted_r2', 0):.4f}")
                
                # Prediction vs Actual scatter plot
                if 'predictions' in results:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=st.session_state.y_test.values,
                        y=results['predictions'],
                        mode='markers',
                        name='Tahminler',
                        marker=dict(color='blue', opacity=0.6)
                    ))
                    # Perfect prediction line
                    min_val = min(st.session_state.y_test.min(), results['predictions'].min())
                    max_val = max(st.session_state.y_test.max(), results['predictions'].max())
                    fig.add_trace(go.Scatter(
                        x=[min_val, max_val],
                        y=[min_val, max_val],
                        mode='lines',
                        name='Mükemmel Tahmin',
                        line=dict(color='red', dash='dash')
                    ))
                    fig.update_layout(
                        title="Tahmin vs Gerçek",
                        xaxis_title="Gerçek Değerler",
                        yaxis_title="Tahmin Edilen Değerler"
                    )
                    st.plotly_chart(fig, width='stretch', key=f"pred_vs_actual_{model_name}")
    
    # Navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    with nav_col1:
        if st.button("← Geri", width='stretch'):
            st.session_state.model_selection_step = 4
            st.rerun()
    with nav_col2:
        if st.button("⏭️ Atla", width='stretch'):
            st.session_state.model_selection_step = 6
            st.rerun()
    with nav_col3:
        if st.button("İleri →", type="primary", width='stretch'):
            st.session_state.model_selection_step = 6
            st.rerun()

# STEP 6: Model Comparison
elif current_step == 6:
    st.header("⚖️ Adım 6: Model Karşılaştırma")
    
    if not hasattr(st.session_state, 'model_results') or not st.session_state.model_results:
        st.warning("⚠️ Model sonuçları bulunamadı! Lütfen geri dönüp modelleri eğitin.")
        model_results = {}
    else:
        model_results = st.session_state.model_results
    
    if model_results:
        # Best Model Display
        if hasattr(st.session_state, 'best_model') and st.session_state.best_model:
            best_model = st.session_state.best_model
            best_metrics = model_results[best_model]['metrics']
            
            st.markdown(f"""
            <div style='
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                color: white;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            '>
                <h3 style='color: white; margin: 0;'>🏆 En İyi Model: <strong>{best_model}</strong></h3>
            </div>
            """, unsafe_allow_html=True)
        
        # Model Comparison Table
        st.markdown("### 📊 Model Karşılaştırma Tablosu")
        comparison_df = create_comparison_table(model_results, st.session_state.problem_type)
        st.dataframe(comparison_df, width='stretch', hide_index=True)
        
        # Metric Visualizations with Carousel
        st.markdown("### 📈 Metrik Görselleştirmeleri")
        
        # Initialize carousel index for metrics
        metric_carousel_key = 'metric_carousel_index'
        if metric_carousel_key not in st.session_state:
            st.session_state[metric_carousel_key] = 0
        
        # Collect all metrics to plot
        all_metrics_data = []
        
        if st.session_state.problem_type in ['binary_classification', 'multiclass_classification']:
            # Classification Metrics
            metrics_to_plot = ['accuracy', 'precision', 'recall', 'f1_score']
            if any('roc_auc' in model_results[m]['metrics'] for m in model_results):
                metrics_to_plot.append('roc_auc')
            
            # Prepare data for all metrics
            for metric in metrics_to_plot:
                metric_display_names = {
                    'accuracy': 'Accuracy',
                    'precision': 'Precision',
                    'recall': 'Recall',
                    'f1_score': 'F1 Score',
                    'roc_auc': 'ROC AUC'
                }
                
                metric_name = metric_display_names.get(metric, metric)
                
                # Collect data
                model_names = []
                metric_values = []
                colors = []
                
                for model_name in comparison_df['Model'].values:
                    if model_name in model_results:
                        metrics = model_results[model_name]['metrics']
                        if metric in metrics:
                            model_names.append(model_name)
                            value = metrics[metric]
                            metric_values.append(value)
                            
                            # Color: best model gets gold, others get purple
                            if hasattr(st.session_state, 'best_model') and model_name == st.session_state.best_model:
                                colors.append('#FFD700')  # Gold
                            else:
                                colors.append('#667eea')  # Purple
                
                if model_names and metric_values:
                    all_metrics_data.append({
                        'metric': metric,
                        'metric_name': metric_name,
                        'model_names': model_names,
                        'metric_values': metric_values,
                        'colors': colors
                    })
        
        else:
            # Regression Metrics
            metrics_to_plot = ['r2_score', 'rmse', 'mae', 'adjusted_r2']
            
            for metric in metrics_to_plot:
                metric_display_names = {
                    'r2_score': 'R² Score',
                    'adjusted_r2': 'Adjusted R²',
                    'rmse': 'RMSE',
                    'mae': 'MAE'
                }
                
                metric_name = metric_display_names.get(metric, metric)
                
                # Collect data
                model_names = []
                metric_values = []
                colors = []
                
                for model_name in comparison_df['Model'].values:
                    if model_name in model_results:
                        metrics = model_results[model_name]['metrics']
                        if metric in metrics:
                            model_names.append(model_name)
                            value = metrics[metric]
                            metric_values.append(value)
                            
                            # Color: best model gets gold
                            if hasattr(st.session_state, 'best_model') and model_name == st.session_state.best_model:
                                colors.append('#FFD700')
                            else:
                                colors.append('#667eea')
                
                if model_names and metric_values:
                    all_metrics_data.append({
                        'metric': metric,
                        'metric_name': metric_name,
                        'model_names': model_names,
                        'metric_values': metric_values,
                        'colors': colors,
                        'is_lower_better': metric in ['rmse', 'mae']
                    })
        
        # Add training time to metrics
        training_times = []
        model_names_time = []
        colors_time = []
        
        for model_name in comparison_df['Model'].values:
            if model_name in model_results:
                training_info = model_results[model_name].get('training_info', {})
                time_val = training_info.get('training_time', 0)
                if time_val > 0:
                    training_times.append(time_val)
                    model_names_time.append(model_name)
                    
                    if hasattr(st.session_state, 'best_model') and model_name == st.session_state.best_model:
                        colors_time.append('#FFD700')
                    else:
                        colors_time.append('#667eea')
        
        if training_times:
            all_metrics_data.append({
                'metric': 'training_time',
                'metric_name': 'Eğitim Süresi',
                'model_names': model_names_time,
                'metric_values': training_times,
                'colors': colors_time,
                'is_time': True
            })
        
        # Display metrics in carousel with navigation buttons
        if all_metrics_data:
            # Get current index from session state
            current_metric_index = st.session_state[metric_carousel_key]
            current_metric_index = min(current_metric_index, len(all_metrics_data) - 1)
            
            # Get updated index after button clicks
            current_metric_index = st.session_state[metric_carousel_key]
            current_metric_index = min(current_metric_index, len(all_metrics_data) - 1)
            
            # Display current metric chart
            with st.container():
                # Get metric descriptions (shared for all charts)
                metric_descriptions = {
                    'Accuracy': {
                        'title': 'Accuracy (Doğruluk)',
                        'description': 'Modelin tüm tahminlerinin doğru olma oranıdır. 0 ile 1 arasında değer alır. 1\'e yakın değerler daha iyi performansı gösterir. Ancak dengesiz veri setlerinde yanıltıcı olabilir.',
                        'formula': 'Accuracy = (TP + TN) / (TP + TN + FP + FN)',
                        'interpretation': 'Yüksek accuracy, modelin genel olarak doğru tahminler yaptığını gösterir.'
                    },
                    'Precision': {
                        'title': 'Precision (Kesinlik)',
                        'description': 'Modelin pozitif olarak tahmin ettiği örneklerin gerçekten pozitif olma oranıdır. False positive\'leri minimize etmek için önemlidir.',
                        'formula': 'Precision = TP / (TP + FP)',
                        'interpretation': 'Yüksek precision, modelin pozitif tahminlerinin çoğunun doğru olduğunu gösterir. Spam tespiti gibi durumlarda kritiktir.'
                    },
                    'Recall': {
                        'title': 'Recall (Duyarlılık)',
                        'description': 'Gerçek pozitif örneklerin ne kadarının doğru şekilde tespit edildiğini gösterir. False negative\'leri minimize etmek için önemlidir.',
                        'formula': 'Recall = TP / (TP + FN)',
                        'interpretation': 'Yüksek recall, modelin gerçek pozitifleri kaçırmadığını gösterir. Hastalık teşhisi gibi durumlarda kritiktir.'
                    },
                    'F1 Score': {
                        'title': 'F1 Score',
                        'description': 'Precision ve Recall metriklerinin harmonik ortalamasıdır. İki metrik arasında denge kurmak için kullanılır.',
                        'formula': 'F1 = 2 × (Precision × Recall) / (Precision + Recall)',
                        'interpretation': 'F1 score, hem precision hem de recall\'ı dengeli bir şekilde değerlendirir. 0 ile 1 arasında değer alır, 1\'e yakın değerler daha iyidir.'
                    },
                    'ROC AUC': {
                        'title': 'ROC AUC (Receiver Operating Characteristic - Area Under Curve)',
                        'description': 'Modelin sınıfları ayırt etme yeteneğini ölçer. Eşik değerinden bağımsız olarak model performansını değerlendirir.',
                        'formula': 'ROC AUC = Eğri altındaki alan',
                        'interpretation': '0.5 ile 1 arasında değer alır. 0.5 rastgele tahmin, 1 mükemmel ayırt etme anlamına gelir. 0.7+ iyi, 0.8+ çok iyi, 0.9+ mükemmel kabul edilir.'
                    },
                    'R² Score': {
                        'title': 'R² Score (R-Kare / Belirleme Katsayısı)',
                        'description': 'Modelin bağımsız değişkenlerin bağımlı değişkeni ne kadar açıkladığını gösterir. 0 ile 1 arasında değer alır.',
                        'formula': 'R² = 1 - (SS_res / SS_tot)',
                        'interpretation': '1\'e yakın değerler modelin veriyi iyi açıkladığını gösterir. Negatif değerler modelin basit ortalamadan daha kötü olduğunu gösterir.'
                    },
                    'Adjusted R²': {
                        'title': 'Adjusted R² (Düzeltilmiş R-Kare)',
                        'description': 'R²\'nin özellik sayısına göre düzeltilmiş halidir. Model karmaşıklığını hesaba katarak daha adil bir değerlendirme sağlar.',
                        'formula': 'Adjusted R² = 1 - [(1-R²)(n-1)/(n-k-1)]',
                        'interpretation': 'Özellik sayısı arttıkça R² artabilir, ancak Adjusted R² bunu düzeltir. Model seçiminde R²\'den daha güvenilirdir.'
                    },
                    'RMSE': {
                        'title': 'RMSE (Root Mean Squared Error)',
                        'description': 'Tahmin hatalarının karekök ortalamasıdır. Büyük hatalara daha fazla ağırlık verir.',
                        'formula': 'RMSE = √(Σ(yi - ŷi)² / n)',
                        'interpretation': 'Düşük değerler daha iyi performansı gösterir. Aynı birimde olduğu için yorumlanması kolaydır. Aykırı değerlerden etkilenir.'
                    },
                    'MAE': {
                        'title': 'MAE (Mean Absolute Error)',
                        'description': 'Tahmin hatalarının mutlak değerlerinin ortalamasıdır. Tüm hatalara eşit ağırlık verir.',
                        'formula': 'MAE = Σ|yi - ŷi| / n',
                        'interpretation': 'Düşük değerler daha iyi performansı gösterir. RMSE\'den daha az aykırı değerlerden etkilenir. Ortalama hata miktarını gösterir.'
                    },
                    'Eğitim Süresi': {
                        'title': 'Eğitim Süresi',
                        'description': 'Modelin eğitilmesi için geçen süreyi gösterir. Daha hızlı eğitilen modeller genellikle daha pratik kullanım sağlar.',
                        'formula': 'Eğitim Süresi = Model eğitiminin tamamlanma süresi',
                        'interpretation': 'Düşük süreler tercih edilir, ancak performansla birlikte değerlendirilmelidir. Büyük veri setlerinde önemli bir faktördür.'
                    }
                }
                
                # Prepare chart data for current metric (sadece mevcut index)
                metric_data = all_metrics_data[current_metric_index]
                
                metric_key = metric_data['metric_name']
                metric_info = metric_descriptions.get(metric_key, {
                    'title': metric_key,
                    'description': 'Bu metrik hakkında detaylı bilgi mevcut değil.',
                    'formula': '',
                    'interpretation': ''
                })
                
                # Create bar chart
                if metric_data.get('is_time'):
                    # Training time chart
                    fig = go.Figure(data=[
                        go.Bar(
                            x=metric_data['model_names'],
                            y=metric_data['metric_values'],
                            marker_color=metric_data['colors'],
                            text=[f'{t:.2f}s' for t in metric_data['metric_values']],
                            textposition='outside',
                            name=metric_data['metric_name'],
                            marker=dict(
                                line=dict(color='rgba(0,0,0,0.1)', width=1)
                            )
                        )
                    ])
                    
                    fig.update_layout(
                        title=dict(
                            text=f'<b>{metric_data["metric_name"]}</b>',
                            x=0.5,
                            xanchor='center',
                            font=dict(size=22, color='#2d3748', family='Arial, sans-serif')
                        ),
                        xaxis=dict(
                            title=dict(
                                text='Model',
                                font=dict(size=14, color='#4a5568', family='Arial, sans-serif'),
                                standoff=0
                            ),
                            tickfont=dict(size=11, color='#718096'),
                            tickangle=-45,
                            gridcolor='rgba(0,0,0,0.05)',
                            showgrid=True,
                            side='bottom'
                        ),
                        yaxis=dict(
                            title=dict(
                                text='Süre (saniye)',
                                font=dict(size=14, color='#4a5568', family='Arial, sans-serif')
                            ),
                            tickfont=dict(size=12, color='#718096'),
                            gridcolor='rgba(0,0,0,0.05)',
                            showgrid=True
                        ),
                        height=None,
                        showlegend=False,
                        plot_bgcolor='#ffffff',
                        paper_bgcolor='white',
                        margin=dict(l=25, r=15, t=15, b=50, pad=0, autoexpand=False),
                        autosize=True,
                        hovermode='x unified'
                    )
                    
                    fig.update_xaxes(automargin=False, title_standoff=5, side='bottom')
                    fig.update_yaxes(automargin=False, title_standoff=5)
                    
                    fig.update_traces(
                        textfont=dict(size=11, color='#2d3748', family='Arial, sans-serif')
                    )
                else:
                        # Metric chart
                        is_lower_better = metric_data.get('is_lower_better', False)
                        title_suffix = ' (Düşük = İyi)' if is_lower_better else ''
                        
                        fig = go.Figure(data=[
                            go.Bar(
                                x=metric_data['model_names'],
                                y=metric_data['metric_values'],
                                marker_color=metric_data['colors'],
                            text=[f'{v:.4f}' for v in metric_data['metric_values']],
                                textposition='outside',
                                name=metric_data['metric_name'],
                                marker=dict(
                                    line=dict(color='rgba(0,0,0,0.1)', width=1)
                                )
                            )
                        ])
                        
                        y_range = None
                        if not is_lower_better and metric_data['metric'] in ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc', 'r2_score', 'adjusted_r2']:
                            y_range = [0, 1.1]
                        
                        fig.update_layout(
                        title=dict(
                            text=f'<b>{metric_data["metric_name"]}{title_suffix}</b>',
                            x=0.5,
                            xanchor='center',
                            font=dict(size=18, color='#2d3748', family='Arial, sans-serif')
                        ),
                        xaxis=dict(
                            title=dict(
                                text='Model',
                                font=dict(size=14, color='#4a5568', family='Arial, sans-serif'),
                                standoff=0
                            ),
                            tickfont=dict(size=11, color='#718096'),
                            tickangle=-45,
                            gridcolor='rgba(0,0,0,0.05)',
                            showgrid=True,
                            side='bottom'
                        ),
                        yaxis=dict(
                            title=dict(
                                text=metric_data['metric_name'],
                                font=dict(size=14, color='#4a5568', family='Arial, sans-serif')
                            ),
                            tickfont=dict(size=12, color='#718096'),
                            range=y_range,
                            gridcolor='rgba(0,0,0,0.05)',
                            showgrid=True
                        ),
                            height=None,
                            showlegend=False,
                            plot_bgcolor='#ffffff',
                            paper_bgcolor='white',
                            margin=dict(l=25, r=15, t=15, b=50, pad=0, autoexpand=False),
                            autosize=True,
                            hovermode='x unified'
                        )
                        
                        fig.update_xaxes(automargin=False, title_standoff=5, side='bottom')
                        fig.update_yaxes(automargin=False, title_standoff=5)
                        
                        fig.update_traces(
                            textfont=dict(size=11, color='#2d3748', family='Arial, sans-serif')
                        )
                    
                # Convert plotly figure to JSON for rendering in iframe
                import json as json_lib
                chart_dict = fig.to_dict()
                # Escape JSON for embedding in JavaScript
                chart_json_str = json_lib.dumps(chart_dict).replace('</script>', '<\\/script>').replace('</SCRIPT>', '<\\/SCRIPT>')
                chart_id = f"chart_{current_metric_index}"
                
                # Create chart HTML with Plotly
                chart_html = f"""
                <div id="{chart_id}" style="width: 100%; height: 600px;"></div>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <script>
                    (function() {{
                        function renderChart() {{
                            if (typeof Plotly === 'undefined') {{
                                setTimeout(renderChart, 100);
                                return;
                            }}
                            
                            const chartDiv = document.getElementById('{chart_id}');
                            if (!chartDiv) {{
                                setTimeout(renderChart, 100);
                                return;
                            }}
                            
                            try {{
                                const chartDataJson = `{chart_json_str}`;
                                const chartData = JSON.parse(chartDataJson);
                                chartData.layout.margin = {{l: 50, r: 25, t: 55, b: 110, pad: 0, autoexpand: false}};
                                delete chartData.layout.height;
                                chartData.layout.autosize = true;
                                if (chartData.layout.xaxis && chartData.layout.xaxis.title) {{
                                    chartData.layout.xaxis.title.standoff = 5;
                                }}
                                if (chartData.layout.yaxis && chartData.layout.yaxis.title) {{
                                    chartData.layout.yaxis.title.standoff = 5;
                                }}
                                
                                Plotly.newPlot(chartDiv, chartData.data, chartData.layout, {{
                                    displayModeBar: false,
                                    responsive: true,
                                    autosizable: true
                                }});
                                
                                setTimeout(() => {{
                                    Plotly.Plots.resize(chartDiv);
                                }}, 100);
                                
                                window.addEventListener('resize', () => {{
                                    Plotly.Plots.resize(chartDiv);
                                }});
                            }} catch (e) {{
                                console.error('Chart rendering error:', e);
                            }}
                        }}
                        
                        if (document.readyState === 'loading') {{
                            document.addEventListener('DOMContentLoaded', renderChart);
                        }} else {{
                            renderChart();
                        }}
                    }})();
                </script>
                """
                
                # Navigation buttons and chart in columns
                col1, col2, col3 = st.columns([0.8, 5, 0.8], vertical_alignment="center")
                
                with col1:
                    st.markdown("<div style='display: flex; justify-content: center; align-items: center; height: 100%;'>", unsafe_allow_html=True)
                    if st.button("◀️", key="prev_metric", disabled=(current_metric_index == 0), width='stretch'):
                        if current_metric_index > 0:
                            st.session_state[metric_carousel_key] = current_metric_index - 1
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    # Mor kart içinde başlık ve açıklama
                    card_html_content = f"""
                    <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.95) 0%, rgba(118, 75, 162, 0.95) 100%); border-radius: 15px; padding: 15px; margin-bottom: 0; box-shadow: 0 8px 25px rgba(0,0,0,0.2); color: white;">
                        <div style="text-align: center; margin-bottom: 10px;">
                            <strong style="font-size: 1.5em; display: block; margin: 0; text-shadow: 0 2px 10px rgba(0,0,0,0.2);">{metric_info['title']} Karşılaştırması</strong>
                            <div style="font-size: 1em; opacity: 0.95; margin-top: 6px; font-weight: 500;">📊 Grafik {current_metric_index + 1}/{len(all_metrics_data)}</div>
                        </div>
                        <div style="background: rgba(255, 255, 255, 0.2); backdrop-filter: blur(10px); padding: 10px 14px; border-radius: 10px; border-left: 4px solid rgba(255, 255, 255, 0.8); box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                            <div style="font-size: 0.95em; line-height: 1.5; margin: 0; font-weight: 400;"><strong style="font-size: 1em;">📖 Açıklama:</strong> {metric_info['description']}</div>
                        </div>
                    </div>
                    """
                    components.html(card_html_content, height=200)
                    components.html(chart_html, height=600)
                
                    # Display metric info card with expandable details
                with st.expander(f"📊 {metric_info['title']} - Detaylı Bilgi", expanded=False):
                    st.markdown(f"""
                    <div style='
                        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                        padding: 15px;
                        border-radius: 8px;
                        margin: 10px 0;
                        border-left: 4px solid #667eea;
                    '>
                        <h4 style='color: #2d3748; margin-top: 0;'>📖 Açıklama</h4>
                        <p style='color: #4a5568; line-height: 1.6;'>{metric_info['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if metric_info['formula']:
                        st.markdown(f"""
                        <div style='
                            background: #fff;
                            padding: 12px;
                            border-radius: 6px;
                            margin: 10px 0;
                            border: 1px solid #dee2e6;
                        '>
                            <strong style='color: #2d3748;'>📐 Formül:</strong>
                            <code style='color: #667eea; font-size: 0.9em; display: block; margin-top: 5px;'>{metric_info['formula']}</code>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if metric_info['interpretation']:
                        st.markdown(f"""
                        <div style='
                            background: linear-gradient(135deg, #e7f3ff 0%, #d0e7ff 100%);
                            padding: 12px;
                            border-radius: 6px;
                            margin: 10px 0;
                            border-left: 4px solid #0066cc;
                        '>
                            <strong style='color: #004085;'>💡 Yorumlama:</strong>
                            <p style='color: #004085; margin: 5px 0 0 0; line-height: 1.6;'>{metric_info['interpretation']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown("<div style='display: flex; justify-content: center; align-items: center; height: 100%;'>", unsafe_allow_html=True)
                    if st.button("▶️", key="next_metric", disabled=(current_metric_index == len(all_metrics_data) - 1), width='stretch'):
                        if current_metric_index < len(all_metrics_data) - 1:
                            st.session_state[metric_carousel_key] = current_metric_index + 1
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
    
    # Navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    with nav_col1:
        if st.button("← Geri", width='stretch'):
            st.session_state.model_selection_step = 5
            st.rerun()
    with nav_col2:
        if st.button("⏭️ Atla", width='stretch'):
            st.session_state.model_selection_step = 7
            st.rerun()
    with nav_col3:
        if st.button("İleri →", type="primary", width='stretch'):
            st.session_state.model_selection_step = 7
            st.rerun()

# STEP 7: Model Interpretation
elif current_step == 7:
    st.header("🔬 Adım 7: Model Yorumlama")
    
    # Check if models are trained
    if 'trained_models' not in st.session_state or not st.session_state.trained_models:
        st.warning("⚠️ Henüz eğitilmiş model bulunmuyor. Lütfen önce modelleri eğitin.")
        if st.button("← Model Eğitimine Dön", width='stretch'):
            st.session_state.model_selection_step = 4
            st.rerun()
    else:
        trained_models = st.session_state.trained_models
        model_results = st.session_state.get('model_results', {})
        
        # Model selection
        st.markdown("### 📌 Model Seçimi")
        model_names = list(trained_models.keys())
        
        if not model_names:
            st.error("❌ Eğitilmiş model bulunamadı.")
        else:
            selected_model_name = st.selectbox(
                "Yorumlamak istediğiniz modeli seçin:",
                model_names,
                key="interpretation_model_selector"
            )
            
            if selected_model_name in trained_models:
                # Check if model_info is a dict or direct model object
                model_info = trained_models[selected_model_name]
                if isinstance(model_info, dict):
                    model = model_info.get('model')
                    training_info = model_info.get('training_info', {})
                else:
                    # Direct model object
                    model = model_info
                    training_info = {}
                
                # Get training data
                if 'X_train' in st.session_state and 'y_train' in st.session_state:
                    X_train = st.session_state.X_train
                    y_train = st.session_state.y_train
                    feature_names = list(X_train.columns)
                    
                    # Model Summary Card
                    st.markdown("### 📊 Model Özeti")
                    summary_col1, summary_col2, summary_col3 = st.columns(3)
                    
                    with summary_col1:
                        st.markdown(f"""
                        <div style='
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 15px;
                            border-radius: 8px;
                            color: white;
                            text-align: center;
                        '>
                            <strong>Model Tipi</strong><br>
                            <span style='font-size: 1.1em;'>{type(model).__name__}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with summary_col2:
                        st.markdown(f"""
                        <div style='
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 15px;
                            border-radius: 8px;
                            color: white;
                            text-align: center;
                        '>
                            <strong>Özellik Sayısı</strong><br>
                            <span style='font-size: 1.1em;'>{len(feature_names)}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with summary_col3:
                        if selected_model_name in model_results:
                            metrics = model_results[selected_model_name].get('metrics', {})
                            primary_metric = 'accuracy' if st.session_state.problem_type in ['binary_classification', 'multiclass_classification'] else 'r2_score'
                            metric_value = metrics.get(primary_metric, 'N/A')
                            metric_display = f"{metric_value:.4f}" if isinstance(metric_value, (int, float)) else str(metric_value)
                            
                            st.markdown(f"""
                            <div style='
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                padding: 15px;
                                border-radius: 8px;
                                color: white;
                                text-align: center;
                            '>
                                <strong>Performans</strong><br>
                                <span style='font-size: 1.1em;'>{metric_display}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Model Performance Summary
                    if selected_model_name in model_results:
                        metrics = model_results[selected_model_name].get('metrics', {})
                        
                        if metrics:
                            st.markdown("#### 📈 Model Performans Özeti")
                            if st.session_state.problem_type in ['binary_classification', 'multiclass_classification']:
                                perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
                                
                                accuracy_val = metrics.get('accuracy', 'N/A')
                                accuracy_display = f"{accuracy_val:.4f}" if isinstance(accuracy_val, (int, float)) else "N/A"
                                with perf_col1:
                                    st.markdown(f"""
                                    <div style='
                                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                        padding: 20px;
                                        border-radius: 12px;
                                        margin: 10px 0;
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                        text-align: center;
                                    '>
                                        <div style='color: white; font-size: 0.9em; margin-bottom: 8px; opacity: 0.9;'>Accuracy</div>
                                        <div style='color: white; font-size: 1.8em; font-weight: bold;'>{accuracy_display}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                precision_val = metrics.get('precision', 'N/A')
                                precision_display = f"{precision_val:.4f}" if isinstance(precision_val, (int, float)) else "N/A"
                                with perf_col2:
                                    st.markdown(f"""
                                    <div style='
                                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                        padding: 20px;
                                        border-radius: 12px;
                                        margin: 10px 0;
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                        text-align: center;
                                    '>
                                        <div style='color: white; font-size: 0.9em; margin-bottom: 8px; opacity: 0.9;'>Precision</div>
                                        <div style='color: white; font-size: 1.8em; font-weight: bold;'>{precision_display}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                recall_val = metrics.get('recall', 'N/A')
                                recall_display = f"{recall_val:.4f}" if isinstance(recall_val, (int, float)) else "N/A"
                                with perf_col3:
                                    st.markdown(f"""
                                    <div style='
                                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                        padding: 20px;
                                        border-radius: 12px;
                                        margin: 10px 0;
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                        text-align: center;
                                    '>
                                        <div style='color: white; font-size: 0.9em; margin-bottom: 8px; opacity: 0.9;'>Recall</div>
                                        <div style='color: white; font-size: 1.8em; font-weight: bold;'>{recall_display}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                f1_val = metrics.get('f1_score', 'N/A')
                                f1_display = f"{f1_val:.4f}" if isinstance(f1_val, (int, float)) else "N/A"
                                with perf_col4:
                                    st.markdown(f"""
                                    <div style='
                                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                        padding: 20px;
                                        border-radius: 12px;
                                        margin: 10px 0;
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                        text-align: center;
                                    '>
                                        <div style='color: white; font-size: 0.9em; margin-bottom: 8px; opacity: 0.9;'>F1 Score</div>
                                        <div style='color: white; font-size: 1.8em; font-weight: bold;'>{f1_display}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
                                
                                r2_val = metrics.get('r2_score', 'N/A')
                                r2_display = f"{r2_val:.4f}" if isinstance(r2_val, (int, float)) else "N/A"
                                with perf_col1:
                                    st.markdown(f"""
                                    <div style='
                                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                        padding: 20px;
                                        border-radius: 12px;
                                        margin: 10px 0;
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                        text-align: center;
                                    '>
                                        <div style='color: white; font-size: 0.9em; margin-bottom: 8px; opacity: 0.9;'>R² Score</div>
                                        <div style='color: white; font-size: 1.8em; font-weight: bold;'>{r2_display}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                rmse_val = metrics.get('rmse', 'N/A')
                                rmse_display = f"{rmse_val:.4f}" if isinstance(rmse_val, (int, float)) else "N/A"
                                with perf_col2:
                                    st.markdown(f"""
                                    <div style='
                                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                        padding: 20px;
                                        border-radius: 12px;
                                        margin: 10px 0;
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                        text-align: center;
                                    '>
                                        <div style='color: white; font-size: 0.9em; margin-bottom: 8px; opacity: 0.9;'>RMSE</div>
                                        <div style='color: white; font-size: 1.8em; font-weight: bold;'>{rmse_display}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                mae_val = metrics.get('mae', 'N/A')
                                mae_display = f"{mae_val:.4f}" if isinstance(mae_val, (int, float)) else "N/A"
                                with perf_col3:
                                    st.markdown(f"""
                                    <div style='
                                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                        padding: 20px;
                                        border-radius: 12px;
                                        margin: 10px 0;
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                        text-align: center;
                                    '>
                                        <div style='color: white; font-size: 0.9em; margin-bottom: 8px; opacity: 0.9;'>MAE</div>
                                        <div style='color: white; font-size: 1.8em; font-weight: bold;'>{mae_display}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                adj_r2_val = metrics.get('adjusted_r2', 'N/A')
                                adj_r2_display = f"{adj_r2_val:.4f}" if isinstance(adj_r2_val, (int, float)) else "N/A"
                                with perf_col4:
                                    st.markdown(f"""
                                    <div style='
                                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                        padding: 20px;
                                        border-radius: 12px;
                                        margin: 10px 0;
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                        text-align: center;
                                    '>
                                        <div style='color: white; font-size: 0.9em; margin-bottom: 8px; opacity: 0.9;'>Adjusted R²</div>
                                        <div style='color: white; font-size: 1.8em; font-weight: bold;'>{adj_r2_display}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Feature Importance Analysis
                    st.markdown("### 🔍 Model Yorumlanabilirliği ve Özellik Analizi")
                    
                    tab1, tab2, tab3 = st.tabs(["📊 Feature Importance", "🔄 Permutation Importance", "✨ SHAP Değerleri"])
                    
                    with tab1:
                        st.markdown("#### 📊 Feature Importance")
                        
                        # Information card with expander
                        with st.expander("📚 Model İçi Feature Importance - Detaylı Bilgi", expanded=False):
                            st.markdown("""
                            <div style='
                                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                                padding: 15px;
                                border-radius: 8px;
                                margin: 10px 0;
                                border-left: 4px solid #0ea5e9;
                            '>
                                <h4 style='color: #0369a1; margin-top: 0;'>📚 Model İçi Feature Importance Nedir?</h4>
                                <p style='color: #0c4a6e; line-height: 1.6;'>
                                    <strong>Model İçi Feature Importance</strong>, makine öğrenmesi modellerinin eğitimi sırasında her bir özelliğin (feature) modele ne kadar katkı sağladığını gösteren bir ölçümdür.
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("""
                            <div style='
                                background: #fff;
                                padding: 12px;
                                border-radius: 6px;
                                margin: 10px 0;
                                border: 1px solid #dee2e6;
                            '>
                                <strong style='color: #2d3748;'>🎯 Nasıl Çalışır?</strong>
                                <ul style='color: #4a5568; line-height: 1.6; margin: 5px 0 0 0; padding-left: 20px;'>
                                    <li><strong>Ağaç Tabanlı Modeller:</strong> Her özelliğin karar ağacında kaç kez kullanıldığına ve ne kadar bilgi kazandırdığına göre önem skoru hesaplanır.</li>
                                    <li><strong>Doğrusal Modeller:</strong> Her özelliğin katsayı (coefficient) değerinin mutlak değeri, o özelliğin önemini gösterir.</li>
                                </ul>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("""
                            <div style='
                                background: linear-gradient(135deg, #e7f3ff 0%, #d0e7ff 100%);
                                padding: 12px;
                                border-radius: 6px;
                                margin: 10px 0;
                                border-left: 4px solid #0066cc;
                            '>
                                <strong style='color: #004085;'>💡 Avantajları</strong>
                                <ul style='color: #004085; line-height: 1.6; margin: 5px 0 0 0; padding-left: 20px;'>
                                    <li>Hızlı ve kolay hesaplanır (model eğitildikten sonra otomatik olarak mevcuttur)</li>
                                    <li>Hangi özelliklerin en önemli olduğunu hızlıca gösterir</li>
                                    <li>Özellik seçimi ve model yorumlanabilirliği için kullanışlıdır</li>
                                </ul>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("""
                            <div style='
                                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                                padding: 15px;
                                border-radius: 8px;
                                margin: 10px 0;
                                border-left: 4px solid #0ea5e9;
                            '>
                                <h4 style='color: #0369a1; margin-top: 0;'>🔢 Sayısal Değerler Ne Anlama Geliyor?</h4>
                                <p style='color: #0c4a6e; line-height: 1.6; margin-bottom: 8px;'>
                                    Feature importance değerlerinin yorumlanması <strong>model tipine göre değişir</strong>:
                                </p>
                                <h6 style='color: #0369a1; margin-top: 12px; margin-bottom: 6px; font-size: 0.95em;'>🌳 Ağaç Tabanlı Modeller (Random Forest, Decision Tree, vb.):</h6>
                                <p style='color: #0c4a6e; line-height: 1.6; margin-bottom: 8px;'>
                                    Genellikle <strong>normalize edilmiş</strong> değerlerdir (toplamı 1.0). Bu durumda:
                                </p>
                                <ul style='color: #0c4a6e; line-height: 1.6; margin-bottom: 12px; padding-left: 20px;'>
                                    <li><strong>1.0 değeri:</strong> Bu özellik, modelin tüm önemini tek başına taşıyor (pratikte çok nadir)</li>
                                    <li><strong>0.5 değeri:</strong> Modelin toplam öneminin %50'sini oluşturuyor</li>
                                    <li><strong>0.1 değeri:</strong> Modelin toplam öneminin %10'unu oluşturuyor</li>
                                    <li><strong>0.0 değeri:</strong> Modele hiç katkı sağlamıyor</li>
                                </ul>
                                <h6 style='color: #0369a1; margin-top: 12px; margin-bottom: 6px; font-size: 0.95em;'>📊 Doğrusal Modeller (Linear Regression, Logistic Regression):</h6>
                                <p style='color: #0c4a6e; line-height: 1.6; margin-bottom: 8px;'>
                                    Değerler <strong>normalize edilmemiş</strong> mutlak katsayı değerleridir. Bu durumda:
                                </p>
                                <ul style='color: #0c4a6e; line-height: 1.6; margin-bottom: 0; padding-left: 20px;'>
                                    <li>Değerler 1'den büyük olabilir (örneğin 1.5, 2.3, 10.0 gibi)</li>
                                    <li>Mutlak değerler önemlidir - daha büyük değer = daha önemli özellik</li>
                                    <li>Karşılaştırma için oranlarına bakılır (örneğin 2.0 değeri, 1.0 değerinden 2 kat daha önemlidir)</li>
                                </ul>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Button to calculate feature importance
                        if st.button("📊 Feature Importance Hesapla", type="primary", key="calc_feature_importance"):
                            st.session_state[f'feature_importance_calculated_{selected_model_name}'] = True
                        
                        # Check if we should show results
                        show_results = st.session_state.get(f'feature_importance_calculated_{selected_model_name}', False)
                        
                        if show_results:
                            try:
                                feature_importance = get_feature_importance(model, feature_names)
                            
                                # Check if feature_importance is valid and not empty
                                if feature_importance and len(feature_importance) > 0:
                                    # Sort by importance
                                    sorted_importance = sorted(
                                        feature_importance.items(),
                                        key=lambda x: abs(x[1]),
                                        reverse=True
                                    )
                                    
                                    # Get top features
                                    top_n = st.slider("Gösterilecek özellik sayısı:", 5, min(50, len(feature_names)), 15, key="top_n_features")
                                    top_features = sorted_importance[:top_n]
                                    
                                    # Ensure we have features to display
                                    if top_features and len(top_features) > 0:
                                        # Create bar chart
                                        features = [f[0] for f in top_features]
                                        importances = [abs(f[1]) for f in top_features]
                                        
                                        # Create horizontal bar chart
                                        fig = go.Figure(data=[
                                            go.Bar(
                                                x=importances,
                                                y=features,
                                                orientation='h',
                                                marker=dict(
                                                    color=importances,
                                                    colorscale='Viridis',
                                                    showscale=True,
                                                    colorbar=dict(
                                                        title=dict(text="Importance", font=dict(color='black', size=12)),
                                                        tickfont=dict(color='black')
                                                    )
                                                ),
                                                text=[f'{imp:.4f}' for imp in importances],
                                                textposition='outside',
                                                textfont=dict(color='black', size=11),
                                                hovertemplate='<b>%{y}</b><br>Importance: %{x:.4f}<extra></extra>'
                                            )
                                        ])
                                        
                                        fig.update_layout(
                                            title=dict(
                                                text='<b>Feature Importance (Top Features)</b>',
                                                x=0.5,
                                                xanchor='center',
                                                font=dict(size=18, color='black')
                                            ),
                                            xaxis=dict(
                                                title=dict(text='Importance', font=dict(size=14, color='black')),
                                                tickfont=dict(color='black', size=12)
                                            ),
                                            yaxis=dict(
                                                title=dict(text='Feature', font=dict(size=14, color='black')),
                                                tickfont=dict(color='black', size=12)
                                            ),
                                            height=max(400, top_n * 25),
                                            plot_bgcolor='white',
                                            paper_bgcolor='white',
                                            margin=dict(l=150, r=50, t=60, b=50),
                                            showlegend=False,
                                            font=dict(color='black')
                                        )
                                        
                                        # Render the chart
                                        st.plotly_chart(fig, width='stretch', key=f"feature_importance_{selected_model_name}")
                                        
                                        # Top features table
                                        try:
                                            analysis = analyze_feature_importance(feature_importance, top_n=top_n)
                                            st.markdown("#### 🏆 En Önemli Özellikler")
                                            top_df = pd.DataFrame(analysis['top_features'])
                                            top_df.columns = ['Özellik', 'Importance']
                                            top_df['Sıra'] = range(1, len(top_df) + 1)
                                            top_df = top_df[['Sıra', 'Özellik', 'Importance']]
                                            st.dataframe(top_df, width='stretch', hide_index=True)
                                        except Exception as analysis_error:
                                            st.warning(f"⚠️ Tablo oluşturulamadı: {str(analysis_error)}")
                                    else:
                                        st.warning("⚠️ Görüntülenecek özellik bulunamadı.")
                                else:
                                    st.warning("⚠️ Bu model için feature importance hesaplanamadı. Model henüz eğitilmemiş olabilir veya bu model tipi feature importance desteklemiyor olabilir.")
                                
                            except Exception as e:
                                st.error(f"❌ Feature importance hesaplanırken hata oluştu: {str(e)}")
                                import traceback
                                st.code(traceback.format_exc())
                    
                    with tab2:
                        st.markdown("#### Permutation Importance")
                        
                        # Information card with expander
                        with st.expander("🔄 Permutation Importance - Detaylı Bilgi", expanded=False):
                            st.markdown("""
                            <div style='
                                background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                                padding: 15px;
                                border-radius: 8px;
                                margin: 10px 0;
                                border-left: 4px solid #f59e0b;
                            '>
                                <h4 style='color: #92400e; margin-top: 0;'>🔄 Permutation Importance Nedir?</h4>
                                <p style='color: #78350f; line-height: 1.6;'>
                                    <strong>Permutation Importance</strong>, bir özelliğin değerlerini rastgele karıştırdığınızda model performansının ne kadar düştüğünü ölçen bir yöntemdir. Bu, özelliğin gerçek önemini daha objektif bir şekilde değerlendirmenizi sağlar.
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("""
                            <div style='
                                background: #fff;
                                padding: 12px;
                                border-radius: 6px;
                                margin: 10px 0;
                                border: 1px solid #dee2e6;
                            '>
                                <strong style='color: #2d3748;'>🎯 Nasıl Çalışır?</strong>
                                <ol style='color: #4a5568; line-height: 1.6; margin: 5px 0 0 0; padding-left: 20px;'>
                                    <li>Model normal şekilde eğitilir ve temel performans skoru kaydedilir.</li>
                                    <li>Bir özelliğin değerleri rastgele karıştırılır (permutasyon).</li>
                                    <li>Model aynı veriyle tekrar test edilir ve yeni performans skoru hesaplanır.</li>
                                    <li>Performans düşüşü, o özelliğin önemini gösterir. Ne kadar çok düşerse, o kadar önemlidir.</li>
                                </ol>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("""
                            <div style='
                                background: linear-gradient(135deg, #e7f3ff 0%, #d0e7ff 100%);
                                padding: 12px;
                                border-radius: 6px;
                                margin: 10px 0;
                                border-left: 4px solid #0066cc;
                            '>
                                <strong style='color: #004085;'>💡 Avantajları</strong>
                                <ul style='color: #004085; line-height: 1.6; margin: 5px 0 0 0; padding-left: 20px;'>
                                    <li><strong>Model Bağımsız:</strong> Herhangi bir model tipiyle çalışır (ağaç, doğrusal, sinir ağı vb.)</li>
                                    <li><strong>Objektif:</strong> Modelin iç yapısına bağlı değildir, gerçek etkiyi ölçer</li>
                                    <li><strong>Güvenilir:</strong> Özellikler arasındaki korelasyonu dikkate alır</li>
                                    <li><strong>Yorumlanabilir:</strong> Negatif değerler, özelliğin modele zarar verdiğini gösterir</li>
                                </ul>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("""
                            <div style='
                                background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                                padding: 15px;
                                border-radius: 8px;
                                margin: 10px 0;
                                border-left: 4px solid #f59e0b;
                            '>
                                <h4 style='color: #92400e; margin-top: 0;'>🔢 Sayısal Değerler Ne Anlama Geliyor?</h4>
                                <p style='color: #78350f; line-height: 1.6; margin-bottom: 8px;'>
                                    Permutation importance değerleri, <strong>model performansındaki değişimi</strong> gösterir. Değerler, özelliğin karıştırılması durumunda performansın ne kadar düştüğünü (veya yükseldiğini) ölçer.
                                </p>
                                <ul style='color: #78350f; line-height: 1.6; margin-bottom: 0; padding-left: 20px;'>
                                    <li><strong>Pozitif değerler (örn: 0.05, 0.10):</strong> Özellik önemlidir. Değer ne kadar büyükse, özellik o kadar önemlidir. Örneğin 0.10 değeri, özelliğin karıştırılması durumunda model performansının 0.10 (veya %10) düştüğünü gösterir.</li>
                                    <li><strong>Yüksek pozitif değerler (örn: 0.20, 0.30):</strong> Özellik çok önemlidir. Model performansı bu özellik olmadan önemli ölçüde düşer.</li>
                                    <li><strong>Düşük pozitif değerler (örn: 0.01, 0.02):</strong> Özellik az önemlidir veya önemsizdir.</li>
                                    <li><strong>Negatif değerler (örn: -0.01, -0.05):</strong> Özellik modele zarar veriyor demektir. Bu özellik olmadan model daha iyi performans gösterir.</li>
                                    <li><strong>Sıfır değeri (0.0):</strong> Özellik modele hiç katkı sağlamıyor demektir.</li>
                                    <li><strong>Karşılaştırma:</strong> Örneğin, bir özellik 0.15 ve diğeri 0.05 değerine sahipse, ilk özellik ikincisinden <strong>3 kat daha önemlidir</strong>.</li>
                                </ul>
                                <p style='color: #78350f; line-height: 1.6; margin-top: 12px; margin-bottom: 0; font-style: italic;'>
                                    <strong>Not:</strong> Permutation importance değerleri, kullanılan scoring metrikine (accuracy, r², vb.) bağlıdır. Classification için genellikle 0-1 arası, regression için daha geniş bir aralıkta olabilir.
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Check if we have cached results
                        perm_importance = None
                        if f'perm_importance_{selected_model_name}' in st.session_state:
                            perm_importance = st.session_state[f'perm_importance_{selected_model_name}']
                        
                        # Button to calculate/recalculate
                        if st.button("🔄 Permutation Importance Hesapla", type="primary", key="calc_perm_importance"):
                            with st.spinner("Permutation importance hesaplanıyor... Bu işlem biraz zaman alabilir."):
                                try:
                                    scoring = 'accuracy' if st.session_state.problem_type in ['binary_classification', 'multiclass_classification'] else 'r2_score'
                                    perm_importance = get_permutation_importance(
                                        model, X_train, y_train,
                                        scoring=scoring,
                                        n_repeats=10
                                    )
                                    
                                    if perm_importance:
                                        # Store in session state
                                        st.session_state[f'perm_importance_{selected_model_name}'] = perm_importance
                                        st.success("✅ Permutation importance başarıyla hesaplandı!")
                                    else:
                                        st.error("❌ Permutation importance hesaplanamadı.")
                                        
                                except Exception as e:
                                    st.error(f"❌ Hata: {str(e)}")
                        
                        # Display results if available (either from button click or cached)
                        if perm_importance:
                            # Sort by importance
                            sorted_perm = sorted(
                                perm_importance.items(),
                                key=lambda x: abs(x[1]),
                                reverse=True
                            )
                            
                            top_n_perm = st.slider("Gösterilecek özellik sayısı:", 5, min(50, len(feature_names)), 15, key="top_n_perm")
                            top_perm_features = sorted_perm[:top_n_perm]
                            
                            # Create bar chart
                            perm_features = [f[0] for f in top_perm_features]
                            perm_importances = [abs(f[1]) for f in top_perm_features]
                            
                            fig = go.Figure(data=[
                                go.Bar(
                                    x=perm_importances,
                                    y=perm_features,
                                    orientation='h',
                                    marker=dict(
                                        color=perm_importances,
                                        colorscale='Plasma',
                                        showscale=True,
                                        colorbar=dict(
                                            title=dict(text="Importance", font=dict(color='black', size=12)),
                                            tickfont=dict(color='black')
                                        )
                                    ),
                                    text=[f'{imp:.4f}' for imp in perm_importances],
                                    textposition='outside',
                                    textfont=dict(color='black', size=11)
                                )
                            ])
                            
                            fig.update_layout(
                                title=dict(
                                    text='<b>Permutation Importance (Top Features)</b>',
                                    x=0.5,
                                    xanchor='center',
                                    font=dict(size=18, color='black')
                                ),
                                xaxis=dict(
                                    title=dict(text='Importance', font=dict(size=14, color='black')),
                                    tickfont=dict(color='black', size=12)
                                ),
                                yaxis=dict(
                                    title=dict(text='Feature', font=dict(size=14, color='black')),
                                    tickfont=dict(color='black', size=12)
                                ),
                                height=max(400, top_n_perm * 25),
                                plot_bgcolor='white',
                                paper_bgcolor='white',
                                margin=dict(l=150, r=50, t=60, b=50),
                                font=dict(color='black')
                            )
                            
                            st.plotly_chart(fig, width='stretch', key=f"perm_importance_chart_{selected_model_name}")
                            
                            # Show results table
                            st.markdown("#### 📊 Permutation Importance Sonuçları")
                            perm_df = pd.DataFrame(sorted_perm[:15], columns=['Özellik', 'Importance'])
                            perm_df['Sıra'] = range(1, len(perm_df) + 1)
                            perm_df = perm_df[['Sıra', 'Özellik', 'Importance']]
                            st.dataframe(perm_df, width='stretch', hide_index=True)
                    
                    with tab3:
                        st.markdown("#### SHAP (SHapley Additive exPlanations) Değerleri")
                        
                        # Information card with expander
                        with st.expander("✨ SHAP (SHapley Additive exPlanations) - Detaylı Bilgi", expanded=False):
                            st.markdown("""
                            <div style='
                                background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
                                padding: 15px;
                                border-radius: 8px;
                                margin: 10px 0;
                                border-left: 4px solid #a855f7;
                            '>
                                <h4 style='color: #6b21a8; margin-top: 0;'>✨ SHAP (SHapley Additive exPlanations) Nedir?</h4>
                                <p style='color: #581c87; line-height: 1.6;'>
                                    <strong>SHAP değerleri</strong>, oyun teorisindeki Shapley değerlerinden esinlenerek geliştirilmiş, her bir özelliğin her bir tahmine ne kadar katkıda bulunduğunu açıklayan bir yöntemdir. Her özelliğin adil payını hesaplar.
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("""
                            <div style='
                                background: #fff;
                                padding: 12px;
                                border-radius: 6px;
                                margin: 10px 0;
                                border: 1px solid #dee2e6;
                            '>
                                <strong style='color: #2d3748;'>🎯 Nasıl Çalışır?</strong>
                                <p style='color: #4a5568; line-height: 1.6; margin: 5px 0 8px 0;'>
                                    SHAP, her özelliğin modele katkısını, o özelliğin olmadığı durumla karşılaştırarak hesaplar. Tüm olası özellik kombinasyonlarını dikkate alarak, her özelliğe adil bir pay verir.
                                </p>
                                <ul style='color: #4a5568; line-height: 1.6; margin: 5px 0 0 0; padding-left: 20px;'>
                                    <li><strong>Toplamsallık:</strong> Tüm SHAP değerlerinin toplamı, modelin tahmini ile ortalama tahmin arasındaki farkı verir</li>
                                    <li><strong>Simetri:</strong> Aynı katkıyı sağlayan özellikler aynı SHAP değerini alır</li>
                                    <li><strong>Dummy Özellik:</strong> Modele katkısı olmayan özelliklerin SHAP değeri sıfırdır</li>
                                </ul>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("""
                            <div style='
                                background: linear-gradient(135deg, #e7f3ff 0%, #d0e7ff 100%);
                                padding: 12px;
                                border-radius: 6px;
                                margin: 10px 0;
                                border-left: 4px solid #0066cc;
                            '>
                                <strong style='color: #004085;'>💡 Avantajları</strong>
                                <ul style='color: #004085; line-height: 1.6; margin: 5px 0 0 0; padding-left: 20px;'>
                                    <li><strong>Bireysel Açıklama:</strong> Her tahmin için özelliklerin katkısını gösterir</li>
                                    <li><strong>Küresel Açıklama:</strong> Tüm veri seti üzerinde özelliklerin genel önemini gösterir</li>
                                    <li><strong>Teorik Temel:</strong> Oyun teorisi ile güçlü matematiksel temellere dayanır</li>
                                    <li><strong>Görselleştirme:</strong> SHAP değerleri görsel olarak çok etkili şekilde gösterilebilir</li>
                                </ul>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("""
                            <div style='
                                background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
                                padding: 15px;
                                border-radius: 8px;
                                margin: 10px 0;
                                border-left: 4px solid #a855f7;
                            '>
                                <h4 style='color: #6b21a8; margin-top: 0;'>🔢 Sayısal Değerler Ne Anlama Geliyor?</h4>
                                <p style='color: #581c87; line-height: 1.6; margin-bottom: 8px;'>
                                    SHAP değerleri, her bir özelliğin <strong>model tahminine ne kadar katkıda bulunduğunu</strong> gösterir. Grafikte gösterilen değerler, tüm örnekler üzerinden hesaplanan <strong>ortalama mutlak SHAP değerleridir</strong>.
                                </p>
                                <ul style='color: #581c87; line-height: 1.6; margin-bottom: 0; padding-left: 20px;'>
                                    <li><strong>Yüksek pozitif değerler (örn: 0.5, 1.0, 2.0):</strong> Özellik çok önemlidir. Bu özellik, model tahminlerine büyük katkı sağlar. Değer ne kadar büyükse, özellik o kadar önemlidir.</li>
                                    <li><strong>Orta pozitif değerler (örn: 0.1, 0.2, 0.3):</strong> Özellik orta düzeyde önemlidir. Model tahminlerine makul bir katkı sağlar.</li>
                                    <li><strong>Düşük pozitif değerler (örn: 0.01, 0.05):</strong> Özellik az önemlidir veya önemsizdir.</li>
                                    <li><strong>Sıfır değeri (0.0):</strong> Özellik modele hiç katkı sağlamıyor demektir.</li>
                                    <li><strong>Karşılaştırma:</strong> Örneğin, bir özellik 0.6 ve diğeri 0.2 değerine sahipse, ilk özellik ikincisinden <strong>3 kat daha önemlidir</strong>.</li>
                                    <li><strong>Mutlak Değer:</strong> Grafikte gösterilen değerler mutlak değerlerdir (her zaman pozitif). Gerçek SHAP değerleri pozitif veya negatif olabilir - pozitif değerler tahmini artırır, negatif değerler azaltır.</li>
                                </ul>
                                <p style='color: #581c87; line-height: 1.6; margin-top: 12px; margin-bottom: 0; font-style: italic;'>
                                    <strong>Not:</strong> SHAP değerlerinin ölçeği, veri setinize ve modelinize bağlıdır. Önemli olan değerlerin birbirine göre oranlarıdır. Hangi özellik daha büyük değere sahipse, o özellik daha önemlidir.
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Check if we have cached results
                        shap_result = None
                        if f'shap_values_{selected_model_name}' in st.session_state:
                            shap_result = st.session_state[f'shap_values_{selected_model_name}']
                        
                        # Button to calculate/recalculate
                        if st.button("✨ SHAP Değerlerini Hesapla", type="primary", key="calc_shap"):
                            with st.spinner("SHAP değerleri hesaplanıyor... Bu işlem biraz zaman alabilir."):
                                try:
                                    shap_result = calculate_shap_values(model, X_train, max_samples=100)
                                    
                                    if shap_result:
                                        # Store in session state
                                        st.session_state[f'shap_values_{selected_model_name}'] = shap_result
                                        st.success("✅ SHAP değerleri başarıyla hesaplandı!")
                                    else:
                                        st.warning("⚠️ SHAP kütüphanesi yüklü değil veya hesaplama başarısız oldu. SHAP yüklemek için: `pip install shap`")
                                        
                                except ImportError:
                                    st.error("❌ SHAP kütüphanesi yüklü değil. Yüklemek için: `pip install shap`")
                                except Exception as e:
                                    st.error(f"❌ Hata: {str(e)}")
                        
                        # Display results if available (either from button click or cached)
                        if shap_result:
                            mean_shap = shap_result.get('mean_abs_shap', {})
                            
                            if mean_shap:
                                # Ensure mean_shap is a dict and values are numeric
                                if isinstance(mean_shap, dict):
                                    # Convert values to float if they are lists or other types
                                    mean_shap_clean = {}
                                    for key, value in mean_shap.items():
                                        try:
                                            if isinstance(value, (list, np.ndarray)):
                                                # If it's a list/array, take the mean or first value
                                                if len(value) > 0:
                                                    mean_shap_clean[key] = float(np.mean(value))
                                                else:
                                                    mean_shap_clean[key] = 0.0
                                            elif isinstance(value, (int, float)):
                                                mean_shap_clean[key] = float(value)
                                            elif hasattr(value, '__float__'):
                                                mean_shap_clean[key] = float(value)
                                            else:
                                                mean_shap_clean[key] = 0.0
                                        except (ValueError, TypeError):
                                            mean_shap_clean[key] = 0.0
                                    mean_shap = mean_shap_clean
                                    
                                    # Sort by SHAP importance
                                    sorted_shap = sorted(
                                        mean_shap.items(),
                                        key=lambda x: abs(float(x[1])) if isinstance(x[1], (int, float)) or hasattr(x[1], '__float__') else 0.0,
                                        reverse=True
                                    )
                                        
                                    top_n_shap = st.slider("Gösterilecek özellik sayısı:", 5, min(50, len(feature_names)), 15, key="top_n_shap")
                                    top_shap_features = sorted_shap[:top_n_shap]
                                        
                                        # Create bar chart
                                    shap_features = [f[0] for f in top_shap_features]
                                shap_importances = []
                                for f in top_shap_features:
                                    try:
                                        val = f[1]
                                        if isinstance(val, (list, np.ndarray)):
                                            val = float(np.mean(val)) if len(val) > 0 else 0.0
                                        else:
                                            val = float(val)
                                        shap_importances.append(abs(val))
                                    except (ValueError, TypeError):
                                        shap_importances.append(0.0)
                                        
                                        fig = go.Figure(data=[
                                            go.Bar(
                                                x=shap_importances,
                                                y=shap_features,
                                                orientation='h',
                                                marker=dict(
                                                    color=shap_importances,
                                                    colorscale='Cividis',
                                                    showscale=True,
                                            colorbar=dict(
                                                title=dict(text="Mean |SHAP|", font=dict(color='black', size=12)),
                                                tickfont=dict(color='black')
                                            )
                                                ),
                                                text=[f'{imp:.4f}' for imp in shap_importances],
                                        textposition='outside',
                                        textfont=dict(color='black', size=11)
                                            )
                                        ])
                                        
                                        fig.update_layout(
                                            title=dict(
                                                text='<b>Mean Absolute SHAP Values (Top Features)</b>',
                                                x=0.5,
                                                xanchor='center',
                                        font=dict(size=18, color='black')
                                            ),
                                    xaxis=dict(
                                        title=dict(text='Mean |SHAP|', font=dict(size=14, color='black')),
                                        tickfont=dict(color='black', size=12)
                                    ),
                                    yaxis=dict(
                                        title=dict(text='Feature', font=dict(size=14, color='black')),
                                        tickfont=dict(color='black', size=12)
                                    ),
                                            height=max(400, top_n_shap * 25),
                                            plot_bgcolor='white',
                                            paper_bgcolor='white',
                                    margin=dict(l=150, r=50, t=60, b=50),
                                    font=dict(color='black')
                                        )
                                        
                                st.plotly_chart(fig, width='stretch', key=f"shap_chart_{selected_model_name}")
                                        
                                # Show results table
                                st.markdown("#### 📊 SHAP Sonuçları")
                                shap_df = pd.DataFrame(sorted_shap[:15], columns=['Özellik', 'Mean |SHAP|'])
                                shap_df['Sıra'] = range(1, len(shap_df) + 1)
                                shap_df = shap_df[['Sıra', 'Özellik', 'Mean |SHAP|']]
                                st.dataframe(shap_df, width='stretch', hide_index=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.error("❌ Eğitim verisi bulunamadı. Lütfen önce modelleri eğitin.")
    
    # Navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    with nav_col1:
        if st.button("← Geri", width='stretch'):
            st.session_state.model_selection_step = 6
            st.rerun()
    with nav_col2:
        if st.button("⏭️ Atla", width='stretch'):
            st.session_state.model_selection_step = 8
            st.rerun()
    with nav_col3:
        if st.button("İleri →", type="primary", width='stretch'):
            st.session_state.model_selection_step = 8
            st.rerun()

# STEP 8: Model Download
elif current_step == 8:
    st.header("💾 Adım 8: Model İndirme")
                        
    # Check if models are trained
    if 'model_results' in st.session_state and st.session_state.model_results:
        model_results = st.session_state.model_results
        
        if model_results:
            st.markdown("### 📋 Eğitilen Modeller")
            
            # Display model list
            model_names = list(model_results.keys())
            selected_model = st.selectbox(
                "İndirmek istediğiniz modeli seçin:",
                model_names,
                key="download_model_selector"
            )
            
            if selected_model:
                # Get model data
                model_data = model_results[selected_model]
                model = model_data.get('model')
                metrics = model_data.get('metrics', {})
                
                # Display model info
                st.markdown("#### 📊 Seçilen Model Bilgileri")
                info_col1, info_col2, info_col3 = st.columns(3)
                
                with info_col1:
                    st.markdown(f"""
                    <div style='
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 15px;
                        border-radius: 8px;
                        color: white;
                        text-align: center;
                    '>
                        <strong>Model Tipi</strong><br>
                        <span style='font-size: 1.1em;'>{type(model).__name__ if model else 'N/A'}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with info_col2:
                    primary_metric = 'accuracy' if st.session_state.problem_type in ['binary_classification', 'multiclass_classification'] else 'r2_score'
                    metric_value = metrics.get(primary_metric, 'N/A')
                    metric_display = f"{metric_value:.4f}" if isinstance(metric_value, (int, float)) else str(metric_value)
                    st.markdown(f"""
                    <div style='
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 15px;
                        border-radius: 8px;
                        color: white;
                        text-align: center;
                    '>
                        <strong>Ana Metrik</strong><br>
                        <span style='font-size: 1.1em;'>{metric_display}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with info_col3:
                    st.markdown(f"""
                    <div style='
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 15px;
                        border-radius: 8px;
                        color: white;
                        text-align: center;
                    '>
                        <strong>Problem Tipi</strong><br>
                        <span style='font-size: 1.1em;'>{st.session_state.problem_type}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                # LLM Recommendations - BAĞIMSIZ MODEL SEÇİCİ
                try:
                    from backend.modules.model_selection.model_download.llm_enhancer import get_model_recommendation
                    
                    # Initialize session state for recommendation - genel öneri (model seçiminden bağımsız)
                    if 'llm_recommendation_general' not in st.session_state:
                        st.session_state.llm_recommendation_general = None
                    
                    # Collect interpretation data
                    feature_importance_data = {}
                    permutation_importance_data = {}
                    shap_data = {}
                    
                    for model_name in model_names:
                        # Feature importance
                        if f'feature_importance_{model_name}' in st.session_state:
                            feature_importance_data[model_name] = st.session_state[f'feature_importance_{model_name}']
                        
                        # Permutation importance
                        if f'perm_importance_{model_name}' in st.session_state:
                            permutation_importance_data[model_name] = st.session_state[f'perm_importance_{model_name}']
                        
                        # SHAP
                        if f'shap_values_{model_name}' in st.session_state:
                            shap_data[model_name] = st.session_state[f'shap_values_{model_name}']
                    
                    # Get LLM recommendation - genel öneri (indirme seçiminden bağımsız)
                    with st.expander("🤖 LLM Model Önerisi", expanded=False):
                        # Get general recommendation (not tied to any specific model selection)
                        current_recommendation = st.session_state.llm_recommendation_general
                        
                        # Button to get recommendation
                        if current_recommendation is None:
                            btn_col1, btn_col2 = st.columns([1, 4])
                            with btn_col1:
                                if st.button("🤖 LLM Önerileri Al", type="primary", key="get_recommendation_general"):
                                    with st.spinner("LLM analiz ediyor ve öneri hazırlıyor..."):
                                        recommendation = get_model_recommendation(
                                            model_results,
                                            st.session_state.problem_type,
                                            feature_importance_data if feature_importance_data else None,
                                            permutation_importance_data if permutation_importance_data else None,
                                            shap_data if shap_data else None
                                        )
                                        
                                        if recommendation:
                                            st.session_state.llm_recommendation_general = recommendation
                                            st.rerun()
                                        else:
                                            st.info("⚠️ LLM önerisi alınamadı. LLM servisi kullanılamıyor olabilir.")
                        else:
                            # Show recommendation
                            recommendation = current_recommendation
                            
                            # Clean up excessive whitespace while preserving markdown structure
                            import re
                            # Remove multiple consecutive newlines (more than 2)
                            cleaned_recommendation = re.sub(r'\n{3,}', '\n\n', recommendation)
                            # Remove leading/trailing whitespace from each line, but preserve markdown formatting
                            lines = cleaned_recommendation.split('\n')
                            cleaned_lines = []
                            prev_empty = False
                            
                            for line in lines:
                                stripped = line.strip()
                                # If line is empty
                                if not stripped:
                                    # Only add one empty line max between content
                                    if not prev_empty and cleaned_lines:
                                        cleaned_lines.append('')
                                        prev_empty = True
                                    continue
                                
                                prev_empty = False
                                # Preserve markdown formatting (headers, lists, bold, etc.)
                                cleaned_lines.append(stripped)
                            
                            # Remove empty lines at the beginning and end
                            while cleaned_lines and not cleaned_lines[0]:
                                cleaned_lines.pop(0)
                            while cleaned_lines and not cleaned_lines[-1]:
                                cleaned_lines.pop()
                            
                            cleaned_recommendation = '\n'.join(cleaned_lines)
                            
                            # Use components.html to render markdown in a styled container
                            # First add CSS, then render markdown normally
                            st.markdown("""
                            <style>
                                .llm-recommendation-wrapper {
                                    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                                    padding: 20px;
                                    border-radius: 8px;
                                    margin: 10px 0;
                                    border-left: 4px solid #0ea5e9;
                                }
                            </style>
                            """, unsafe_allow_html=True)
                            
                            # Render markdown content normally
                            st.markdown(cleaned_recommendation)
                            
                            # Apply wrapper style using JavaScript (runs after render)
                            st.markdown("""
                            <script>
                                (function() {
                                    const markdownContainers = document.querySelectorAll('[data-testid="stMarkdownContainer"]');
                                    if (markdownContainers.length > 0) {
                                        const lastContainer = markdownContainers[markdownContainers.length - 1];
                                        lastContainer.classList.add('llm-recommendation-wrapper');
                                    }
                                })();
                            </script>
                            """, unsafe_allow_html=True)
                            
                            # Button to get new recommendation
                            btn_col1, btn_col2 = st.columns([1, 4])
                            with btn_col1:
                                if st.button("🔄 Yeni Öneri Al", key="new_recommendation_general"):
                                    # Clear the general recommendation
                                    st.session_state.llm_recommendation_general = None
                                    st.rerun()
                except Exception as e:
                    st.warning(f"⚠️ LLM önerisi yüklenemedi: {str(e)}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Download button
                if model:
                    # Create download button
                    model_bytes = pickle.dumps(model)
                    st.download_button(
                        label="💾 Modeli İndir",
                        data=model_bytes,
                        file_name=f"{selected_model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl",
                        mime="application/octet-stream",
                        type="primary",
                        width='stretch',
                        key=f"download_{selected_model}"
                    )
                    
                    st.info("💡 İndirilen model dosyasını pickle ile yüklemek için: `import pickle; model = pickle.load(open('model.pkl', 'rb'))`")
                else:
                    st.error("❌ Model bulunamadı. Lütfen modeli tekrar eğitin.")
        else:
            st.warning("⚠️ Henüz eğitilmiş model bulunmamaktadır. Lütfen önce modelleri eğitin.")
    else:
        st.error("❌ Eğitim verisi bulunamadı. Lütfen önce modelleri eğitin.")
    
    # Navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    with nav_col1:
        if st.button("← Geri", width='stretch'):
            st.session_state.model_selection_step = 7
            st.rerun()
    with nav_col2:
        st.empty()
    with nav_col3:
        st.empty()

