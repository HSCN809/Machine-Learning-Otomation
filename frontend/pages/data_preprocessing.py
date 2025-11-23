"""Streamlit page for Data Preprocessing - Wizard-based step-by-step approach."""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import logging
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Missing values functions - from new folder structure
from backend.modules.data_preprocessing.missing_values import (
    fill_missing_values_mean,
    fill_missing_values_median,
    fill_missing_values_mode,
    fill_missing_values_forward_fill,
    fill_missing_values_backward_fill,
    fill_missing_values_interpolation,
    fill_missing_values_knn,
    fill_missing_values_drop,
    get_data_statistics,
    compare_data_statistics,
    analyze_missing_values
)

# Outlier handling functions - from new folder structure
from backend.modules.data_preprocessing.outlier import (
    remove_outliers_iqr,
    cap_outliers_iqr,
    remove_outliers_zscore,
    cap_outliers_zscore,
    remove_outliers_isolation_forest,
    remove_outliers_lof,
    apply_outlier_method,
    analyze_outliers_iqr,
    analyze_outliers_zscore,
    analyze_outliers_isolation_forest,
    analyze_outliers_lof,
    get_all_outlier_info
)

# Encoding functions - from new folder structure
from backend.modules.data_preprocessing.encoding import (
    label_encode,
    one_hot_encode,
    ordinal_encode,
    binary_encode,
    frequency_encode,
    analyze_categorical_columns,
    get_categorical_statistics
)

# Feature engineering functions - from new folder structure
from backend.modules.data_preprocessing.feature_engineering import (
    remove_duplicate_rows,
    drop_columns,
    create_numeric_feature,
    create_datetime_feature,
    create_categorical_combination,
    apply_feature_engineering_method,
    analyze_duplicate_rows,
    analyze_irrelevant_columns,
    get_feature_engineering_summary
)

# Scaling functions - from new folder structure
from backend.modules.data_preprocessing.scaling import (
    standard_scale,
    minmax_scale,
    robust_scale,
    normalize,
    power_transform,
    apply_scaling_method,
    analyze_numeric_columns,
    get_scaling_statistics
)

# LLM enhancement for preprocessing - import from specific modules
from backend.modules.data_preprocessing.missing_values.llm_enhancer import suggest_missing_values_steps
from backend.modules.data_preprocessing.outlier.llm_enhancer import suggest_outlier_steps
from backend.modules.data_preprocessing.encoding.llm_enhancer import suggest_encoding_steps
from backend.modules.data_preprocessing.scaling.llm_enhancer import suggest_scaling_steps
from backend.modules.data_upload.data_validator import get_data_summary
from backend.modules.eda.eda_visualizer import create_box_plot
from backend.modules.eda.eda_visualizer import create_missing_heatmap
from backend.modules.eda.eda_visualizer import create_histogram
from backend.modules.eda.eda_visualizer import create_scatter_plot

# Logger setup
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Veri Ön İşleme",
    page_icon="🔧",
    layout="wide"
)

# Hide default page navigation
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Flip Card Styles */
    .flip-card {
        background-color: transparent;
        width: 100%;
        height: 320px;
        perspective: 1000px;
        margin: 10px 0;
    }
    
    .flip-card-inner {
        position: relative;
        width: 100%;
        height: 100%;
        text-align: center;
        transition: transform 0.6s;
        transform-style: preserve-3d;
    }
    
    .flip-card:hover .flip-card-inner {
        transform: rotateY(180deg);
    }
    
    .flip-card-front, .flip-card-back {
        position: absolute;
        width: 100%;
        height: 100%;
        backface-visibility: hidden;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .flip-card-front {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .flip-card-back {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        color: white;
        transform: rotateY(180deg);
        font-size: 0.95em;
        line-height: 1.6;
        text-align: center;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# Update session state for current page
st.session_state.page = 'Veri Ön İşleme'

st.title("🔧 Veri Ön İşleme - Adım Adım Rehber")
st.markdown("---")

# Sidebar navigation
with st.sidebar:
    st.title("🤖 ML Automation")
    st.markdown("---")
    
    # Status indicator
    if st.session_state.get('uploaded_data') is not None:
        st.success("✅ Veri yüklü")
        df = st.session_state.get('uploaded_data')
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
    
    if st.button("🔧 Veri Ön İşleme", width='stretch', type="primary"):
        pass  # Already on this page
    
    st.markdown("---")
    st.markdown("### ⚙️ Ayarlar")
    
    # LLM suggestions toggle
    llm_enabled = st.toggle(
        "🤖 LLM Önerileri",
        value=True,
        help="LLM ile ön işleme önerileri"
    )
    
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
    Veri Ön İşleme modülü, verilerinizi adım adım işlemenizi sağlar. Eksik değerler, encoding, scaling, outlier ve feature engineering işlemlerini yapabilirsiniz.
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("💡 Sol menüden sayfalar arasında geçiş yapabilirsiniz")

# Check if data is loaded
if st.session_state.get('uploaded_data') is None:
    st.warning("⚠️ Veri yüklenmedi!")
    st.info("💡 Lütfen önce 'Veri Yükleme' sayfasından veri yükleyin.")
    if st.button("📊 Veri Yükleme Sayfasına Git", type="primary"):
        st.switch_page("pages/data_upload.py")
    st.stop()

# Get data from session state
original_df = st.session_state.get('uploaded_data')

if original_df is None or original_df.empty:
    st.error("❌ Veri bulunamadı veya boş!")
    st.stop()

# Check if data has changed (new dataset uploaded)
if 'original_data' in st.session_state:
    # Compare previous data with current data
    previous_data = st.session_state.original_data
    current_data = original_df
    
    # Check if data has changed (shape or content)
    data_changed = (
        previous_data.shape != current_data.shape or
        not previous_data.equals(current_data)
    )
    
    if data_changed:
        # New data uploaded, reset preprocessing states
        st.session_state.preprocessed_data = original_df.copy()
        st.session_state.original_data = original_df.copy()
        st.session_state.preprocessing_history = []
        st.session_state.preprocessing_suggestions = {}
        st.session_state.applied_suggestion_ids = []
        st.session_state.preprocessing_step = 1
        st.session_state.step_completed = set()
        st.info("🔄 Yeni veri seti yüklendi! Veri ön işleme sıfırlandı.")
        st.rerun()

# Initialize session state
if 'preprocessed_data' not in st.session_state:
    st.session_state.preprocessed_data = original_df.copy()
if 'original_data' not in st.session_state:
    st.session_state.original_data = original_df.copy()
if 'preprocessing_history' not in st.session_state:
    st.session_state.preprocessing_history = []
if 'preprocessing_suggestions' not in st.session_state:
    st.session_state.preprocessing_suggestions = {}
if 'applied_suggestion_ids' not in st.session_state:
    st.session_state.applied_suggestion_ids = []
if 'preprocessing_step' not in st.session_state:
    st.session_state.preprocessing_step = 1
if 'step_completed' not in st.session_state:
    st.session_state.step_completed = set()

# Get current data
df = st.session_state.preprocessed_data.copy()

# Get column types
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

# Get data summary for LLM
data_summary = get_data_summary(df)

# Determine analysis level
def determine_analysis_level(df, numeric_cols, categorical_cols, data_summary):
    """Determine analysis level based on dataset characteristics."""
    total_rows = len(df)
    total_cols = len(df.columns)
    num_numeric = len(numeric_cols)
    num_categorical = len(categorical_cols)
    missing_pct = data_summary.get('missing_values', {}).get('missing_percentage', 0)
    
    if total_rows > 10000 or total_cols > 20 or (num_numeric > 10 and num_categorical > 5):
        return 'Gelişmiş'
    elif total_rows > 1000 or total_cols > 10 or missing_pct > 10:
        return 'Orta'
    else:
        return 'Temel'

analysis_level = determine_analysis_level(df, numeric_cols, categorical_cols, data_summary)

# Steps definition
steps = [
    {"name": "Feature Engineering", "icon": "🛠️", "key": "feature_engineering"},
    {"name": "Eksik Değerler", "icon": "🔍", "key": "missing_values"},
    {"name": "Outlier", "icon": "🎯", "key": "outlier"},
    {"name": "Encoding", "icon": "🔤", "key": "encoding"},
    {"name": "Scaling", "icon": "📏", "key": "scaling"},
    {"name": "Özet", "icon": "📊", "key": "summary"}
]

# Progress bar function
def create_progress_bar(steps, current_step):
    """Create HTML progress bar for wizard steps."""
    html_parts = ['<div style="background: #f0f0f0; padding: 20px; border-radius: 10px; margin-bottom: 30px;">']
    html_parts.append('<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">')
    
    for i, step in enumerate(steps, 1):
        step_num = i
        step_name = step['name']
        step_icon = step['icon']
        
        if step_num < current_step:
            # Completed
            status = "✓"
            color = "#4CAF50"
            bg_color = "#E8F5E9"
        elif step_num == current_step:
            # Current
            status = "→"
            color = "#2196F3"
            bg_color = "#E3F2FD"
        else:
            # Pending
            status = "&nbsp;"
            color = "#9E9E9E"
            bg_color = "#F5F5F5"
        
        step_html = f'''<div style="flex: 1; min-width: 120px; text-align: center; padding: 10px; margin: 5px; background: {bg_color}; border-radius: 8px; border: 2px solid {color};">
            <div style="font-size: 1.5em; font-weight: bold; color: {color};">{step_icon} {status}</div>
            <div style="font-size: 0.9em; color: {color}; margin-top: 5px;">Step {step_num}</div>
            <div style="font-size: 0.8em; color: {color}; margin-top: 2px;">{step_name}</div>
        </div>'''
        html_parts.append(step_html)
    
    html_parts.append('</div></div>')
    return ''.join(html_parts)

# Display progress bar
current_step = st.session_state.preprocessing_step

# Use columns for progress bar instead of HTML
st.markdown("### 📍 İlerleme")
progress_cols = st.columns(6)
for i, step in enumerate(steps):
    step_num = i + 1
    step_name = step['name']
    step_icon = step['icon']
    
    with progress_cols[i]:
        if step_num < current_step:
            # Completed
            status = "✓"
            color = "#9C27B0"
            bg_color = "#F3E5F5"
        elif step_num == current_step:
            # Current
            status = "→"
            color = "#7B1FA2"
            bg_color = "#E1BEE7"
        else:
            # Pending
            status = "○"
            color = "#9E9E9E"
            bg_color = "#F5F5F5"
        
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 15px;
            background: {bg_color};
            border-radius: 8px;
            border: 2px solid {color};
            margin-bottom: 10px;
        ">
            <div style="font-size: 1.5em; font-weight: bold; color: {color};">
                {step_icon} {status}
            </div>
            <div style="font-size: 0.9em; color: {color}; margin-top: 5px;">
                Step {step_num}
            </div>
            <div style="font-size: 0.8em; color: {color}; margin-top: 2px;">
                {step_name}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Helper function to check if step has operations
def check_step_has_operation(step_num):
    """Check if current step has any applied operations."""
    step_key = steps[step_num - 1]['key']
    for history_item in st.session_state.preprocessing_history:
        if history_item.get('step') == step_num or history_item.get('step_key') == step_key:
            return True
    return False

# Step content rendering functions
def render_feature_engineering_step(df):
    """Render feature engineering preprocessing step."""
    st.subheader(f"🛠️ {steps[0]['name']}")
    
    # CRITICAL: Use current preprocessed_data directly
    current_df = st.session_state.preprocessed_data.copy()
    
    logger.debug(f"🔍 [FEATURE ENGINEERING STEP] render_feature_engineering_step called")
    logger.debug(f"🔍 [FEATURE ENGINEERING STEP] current_df shape: {current_df.shape}")
    logger.debug(f"🔍 [FEATURE ENGINEERING STEP] current_df columns: {list(current_df.columns)}")
    
    # Feature engineering analysis section
    st.markdown("### 📊 Feature Engineering Analizi")
    
    # Check if any operations were applied
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
    if step_history:
        st.info("ℹ️ İşlemler uygulandıktan sonra analiz güncellenmiştir.")
    
    # Analyze feature engineering aspects
    try:
        duplicate_info = analyze_duplicate_rows(current_df)
        irrelevant_info = analyze_irrelevant_columns(current_df)
        logger.debug(f"🔍 [FEATURE ENGINEERING STEP] Analysis complete: {duplicate_info['total_duplicates']} duplicates, {len(irrelevant_info['all_irrelevant'])} irrelevant columns")
    except Exception as e:
        logger.error(f"❌ [FEATURE ENGINEERING STEP] Error in analysis: {e}", exc_info=True)
        st.error(f"❌ Feature engineering analizi sırasında hata oluştu: {str(e)}")
        return
    
    # Summary metrics - in purple cards
    total_rows = len(current_df)
    total_columns = len(current_df.columns)
    duplicate_count = duplicate_info['total_duplicates']
    duplicate_percentage = duplicate_info['duplicate_percentage']
    irrelevant_count = len(irrelevant_info['all_irrelevant'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Toplam Satır</div>
            <div style='font-size: 2em; font-weight: bold;'>{total_rows:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Tekrarlayan Satır</div>
            <div style='font-size: 2em; font-weight: bold;'>{duplicate_count:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Tekrarlayan Yüzdesi</div>
            <div style='font-size: 2em; font-weight: bold;'>{duplicate_percentage:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Toplam Sütun</div>
            <div style='font-size: 2em; font-weight: bold;'>{total_columns}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Duplicate rows table
    if duplicate_count > 0:
        st.markdown("#### 📋 Tekrarlayan Satırlar")
        st.info(f"ℹ️ {duplicate_count:,} tekrarlayan satır bulundu ({duplicate_percentage:.2f}%)")
    else:
        st.markdown("#### 📋 Tekrarlayan Satırlar")
        st.success("✅ Veri setinde tekrarlayan satır bulunmuyor!")
    
    st.markdown("---")
    
    # Irrelevant columns table
    st.markdown("#### 📋 Gereksiz Sütunlar")
    if irrelevant_count > 0:
        irrelevant_data = []
        for item in irrelevant_info['constant_columns']:
            irrelevant_data.append({
                'Sütun': item['column'],
                'Sebep': item['reason'],
                'Detay': f"Unique: {item['unique_count']}"
            })
        for item in irrelevant_info['low_variance_columns']:
            irrelevant_data.append({
                'Sütun': item['column'],
                'Sebep': item['reason'],
                'Detay': f"Varyans: {item['variance']:.6f}"
            })
        for item in irrelevant_info['high_unique_ratio_columns']:
            irrelevant_data.append({
                'Sütun': item['column'],
                'Sebep': item['reason'],
                'Detay': f"Unique: {item['unique_count']}/{item['total_rows']} ({item['unique_ratio']:.2%})"
            })
        
        if irrelevant_data:
            irrelevant_df = pd.DataFrame(irrelevant_data)
            st.dataframe(irrelevant_df, width='stretch', hide_index=True)
    else:
        st.success("✅ Veri setinde gereksiz sütun bulunmuyor!")
    
    st.markdown("---")
    
    # DataFrame Preview
    st.markdown("#### 📊 Veri Önizlemesi")
    st.caption("Feature engineering işlemlerinden önce veri setinin güncel durumu")
    
    preview_rows = min(10, len(current_df))
    st.dataframe(
        current_df.head(preview_rows),
        width='stretch',
        hide_index=False
    )
    st.caption(f"Gösterilen: İlk {preview_rows} satır (Toplam: {len(current_df):,} satır, {len(current_df.columns)} sütun)")
    
    st.markdown("---")
    
    # LLM suggestions section removed - will be added back later if needed
    
    # Manual operations
    st.markdown("### 🔧 Manuel İşlemler")
    
    step_key = 'feature_engineering'
    
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    '>
    """, unsafe_allow_html=True)
    
    # Tab 1: Duplicate Rows Removal
    tab1, tab2, tab3 = st.tabs(["🔄 Tekrarlayan Satırlar", "🗑️ Sütun Silme", "➕ Yeni Özellik"])
    
    with tab1:
        st.markdown("#### 🔄 Tekrarlayan Satırları Kaldır")
        duplicate_count_tab = duplicate_info['total_duplicates']
        
        if duplicate_count_tab > 0:
            st.info(f"ℹ️ {duplicate_count_tab:,} tekrarlayan satır bulundu")
            keep_option = st.radio(
                "Hangi tekrarları tut?",
                options=['first', 'last', 'none'],
                format_func=lambda x: {'first': 'İlkini tut', 'last': 'Sonunu tut', 'none': 'Hepsini kaldır'}[x],
                key="duplicate_keep_option"
            )
            
            if st.button("✅ Uygula", key="apply_duplicate_removal", type="primary", width='stretch'):
                try:
                    df_processed = current_df.copy()
                    df_processed = remove_duplicate_rows(df_processed, keep=keep_option)
                    
                    st.session_state.preprocessed_data = df_processed
                    
                    st.session_state.preprocessing_history.append({
                        'step': current_step,
                        'step_key': step_key,
                        'type': step_key,
                        'method': 'remove_duplicates',
                        'columns': [],
                        'keep': keep_option,
                        'timestamp': datetime.now().isoformat(),
                        'before_data': current_df.copy()
                    })
                    
                    st.success(f"✅ {duplicate_count_tab:,} tekrarlayan satır kaldırıldı!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Hata oluştu: {str(e)}")
                    logger.error(f"Error removing duplicates: {e}", exc_info=True)
        else:
            st.success("✅ Veri setinde tekrarlayan satır bulunmuyor!")
    
    with tab2:
        st.markdown("#### 🗑️ Gereksiz Sütunları Sil")
        
        # Get all columns
        all_columns = current_df.columns.tolist()
        
        # Get already dropped columns from history
        dropped_columns = set()
        for hist in st.session_state.preprocessing_history:
            if hist.get('type') == step_key and hist.get('method') == 'drop_column':
                hist_columns = hist.get('columns', [])
                if isinstance(hist_columns, list):
                    dropped_columns.update(hist_columns)
        
        # Filter out already dropped columns
        available_columns = [col for col in all_columns if col not in dropped_columns]
        
        if available_columns:
            selected_columns_to_drop = st.multiselect(
                "Silinecek sütunları seçin",
                options=available_columns,
                help=f"Silinebilir {len(available_columns)} sütun gösteriliyor",
                label_visibility="collapsed"
            )
            
            if selected_columns_to_drop:
                st.info(f"✅ {len(selected_columns_to_drop)} sütun seçildi")
                
                if st.button("✅ Uygula", key="apply_column_drop", type="primary", width='stretch'):
                    try:
                        df_processed = current_df.copy()
                        df_processed = drop_columns(df_processed, selected_columns_to_drop)
                        
                        st.session_state.preprocessed_data = df_processed
                        
                        st.session_state.preprocessing_history.append({
                            'step': current_step,
                            'step_key': step_key,
                            'type': step_key,
                            'method': 'drop_column',
                            'columns': selected_columns_to_drop,
                            'timestamp': datetime.now().isoformat(),
                            'before_data': current_df.copy()
                        })
                        
                        st.success(f"✅ {len(selected_columns_to_drop)} sütun başarıyla silindi: {', '.join(selected_columns_to_drop)}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Hata oluştu: {str(e)}")
                        logger.error(f"Error dropping columns: {e}", exc_info=True)
            else:
                st.info("ℹ️ Lütfen silmek istediğiniz sütunları seçin")
        else:
            st.success("✅ Tüm sütunlar zaten silinmiş veya silinecek sütun bulunmuyor!")
    
    with tab3:
        st.markdown("#### ➕ Yeni Özellik Oluştur")
        
        # Sub-tabs for different feature creation types
        subtab1, subtab2, subtab3 = st.tabs(["🔢 Sayısal İşlemler", "📅 Tarih/Saat", "🔗 Kategorik Birleştirme"])
        
        with subtab1:
            st.markdown("##### 🔢 Sayısal Sütunlardan Yeni Özellik")
            numeric_cols_fe = current_df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_cols_fe) >= 2:
                selected_numeric_cols = st.multiselect(
                    "İşlem yapılacak sayısal sütunları seçin (en az 2)",
                    options=numeric_cols_fe,
                    help="En az 2 sayısal sütun seçmelisiniz"
                )
                
                if len(selected_numeric_cols) >= 2:
                    operation = st.selectbox(
                        "İşlem tipi",
                        options=['add', 'subtract', 'multiply', 'divide'],
                        format_func=lambda x: {'add': 'Toplama (+)', 'subtract': 'Çıkarma (-)', 'multiply': 'Çarpma (×)', 'divide': 'Bölme (÷)'}[x],
                        key="numeric_operation"
                    )
                    
                    new_column_name = st.text_input(
                        "Yeni sütun adı",
                        value=f"{'_'.join(selected_numeric_cols[:2])}_{operation}",
                        key="new_numeric_column_name"
                    )
                    
                    if new_column_name and new_column_name not in current_df.columns:
                        if st.button("✅ Oluştur", key="create_numeric_feature", type="primary", width='stretch'):
                            try:
                                df_processed = current_df.copy()
                                df_processed = create_numeric_feature(df_processed, operation, selected_numeric_cols, new_column_name)
                                
                                st.session_state.preprocessed_data = df_processed
                                
                                st.session_state.preprocessing_history.append({
                                    'step': current_step,
                                    'step_key': step_key,
                                    'type': step_key,
                                    'method': 'create_numeric_feature',
                                    'columns': selected_numeric_cols,
                                    'operation': operation,
                                    'new_column_name': new_column_name,
                                    'timestamp': datetime.now().isoformat(),
                                    'before_data': current_df.copy()
                                })
                                
                                st.success(f"✅ Yeni özellik '{new_column_name}' başarıyla oluşturuldu!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Hata oluştu: {str(e)}")
                                logger.error(f"Error creating numeric feature: {e}", exc_info=True)
                    elif new_column_name in current_df.columns:
                        st.warning("⚠️ Bu sütun adı zaten mevcut!")
                else:
                    st.info("ℹ️ En az 2 sayısal sütun seçmelisiniz")
            else:
                st.info("ℹ️ Yeni sayısal özellik oluşturmak için en az 2 sayısal sütun gereklidir")
        
        with subtab2:
            st.markdown("##### 📅 Tarih/Saat Sütunundan Özellik Çıkar")
            datetime_cols = current_df.select_dtypes(include=['datetime']).columns.tolist()
            
            if datetime_cols:
                selected_datetime_col = st.selectbox(
                    "Tarih/saat sütunu seçin",
                    options=datetime_cols,
                    key="datetime_column_select"
                )
                
                feature_type = st.selectbox(
                    "Çıkarılacak özellik",
                    options=['year', 'month', 'day', 'weekday', 'hour', 'minute', 'second'],
                    format_func=lambda x: {
                        'year': 'Yıl', 'month': 'Ay', 'day': 'Gün', 
                        'weekday': 'Hafta Günü', 'hour': 'Saat', 
                        'minute': 'Dakika', 'second': 'Saniye'
                    }[x],
                    key="datetime_feature_type"
                )
                
                new_column_name = st.text_input(
                    "Yeni sütun adı",
                    value=f"{selected_datetime_col}_{feature_type}",
                    key="new_datetime_column_name"
                )
                
                if new_column_name and new_column_name not in current_df.columns:
                    if st.button("✅ Oluştur", key="create_datetime_feature", type="primary", width='stretch'):
                        try:
                            df_processed = current_df.copy()
                            df_processed = create_datetime_feature(df_processed, selected_datetime_col, feature_type, new_column_name)
                            
                            st.session_state.preprocessed_data = df_processed
                            
                            st.session_state.preprocessing_history.append({
                                'step': current_step,
                                'step_key': step_key,
                                'type': step_key,
                                'method': 'create_datetime_feature',
                                'columns': [selected_datetime_col],
                                'feature_type': feature_type,
                                'new_column_name': new_column_name,
                                'timestamp': datetime.now().isoformat(),
                                'before_data': current_df.copy()
                            })
                            
                            st.success(f"✅ Yeni özellik '{new_column_name}' başarıyla oluşturuldu!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Hata oluştu: {str(e)}")
                            logger.error(f"Error creating datetime feature: {e}", exc_info=True)
                elif new_column_name in current_df.columns:
                    st.warning("⚠️ Bu sütun adı zaten mevcut!")
            else:
                st.info("ℹ️ Tarih/saat sütunu bulunmuyor")
        
        with subtab3:
            st.markdown("##### 🔗 Kategorik Sütunları Birleştir")
            categorical_cols_fe = current_df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            if len(categorical_cols_fe) >= 2:
                selected_categorical_cols = st.multiselect(
                    "Birleştirilecek kategorik sütunları seçin (en az 2)",
                    options=categorical_cols_fe,
                    help="En az 2 kategorik sütun seçmelisiniz"
                )
                
                if len(selected_categorical_cols) >= 2:
                    separator = st.text_input(
                        "Ayırıcı karakter",
                        value="_",
                        key="categorical_separator"
                    )
                    
                    new_column_name = st.text_input(
                        "Yeni sütun adı",
                        value=f"{'_'.join(selected_categorical_cols[:2])}_combined",
                        key="new_categorical_column_name"
                    )
                    
                    if new_column_name and new_column_name not in current_df.columns:
                        if st.button("✅ Oluştur", key="create_categorical_combination", type="primary", width='stretch'):
                            try:
                                df_processed = current_df.copy()
                                df_processed = create_categorical_combination(df_processed, selected_categorical_cols, new_column_name, separator)
                                
                                st.session_state.preprocessed_data = df_processed
                                
                                st.session_state.preprocessing_history.append({
                                    'step': current_step,
                                    'step_key': step_key,
                                    'type': step_key,
                                    'method': 'create_categorical_combination',
                                    'columns': selected_categorical_cols,
                                    'separator': separator,
                                    'new_column_name': new_column_name,
                                    'timestamp': datetime.now().isoformat(),
                                    'before_data': current_df.copy()
                                })
                                
                                st.success(f"✅ Yeni özellik '{new_column_name}' başarıyla oluşturuldu!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Hata oluştu: {str(e)}")
                                logger.error(f"Error creating categorical combination: {e}", exc_info=True)
                    elif new_column_name in current_df.columns:
                        st.warning("⚠️ Bu sütun adı zaten mevcut!")
                else:
                    st.info("ℹ️ En az 2 kategorik sütun seçmelisiniz")
            else:
                st.info("ℹ️ Yeni kategorik birleştirme oluşturmak için en az 2 kategorik sütun gereklidir")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Show applied operations for this step with undo functionality - ALWAYS SHOW
    st.markdown("### 📋 Uygulanan İşlemler")
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
    if step_history:
        for idx, hist in enumerate(step_history):
            method_op = hist.get('method', '')
            columns_op = hist.get('columns', [])
            new_column_name_op = hist.get('new_column_name', '')
            
            col1, col2 = st.columns([4, 1])
            with col1:
                if method_op == 'remove_duplicates':
                    keep_op = hist.get('keep', 'first')
                    keep_text = {'first': 'ilkini', 'last': 'sonunu', 'none': 'hepsini'}.get(keep_op, keep_op)
                    display_text = f"Tekrarlayan satırlar kaldırıldı ({keep_text} tutuldu)"
                elif method_op == 'drop_column':
                    display_text = f"{', '.join(columns_op)} sütunları silindi"
                elif method_op in ['create_numeric_feature', 'create_datetime_feature', 'create_categorical_combination']:
                    display_text = f"Yeni özellik '{new_column_name_op}' oluşturuldu ({method_op})"
                else:
                    display_text = f"{method_op} işlemi uygulandı"
                
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 5px 0;
                    color: white;
                '>
                    <span style='font-size: 1.2em; margin-right: 10px;'>✅</span>
                    {display_text}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("↶ Geri Al", key=f"undo_feature_engineering_{idx}", width='stretch'):
                    # Remove from history
                    operation_to_remove = step_history[idx]
                    removed_method = operation_to_remove.get('method', '')
                    removed_columns = operation_to_remove.get('columns', [])
                    
                    st.session_state.preprocessing_history.remove(operation_to_remove)
                    
                    # Rebuild dataframe - suppress INFO logs during rebuild
                    original_log_level = logger.level
                    logger.setLevel(logging.WARNING)
                    try:
                        df_rebuilt = st.session_state.original_data.copy()
                        
                        # Apply all operations in correct order: feature_engineering -> missing_values -> outlier -> encoding
                        for op in st.session_state.preprocessing_history:
                            op_type = op.get('type', '')
                            
                            if op_type == 'feature_engineering':
                                op_method = op.get('method', '')
                                if op_method == 'remove_duplicates':
                                    df_rebuilt = remove_duplicate_rows(df_rebuilt, keep=op.get('keep', 'first'))
                                elif op_method == 'drop_column':
                                    df_rebuilt = drop_columns(df_rebuilt, op.get('columns', []))
                                elif op_method == 'create_numeric_feature':
                                    df_rebuilt = create_numeric_feature(
                                        df_rebuilt,
                                        op.get('operation', 'add'),
                                        op.get('columns', []),
                                        op.get('new_column_name', '')
                                    )
                                elif op_method == 'create_datetime_feature':
                                    df_rebuilt = create_datetime_feature(
                                        df_rebuilt,
                                        op.get('columns', [])[0] if op.get('columns') else '',
                                        op.get('feature_type', 'year'),
                                        op.get('new_column_name', '')
                                    )
                                elif op_method == 'create_categorical_combination':
                                    df_rebuilt = create_categorical_combination(
                                        df_rebuilt,
                                        op.get('columns', []),
                                        op.get('new_column_name', ''),
                                        op.get('separator', '_')
                                    )
                            elif op_type == 'missing_values':
                                op_method_dict = op.get('method_dict')
                                if op_method_dict:
                                    if op_method_dict.get('numeric') and op_method_dict.get('numeric_cols'):
                                        df_rebuilt = apply_missing_values_method(
                                            df_rebuilt, 
                                            op_method_dict['numeric_cols'], 
                                            op_method_dict['numeric']
                                        )
                                    if op_method_dict.get('categorical') and op_method_dict.get('categorical_cols'):
                                        df_rebuilt = apply_missing_values_method(
                                            df_rebuilt, 
                                            op_method_dict['categorical_cols'], 
                                            op_method_dict['categorical']
                                        )
                                else:
                                    df_rebuilt = apply_missing_values_method(
                                        df_rebuilt, 
                                        op.get('columns', []), 
                                        op.get('method', '')
                                    )
                            elif op_type == 'outlier':
                                outlier_method = op.get('method', '')
                                method_parts = outlier_method.split('_')
                                if len(method_parts) >= 2:
                                    detection_method = '_'.join(method_parts[:-1])
                                    action = method_parts[-1]
                                    df_rebuilt = apply_outlier_method_wrapper(
                                        df_rebuilt,
                                        op.get('columns', []),
                                        detection_method,
                                        action
                                    )
                            elif op_type == 'encoding':
                                op_columns = op.get('columns', [])
                                op_method = op.get('method', '')
                                
                                if op_method in ['binary_encoding', 'one_hot_encoding']:
                                    existing_columns = [col for col in op_columns if col in df_rebuilt.columns]
                                    if existing_columns:
                                        df_rebuilt = apply_encoding_method(
                                            df_rebuilt,
                                            existing_columns,
                                            op_method
                                        )
                                else:
                                    df_rebuilt = apply_encoding_method(
                                        df_rebuilt,
                                        op_columns,
                                        op_method
                                    )
                    finally:
                        logger.setLevel(original_log_level)
                    
                    st.session_state.preprocessed_data = df_rebuilt
                    
                    # Remove from applied_suggestion_ids if it was from LLM
                    if operation_to_remove.get('from_llm'):
                        remove_method = operation_to_remove.get('method', '')
                        remove_columns = operation_to_remove.get('columns', [])
                        step_key_undo = 'feature_engineering'
                        suggestion_id = f"{step_key_undo}_{remove_method}_{'_'.join(remove_columns) if remove_columns else 'all'}"
                        if suggestion_id in st.session_state.applied_suggestion_ids:
                            st.session_state.applied_suggestion_ids.remove(suggestion_id)
                    
                    st.success("✅ İşlem geri alındı!")
                    st.rerun()
    else:
        st.info("ℹ️ Henüz bu adımda işlem uygulanmadı.")
    
    # Add spacing before navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Action buttons - right aligned at bottom
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col2:
        if current_step > 1:
            if st.button("← Geri", key="prev_step_feature_engineering", width='stretch'):
                st.session_state.preprocessing_step -= 1
                st.rerun()
    with col3:
        # Atla butonu - son adımda (Summary) gösterilmez
        if current_step < len(steps):
            if st.button("Atla", key="skip_step_feature_engineering", width='stretch'):
                st.session_state.preprocessing_step += 1
                st.rerun()
    with col4:
        has_operation = check_step_has_operation(current_step)
        if st.button("İleri →", key="next_step_feature_engineering", disabled=not has_operation, width='stretch'):
            st.session_state.preprocessing_step += 1
            st.rerun()


def render_missing_values_step(df):
    """Render missing values preprocessing step."""
    st.subheader(f"🔍 {steps[1]['name']}")
    
    # Missing values analysis section (before LLM suggestions)
    st.markdown("### 📊 Eksik Değer Analizi")
    
    # Check if any operations were applied
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
    if step_history:
        st.info("ℹ️ İşlemler uygulandıktan sonra eksik değer analizi güncellenmiştir.")
    
    # Analyze missing values from current dataframe
    current_df = st.session_state.preprocessed_data.copy()
    try:
        missing_info = analyze_missing_values(current_df)
    except Exception as e:
        logger.error(f"❌ [MISSING VALUES STEP] Error in analyze_missing_values: {e}", exc_info=True)
        st.error(f"❌ Eksik değer analizi sırasında hata oluştu: {str(e)}")
        return
    
    # Summary metrics - in purple cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Toplam Eksik</div>
            <div style='font-size: 2em; font-weight: bold;'>{missing_info['total_missing']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Eksik Yüzdesi</div>
            <div style='font-size: 2em; font-weight: bold;'>{missing_info['missing_percentage']:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Etkilenen Sütun</div>
            <div style='font-size: 2em; font-weight: bold;'>{len(missing_info['columns_with_missing'])}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        total_cells = len(current_df) * len(current_df.columns)
        complete_cells = total_cells - missing_info['total_missing']
        complete_pct = (complete_cells/total_cells*100) if total_cells > 0 else 100
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Tam Veri</div>
            <div style='font-size: 2em; font-weight: bold;'>{complete_pct:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Visual heatmap - Always show, even if no missing values
    st.markdown("#### 🔥 Eksik Değer Haritası")
    missing_viz = create_missing_heatmap(current_df, library='plotly')
    if missing_viz:
        st.plotly_chart(missing_viz, width='stretch', key="missing_heatmap_preprocessing")
    if not missing_info['columns_with_missing']:
        st.success("✅ Veri setinde eksik değer bulunmuyor!")
    
    # Detailed table - Show all columns, even if no missing values
    st.markdown("#### 📋 Sütun Bazlı Detay")
    
    # Get data types for columns
    def get_dtype_name(col):
        dtype = current_df[col].dtype
        if pd.api.types.is_integer_dtype(dtype):
            return 'Integer'
        elif pd.api.types.is_float_dtype(dtype):
            return 'Float'
        elif pd.api.types.is_object_dtype(dtype):
            return 'Object'
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return 'DateTime'
        elif pd.api.types.is_bool_dtype(dtype):
            return 'Boolean'
        elif pd.api.types.is_categorical_dtype(dtype):
            return 'Category'
        else:
            return str(dtype)
    
    # Create table with ALL columns, not just those with missing values
    all_columns = current_df.columns.tolist()
    missing_by_column = missing_info.get('missing_by_column', {})
    missing_percentage_by_column = missing_info.get('missing_percentage_by_column', {})
    
    missing_df = pd.DataFrame({
        'Sütun': all_columns,
        'Veri Türü': [get_dtype_name(col) for col in all_columns],
        'Eksik Sayısı': [missing_by_column.get(col, 0) for col in all_columns],
        'Eksik Yüzdesi': [missing_percentage_by_column.get(col, 0) for col in all_columns]
    })
    
    # Sort by missing percentage (descending), then by column name
    missing_df = missing_df.sort_values(['Eksik Yüzdesi', 'Sütun'], ascending=[False, True])
    missing_df['Eksik Yüzdesi'] = missing_df['Eksik Yüzdesi'].apply(lambda x: f"{x:.2f}%")
    
    # Reorder columns for better display
    missing_df = missing_df[['Sütun', 'Veri Türü', 'Eksik Sayısı', 'Eksik Yüzdesi']]
    
    # Style the dataframe
    st.dataframe(
        missing_df,
        width='stretch',
        hide_index=True
    )
    
    # Show message if no missing values
    if not missing_info['columns_with_missing']:
        st.success("✅ Veri setinde eksik değer bulunmuyor!")
    
    st.markdown("---")
    
    # LLM suggestions
    if llm_enabled:
        step_key = 'missing_values'
        suggestions_key = f'step_{current_step}_{step_key}'
        index_key = f'preprocessing_suggestion_index_{step_key}'
        
        # Initialize suggestion index for this step
        if index_key not in st.session_state:
            st.session_state[index_key] = 0
        
        with st.expander("🤖 LLM Önerileri", expanded=True):
            # Button to get suggestions
            if suggestions_key not in st.session_state.preprocessing_suggestions:
                if st.button("💡 LLM Önerilerini Al", key=f"get_suggestions_{step_key}"):
                    # Yeni öneriler alındığında uygulanmış öneri ID'lerini temizle (bu step için)
                    # Not: Tüm applied_suggestion_ids'i temizlemiyoruz, sadece bu step için olanları
                    
                    with st.spinner("🤖 LLM önerileri oluşturuluyor..."):
                        # Get missing columns info for prompt
                        missing_info_step = analyze_missing_values(df)
                        columns_with_missing_step = missing_info_step.get('columns_with_missing', [])
                        
                        # Update data_summary with missing columns info
                        data_summary_with_missing = data_summary.copy()
                        if 'missing_values' not in data_summary_with_missing:
                            data_summary_with_missing['missing_values'] = {}
                        data_summary_with_missing['missing_values']['columns_with_missing'] = columns_with_missing_step
                        data_summary_with_missing['missing_values']['missing_by_column'] = missing_info_step.get('missing_by_column', {})
                        data_summary_with_missing['missing_values']['missing_percentage_by_column'] = missing_info_step.get('missing_percentage_by_column', {})
                        
                        if step_key == 'missing_values':
                            suggestions_result = suggest_missing_values_steps(
                                data_summary_with_missing,
                                numeric_cols,
                                categorical_cols,
                                analysis_level
                            )
                        else:
                            suggestions_result = {"suggestions": []}
                        
                        if suggestions_result.get('error'):
                            st.error(f"❌ LLM önerisi alınamadı: {suggestions_result.get('error')}")
                        else:
                            suggestions = suggestions_result.get('suggestions', [])
                            # Filter suggestions for this step type
                            filtered_suggestions = [s for s in suggestions if s.get('preprocessing_type') == step_key]
                            
                            # Otomatik öncelik hesaplaması (LLM'in verdiği önceliği override et)
                            if step_key == 'missing_values':
                                missing_percentage_by_column = missing_info_step.get('missing_percentage_by_column', {})
                                for suggestion in filtered_suggestions:
                                    columns = suggestion.get('columns', [])
                                    if columns:
                                        # Her sütun için eksik değer yüzdesini kontrol et
                                        max_missing_pct = 0
                                        for col in columns:
                                            if col in missing_percentage_by_column:
                                                max_missing_pct = max(max_missing_pct, missing_percentage_by_column[col])
                                        
                                        # Önceliği otomatik belirle (LLM'in verdiği önceliği override et)
                                        if max_missing_pct > 50:
                                            suggestion['priority'] = 'yüksek'
                                        elif max_missing_pct >= 10:
                                            suggestion['priority'] = 'orta'
                                        else:
                                            suggestion['priority'] = 'düşük'
                            
                            st.session_state.preprocessing_suggestions[suggestions_key] = filtered_suggestions
                            st.session_state[index_key] = 0  # Reset index
                            if filtered_suggestions:
                                st.success(f"✅ {len(filtered_suggestions)} öneri alındı")
                            st.rerun()
            else:
                # Yeniden öneri al butonu (öneriler varsa)
                if st.button("🔄 Yeni Öneriler Al", key=f"refresh_suggestions_{step_key}"):
                    # Önerileri temizle ve yeniden al
                    del st.session_state.preprocessing_suggestions[suggestions_key]
                    st.session_state[index_key] = 0
                    st.rerun()
            
            # Display suggestions in carousel format
            if suggestions_key in st.session_state.preprocessing_suggestions:
                suggestions = st.session_state.preprocessing_suggestions[suggestions_key]
                if suggestions:
                    current_index = st.session_state[index_key]
                    
                    st.markdown(f"<div style='text-align: center; margin: 10px 0;'><strong>{len(suggestions)} öneri sunuldu</strong> | <em>Öneri {current_index + 1}/{len(suggestions)}</em></div>", unsafe_allow_html=True)
                    
                    # Navigation buttons and current suggestion
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        if st.button("◀️ Önceki", key=f"prev_suggestion_{step_key}", disabled=(current_index == 0), width='stretch'):
                            st.session_state[index_key] = max(0, current_index - 1)
                            st.rerun()
                    
                    with col2:
                        # Current suggestion - kart tasarımı
                        suggestion = suggestions[current_index]
                        method = suggestion.get('method', 'Bilinmeyen')
                        columns = suggestion.get('columns', [])
                        reason = suggestion.get('reason', '')
                        priority = suggestion.get('priority', 'orta')
                        analysis_level_sugg = suggestion.get('analysis_level', 'Temel')
                        
                        # HTML tag'lerini temizle
                        import html as html_module
                        import re
                        if reason:
                            try:
                                reason = html_module.unescape(reason)
                            except:
                                pass
                            reason = re.sub(r'<[^>]+>', '', reason, flags=re.DOTALL | re.IGNORECASE)
                            reason = ' '.join(reason.split()).strip()
                        
                        # Priority ve level renkleri
                        priority_colors = {'yüksek': '#f44336', 'orta': '#ff9800', 'düşük': '#4caf50'}
                        level_colors = {'Temel': '#4CAF50', 'Orta': '#FF9800', 'Gelişmiş': '#F44336'}
                        priority_color = priority_colors.get(priority, '#ff9800')
                        level_color = level_colors.get(analysis_level_sugg, '#4CAF50')
                        
                        # Güvenli HTML
                        method_safe = html_module.escape(str(method))
                        reason_safe = html_module.escape(reason) if reason else 'Açıklama bulunamadı.'
                        priority_safe = html_module.escape(priority)
                        level_safe = html_module.escape(analysis_level_sugg)
                        columns_display = ', '.join(columns) if columns else 'Tüm sütunlar'
                        columns_safe = html_module.escape(columns_display)
                        
                        # Kart tasarımı
                        if columns:
                            card_html = f"""
                        <div style='
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 25px;
                            border-radius: 15px;
                            margin: 10px 0;
                            color: white;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            min-height: 180px;
                            border-left: 5px solid #f0f0f0;
                        '>
                            <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;'>
                                <h3 style='color: white; margin: 0; margin-right: 10px; font-size: 1.3em;'>
                                    🔧 {method_safe}
                                </h3>
                                <div style='display: flex; gap: 10px;'>
                                    <span style='
                                        background: {priority_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                    '>
                                        Öncelik: {priority_safe}
                                    </span>
                                    <span style='
                                        background: {level_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                        text-transform: uppercase;
                                    '>
                                        {level_safe}
                                    </span>
                                </div>
                            </div>
                            <div style='
                                background: rgba(255, 255, 255, 0.15);
                                padding: 10px 15px;
                                border-radius: 8px;
                                margin-bottom: 15px;
                                display: inline-block;
                            '>
                                <span style='color: #f0f0f0; font-size: 0.95em;'>
                                    <strong>📍 Sütunlar:</strong> {columns_safe}
                                </span>
                            </div>
                            <p style='
                                color: white; 
                                margin: 15px 0 0 0; 
                                line-height: 1.7; 
                                font-size: 1em;
                                padding: 10px;
                                background: rgba(255, 255, 255, 0.1);
                                border-radius: 8px;
                            '>
                                {reason_safe}
                            </p>
                        </div>
                        """
                        else:
                            card_html = f"""
                        <div style='
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 25px;
                            border-radius: 15px;
                            margin: 10px 0;
                            color: white;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            min-height: 150px;
                            border-left: 5px solid #f0f0f0;
                        '>
                            <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;'>
                                <h3 style='color: white; margin: 0; font-size: 1.4em; font-weight: bold;'>
                                    🔧 {method_safe}
                                </h3>
                                <div style='display: flex; gap: 10px;'>
                                    <span style='
                                        background: {priority_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                    '>
                                        Öncelik: {priority_safe}
                                    </span>
                                    <span style='
                                        background: {level_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                        text-transform: uppercase;
                                    '>
                                        {level_safe}
                                    </span>
                                </div>
                            </div>
                            <p style='
                                color: white; 
                                margin: 0; 
                                line-height: 1.8; 
                                font-size: 1.05em;
                                padding: 15px;
                                background: rgba(255, 255, 255, 0.15);
                                border-radius: 8px;
                                font-weight: 500;
                            '>
                                {reason_safe}
                            </p>
                        </div>
                        """
                        
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Uygula butonu - Check if method+column combination already applied
                        method = suggestion.get('method', '')
                        columns = suggestion.get('columns', [])
                        
                        # Check if this method+column combination is already applied
                        is_applied = False
                        is_manual_operation = False
                        applied_reason = ""
                        button_text = "✅ Zaten Uygulandı"
                        
                        if step_key == 'missing_values' and columns:
                            # Get all processed columns from step history (step 1 = missing values)
                            step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
                            processed_columns = set()
                            for hist in step_history:
                                hist_columns = hist.get('columns', [])
                                if isinstance(hist_columns, list):
                                    processed_columns.update(hist_columns)
                            
                            # Check if any of the suggested columns are already processed (regardless of method)
                            already_processed_cols = [col for col in columns if col in processed_columns]
                            
                            if already_processed_cols:
                                # Check if it was applied via LLM suggestion or manually
                                # If the method in history matches the suggestion method, it's likely from LLM
                                # Otherwise, it's manual
                                is_llm_applied = False
                                for col in already_processed_cols:
                                    for history_item in step_history:
                                        if (history_item.get('type') == step_key and
                                            history_item.get('method') == method and
                                            col in history_item.get('columns', [])):
                                            is_llm_applied = True
                                            break
                                    if is_llm_applied:
                                        break
                                
                                is_applied = True
                                if not is_llm_applied:
                                    # Manual operation
                                    is_manual_operation = True
                                    button_text = f"ℹ️ Bu sütun üzerinde Manuel olarak işlem yapıldı: {', '.join(already_processed_cols)}"
                                else:
                                    # LLM suggestion was applied
                                    button_text = "✅ Zaten Uygulandı"
                            else:
                                # Also check if this specific method+column combination is already applied
                                for col in columns:
                                    # Check in preprocessing_history
                                    for history_item in st.session_state.preprocessing_history:
                                        if (history_item.get('step') == current_step and 
                                            history_item.get('type') == step_key and
                                            history_item.get('method') == method and
                                            col in history_item.get('columns', [])):
                                            is_applied = True
                                            button_text = "✅ Zaten Uygulandı"
                                            break
                                    if is_applied:
                                        break
                        
                        # Also check by suggestion_id for backward compatibility
                        if not is_applied:
                            suggestion_id = f"{step_key}_{method}_{'_'.join(columns) if columns else 'all'}"
                            is_applied = suggestion_id in st.session_state.applied_suggestion_ids
                            if is_applied:
                                button_text = "✅ Zaten Uygulandı"
                        
                        if is_applied:
                            st.button(button_text, key=f"apply_suggestion_{step_key}_{current_index}", width='stretch', disabled=True)
                        else:
                            if st.button("✅ Uygula", key=f"apply_suggestion_{step_key}_{current_index}", width='stretch', type="primary"):
                                # Validate method for missing_values step
                                if step_key == 'missing_values':
                                    valid_methods = ['mean', 'median', 'mode', 'forward_fill', 'backward_fill', 'interpolation', 'knn', 'drop']
                                    if method not in valid_methods:
                                        st.error(f"❌ Bilinmeyen yöntem: '{method}'. Lütfen geçerli bir yöntem seçin: {', '.join(valid_methods)}")
                                        logger.warning(f"Unknown method for missing_values: {method}")
                                    else:
                                        apply_preprocessing_suggestion(df, suggestion, step_key)
                                else:
                                    apply_preprocessing_suggestion(df, suggestion, step_key)
                    
                    with col3:
                        if st.button("Sonraki ▶️", key=f"next_suggestion_{step_key}", disabled=(current_index == len(suggestions) - 1), width='stretch'):
                            st.session_state[index_key] = min(len(suggestions) - 1, current_index + 1)
                            st.rerun()
                    
                    # Dots indicator
                    dots_html = "<div style='text-align: center; margin-top: 15px;'>"
                    for i in range(len(suggestions)):
                        if i == current_index:
                            dots_html += "🔵 "
                        else:
                            dots_html += "⚪ "
                    dots_html += "</div>"
                    st.markdown(dots_html, unsafe_allow_html=True)
    
    # Manual operations - Enhanced design
    st.markdown("### 🔧 Manuel İşlemler")
    
    # Create a styled container for manual operations
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    '>
    """, unsafe_allow_html=True)
    
    # Sütun Seçimi - Alt alta konumlandırıldı
    st.markdown("#### 📌 Sütun Seçimi")
    
    # Get columns with missing values
    missing_info = analyze_missing_values(df)
    columns_with_missing = missing_info.get('columns_with_missing', [])
    
    # Get already processed columns from step history (step 1 = missing values)
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == 1]
    processed_columns = set()
    for hist in step_history:
        hist_columns = hist.get('columns', [])
        if isinstance(hist_columns, list):
            processed_columns.update(hist_columns)
    
    # Filter out already processed columns from selection options
    available_columns = [col for col in columns_with_missing if col not in processed_columns]
    
    if available_columns:
        selected_columns = st.multiselect(
            "Eksik değerleri doldurmak istediğiniz sütunları seçin",
            options=available_columns,
            help=f"Eksik değer içeren {len(available_columns)} sütun gösteriliyor (Daha önce doldurulan {len(processed_columns)} sütun gizlendi)",
            label_visibility="collapsed"
        )
        
        # Show info message about selected columns
        if selected_columns:
            # Analyze selected columns
            selected_numeric = [col for col in selected_columns if col in numeric_cols]
            selected_categorical = [col for col in selected_columns if col in categorical_cols]
            
            if selected_numeric and selected_categorical:
                info_text = f"✅ {len(selected_numeric)} sayısal, {len(selected_categorical)} kategorik sütun seçildi"
            elif selected_numeric:
                info_text = f"✅ {len(selected_numeric)} sayısal sütun seçildi"
            elif selected_categorical:
                info_text = f"✅ {len(selected_categorical)} kategorik sütun seçildi"
            else:
                info_text = f"✅ {len(selected_columns)} sütun seçildi"
            st.info(info_text)
        else:
            # Show message when no columns are selected
            st.info("ℹ️ Lütfen eksik değerleri doldurmak istediğiniz sütunları seçin")
    else:
        if columns_with_missing:
            st.success(f"✅ Tüm eksik değer içeren sütunlar dolduruldu! ({len(processed_columns)} sütun)")
        else:
            st.success("✅ Veri setinde eksik değer bulunmuyor!")
        selected_columns = []
    
    st.markdown("<br>", unsafe_allow_html=True)  # Boşluk ekle
    
    # Yöntem Seçimi - Alt alta konumlandırıldı
    st.markdown("#### ⚙️ Yöntem Seçimi")
    
    # Analyze selected columns to determine available methods
    # First check if all missing columns have been processed (before checking selected_columns)
    all_columns_processed = len(columns_with_missing) > 0 and len(available_columns) == 0
    
    if selected_columns:
        selected_numeric = [col for col in selected_columns if col in numeric_cols]
        selected_categorical = [col for col in selected_columns if col in categorical_cols]
        
        if selected_numeric and selected_categorical:
            # Both types selected - show tabs
            tab1, tab2 = st.tabs(["🔢 Sayısal Sütunlar", "📝 Kategorik Sütunlar"])
            
            with tab1:
                numeric_method = st.selectbox(
                    "Sayısal sütunlar için yöntem",
                    options=['mean', 'median', 'interpolation', 'knn', 'forward_fill', 'backward_fill', 'drop'],
                    key="numeric_method_select",
                    help="Sayısal sütunlar için uygun yöntemler"
                )
                numeric_method_info = {
                    'mean': {
                        'name': 'Ortalama (Mean)',
                        'description': 'Eksik değerler, sütunun aritmetik ortalaması ile doldurulur. Normal dağılımlı veriler için idealdir.<br><br><strong>✓ Avantajları:</strong> Hesaplaması hızlı, basit ve anlaşılır.<br><strong>✗ Dezavantajları:</strong> Aykırı değerlerden etkilenir, dağılım normal değilse yanıltıcı olabilir.<br><strong>📌 Kullanım:</strong> Yaş, gelir gibi sürekli değişkenler için uygundur.'
                    },
                    'median': {
                        'name': 'Medyan (Median)',
                        'description': 'Eksik değerler, sütunun medyan (ortanca) değeri ile doldurulur. Aykırı değerlere karşı daha dayanıklıdır.<br><br><strong>✓ Avantajları:</strong> Aykırı değerlerden etkilenmez, güçlü bir merkezi eğilim ölçüsüdür.<br><strong>✗ Dezavantajları:</strong> Çok sayıda eksik değer varsa yetersiz kalabilir.<br><strong>📌 Kullanım:</strong> Aykırı değer içeren veriler, fiyat, maaş gibi asimetrik dağılımlar için idealdir.'
                    },
                    'interpolation': {
                        'name': 'İnterpolasyon',
                        'description': 'Bilinen değerlerden bilinmeyeni tahmin etme yöntemidir. Bilinen veri noktaları arasındaki eksik değerleri tahmin etme ve doldurmada önemli bir rol oynar.<br><br><strong>✓ Avantajları:</strong> Zaman içindeki trendleri korur, komşu değerler arasındaki ilişkiyi kullanır.<br><strong>✗ Dezavantajları:</strong> Ardışık eksik değerlerde başarısız olabilir.<br><strong>📌 Kullanım:</strong> Sıcaklık, fiyat geçmişi, zaman serileri için mükemmeldir.'
                    },
                    'knn': {
                        'name': 'K-NN (K-Nearest Neighbors)',
                        'description': 'Eksik değerler, en yakın k komşu satırın değerlerine göre tahmin edilir. İlişkili sütunlar varsa çok etkilidir.<br><br><strong>✓ Avantajları:</strong> Diğer sütunlardaki ilişkileri kullanır, karmaşık desenleri yakalayabilir.<br><strong>✗ Dezavantajları:</strong> Hesaplama maliyeti yüksek, büyük veri setlerinde yavaş.<br><strong>📌 Kullanım:</strong> Çok değişkenli veriler, birbirleriyle ilişkili sütunlar için idealdir.'
                    },
                    'forward_fill': {
                        'name': 'İleri Doldurma (Forward Fill)',
                        'description': 'Eksik değerler, bir önceki satırdaki değer ile ileriye doğru (aşağıya) doldurulur. Sıralı veriler için uygundur.<br><br><strong>✓ Avantajları:</strong> Basit ve hızlı, zaman serilerinde mantıklı.<br><strong>✗ Dezavantajları:</strong> İlk satırlar eksikse doldurulamaz, trend değişimlerini yansıtmayabilir.<br><strong>📌 Kullanım:</strong> Zaman serileri, ölçüm verileri, sıralı gözlemler için uygundur.'
                    },
                    'backward_fill': {
                        'name': 'Geri Doldurma (Backward Fill)',
                        'description': 'Eksik değerler, bir sonraki satırdaki değer ile geriye doğru (yukarıya) doldurulur. Sıralı veriler için uygundur.<br><br><strong>✓ Avantajları:</strong> Basit ve hızlı, son satırlardaki eksikleri doldurur.<br><strong>✗ Dezavantajları:</strong> Son satırlar eksikse doldurulamaz, geçmiş trendleri yansıtmayabilir.<br><strong>📌 Kullanım:</strong> Zaman serileri, ölçüm verileri, forward fill ile birlikte kullanılabilir.'
                    },
                    'drop': {
                        'name': 'Sütunu Sil (Drop Column)',
                        'description': 'Eksik değer içeren sütun tamamen silinir. Veri setinden kaldırılır.<br><br><strong>✓ Avantajları:</strong> Çok fazla eksik değer içeren sütunları temizler, model performansını artırabilir.<br><strong>✗ Dezavantajları:</strong> Sütun tamamen kaybolur, önemli bilgi kaybına neden olabilir.<br><strong>📌 Kullanım:</strong> Eksik değer yüzdesi >50% olan sütunlar için idealdir.'
                    }
                }
                method_info = numeric_method_info.get(numeric_method, {'name': numeric_method, 'description': 'Yöntem bilgisi bulunamadı'})
                st.markdown(f"""
                <div class="flip-card">
                    <div class="flip-card-inner">
                        <div class="flip-card-front">
                            <div>
                                <div style="font-size: 2.1em; font-weight: bold; margin-bottom: 5px;">📊 Bilgi Kartı</div>
                                <div style="font-size: 1.9em;">{method_info['name']}</div>
                            </div>
                        </div>
                        <div class="flip-card-back">
                            <div style="width: 100%;">
                                <div style="font-weight: bold; margin-bottom: 10px; font-size: 1.1em; text-align: center;">{method_info['name']}</div>
                                <div style="text-align: center; padding: 0 10px;">{method_info['description']}</div>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with tab2:
                categorical_method = st.selectbox(
                    "Kategorik sütunlar için yöntem",
                    options=['mode', 'forward_fill', 'backward_fill', 'drop'],
                    key="categorical_method_select",
                    help="Kategorik sütunlar için uygun yöntemler"
                )
                categorical_method_info = {
                    'mode': {
                        'name': 'Mod (En Sık Görülen)',
                        'description': 'Eksik değerler, sütunda en sık görülen (mod) değer ile doldurulur. Kategorik veriler için en yaygın yöntemdir.<br><br><strong>✓ Avantajları:</strong> Basit ve hızlı, kategorik veriler için mantıklı, veri dağılımını korur.<br><strong>✗ Dezavantajları:</strong> Çok sayıda benzersiz değer varsa yetersiz kalabilir.<br><strong>📌 Kullanım:</strong> Şehir, kategori, durum gibi nominal değişkenler için idealdir.'
                    },
                    'forward_fill': {
                        'name': 'İleri Doldurma (Forward Fill)',
                        'description': 'Eksik değerler, bir önceki satırdaki değer ile ileriye doğru (aşağıya) doldurulur. Sıralı kategorik veriler için uygundur.<br><br><strong>✓ Avantajları:</strong> Sıralı verilerde mantıklı, hızlı uygulanır.<br><strong>✗ Dezavantajları:</strong> İlk satırlar eksikse doldurulamaz, sıralı olmayan verilerde anlamsız olabilir.<br><strong>📌 Kullanım:</strong> Zaman serisi kategorileri, sıralı durumlar için uygundur.'
                    },
                    'backward_fill': {
                        'name': 'Geri Doldurma (Backward Fill)',
                        'description': 'Eksik değerler, bir sonraki satırdaki değer ile geriye doğru (yukarıya) doldurulur. Sıralı kategorik veriler için uygundur.<br><br><strong>✓ Avantajları:</strong> Son satırlardaki eksikleri doldurur, forward fill ile birlikte kullanılabilir.<br><strong>✗ Dezavantajları:</strong> Son satırlar eksikse doldurulamaz, sıralı olmayan verilerde anlamsız olabilir.<br><strong>📌 Kullanım:</strong> Zaman serisi kategorileri, forward fill ile birlikte kullanım için idealdir.'
                    },
                    'drop': {
                        'name': 'Sütunu Sil (Drop Column)',
                        'description': 'Eksik değer içeren sütun tamamen silinir. Veri setinden kaldırılır.<br><br><strong>✓ Avantajları:</strong> Çok fazla eksik değer içeren sütunları temizler, model performansını artırabilir.<br><strong>✗ Dezavantajları:</strong> Sütun tamamen kaybolur, önemli bilgi kaybına neden olabilir.<br><strong>📌 Kullanım:</strong> Eksik değer yüzdesi >50% olan sütunlar için idealdir.'
                    }
                }
                method_info = categorical_method_info.get(categorical_method, {'name': categorical_method, 'description': 'Yöntem bilgisi bulunamadı'})
                st.markdown(f"""
                <div class="flip-card">
                    <div class="flip-card-inner">
                        <div class="flip-card-front">
                            <div>
                                <div style="font-size: 2.1em; font-weight: bold; margin-bottom: 5px;">📊 Bilgi Kartı</div>
                                <div style="font-size: 1.9em;">{method_info['name']}</div>
                            </div>
                        </div>
                        <div class="flip-card-back">
                            <div style="width: 100%;">
                                <div style="font-weight: bold; margin-bottom: 10px; font-size: 1.1em; text-align: center;">{method_info['name']}</div>
                                <div style="text-align: center; padding: 0 10px;">{method_info['description']}</div>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            # Store both methods
            method = {
                'numeric': numeric_method if selected_numeric else None,
                'categorical': categorical_method if selected_categorical else None,
                'numeric_cols': selected_numeric,
                'categorical_cols': selected_categorical
            }
        elif selected_numeric:
            # Only numeric
            method = st.selectbox(
                "Sayısal sütunlar için yöntem",
                options=['mean', 'median', 'interpolation', 'knn', 'forward_fill', 'backward_fill', 'drop'],
                key="method_select_numeric_only",
                help="Sayısal sütunlar için uygun yöntemler",
                label_visibility="collapsed"
            )
            numeric_method_info = {
                'mean': {
                    'name': 'Ortalama (Mean)',
                    'description': 'Eksik değerler, sütunun aritmetik ortalaması ile doldurulur. Normal dağılımlı veriler için idealdir.<br><br><strong>✓ Avantajları:</strong> Hesaplaması hızlı, basit ve anlaşılır.<br><strong>✗ Dezavantajları:</strong> Aykırı değerlerden etkilenir, dağılım normal değilse yanıltıcı olabilir.<br><strong>📌 Kullanım:</strong> Yaş, gelir gibi sürekli değişkenler için uygundur.'
                },
                'median': {
                    'name': 'Medyan (Median)',
                    'description': 'Eksik değerler, sütunun medyan (ortanca) değeri ile doldurulur. Aykırı değerlere karşı daha dayanıklıdır.<br><br><strong>✓ Avantajları:</strong> Aykırı değerlerden etkilenmez, güçlü bir merkezi eğilim ölçüsüdür.<br><strong>✗ Dezavantajları:</strong> Çok sayıda eksik değer varsa yetersiz kalabilir.<br><strong>📌 Kullanım:</strong> Aykırı değer içeren veriler, fiyat, maaş gibi asimetrik dağılımlar için idealdir.'
                },
                'interpolation': {
                    'name': 'İnterpolasyon',
                    'description': 'Bilinen değerlerden bilinmeyeni tahmin etme yöntemidir. Bilinen veri noktaları arasındaki eksik değerleri tahmin etme ve doldurmada önemli bir rol oynar.<br><br><strong>✓ Avantajları:</strong> Zaman içindeki trendleri korur, komşu değerler arasındaki ilişkiyi kullanır.<br><strong>✗ Dezavantajları:</strong> Ardışık eksik değerlerde başarısız olabilir.<br><strong>📌 Kullanım:</strong> Sıcaklık, fiyat geçmişi, zaman serileri için mükemmeldir.'
                },
                'knn': {
                    'name': 'K-NN (K-Nearest Neighbors)',
                    'description': 'Eksik değerler, en yakın k komşu satırın değerlerine göre tahmin edilir. İlişkili sütunlar varsa çok etkilidir.<br><br><strong>✓ Avantajları:</strong> Diğer sütunlardaki ilişkileri kullanır, karmaşık desenleri yakalayabilir.<br><strong>✗ Dezavantajları:</strong> Hesaplama maliyeti yüksek, büyük veri setlerinde yavaş.<br><strong>📌 Kullanım:</strong> Çok değişkenli veriler, birbirleriyle ilişkili sütunlar için idealdir.'
                },
                'forward_fill': {
                    'name': 'İleri Doldurma (Forward Fill)',
                    'description': 'Eksik değerler, bir önceki satırdaki değer ile ileriye doğru (aşağıya) doldurulur. Sıralı veriler için uygundur.<br><br><strong>✓ Avantajları:</strong> Basit ve hızlı, zaman serilerinde mantıklı.<br><strong>✗ Dezavantajları:</strong> İlk satırlar eksikse doldurulamaz, trend değişimlerini yansıtmayabilir.<br><strong>📌 Kullanım:</strong> Zaman serileri, ölçüm verileri, sıralı gözlemler için uygundur.'
                },
                'backward_fill': {
                    'name': 'Geri Doldurma (Backward Fill)',
                    'description': 'Eksik değerler, bir sonraki satırdaki değer ile geriye doğru (yukarıya) doldurulur. Sıralı veriler için uygundur.<br><br><strong>✓ Avantajları:</strong> Basit ve hızlı, son satırlardaki eksikleri doldurur.<br><strong>✗ Dezavantajları:</strong> Son satırlar eksikse doldurulamaz, geçmiş trendleri yansıtmayabilir.<br><strong>📌 Kullanım:</strong> Zaman serileri, ölçüm verileri, forward fill ile birlikte kullanılabilir.'
                },
                'drop': {
                    'name': 'Sütun Sil (Drop Column)',
                    'description': 'Eksik değer içeren sütunları veri setinden tamamen kaldırır. Çok yüksek oranda eksik değer (>50%) içeren sütunlar için idealdir.<br><br><strong>✓ Avantajları:</strong> Model performansını artırabilir, veri setini sadeleştirir.<br><strong>✗ Dezavantajları:</strong> Bilgi kaybına neden olabilir, dikkatli kullanılmalıdır.<br><strong>📌 Kullanım:</strong> Eksik değer yüzdesi çok yüksek olan (örn. %70 üzeri) sütunlar için uygundur.'
                }
            }
            method_info = numeric_method_info.get(method, {'name': method, 'description': 'Yöntem bilgisi bulunamadı'})
            st.markdown(f"""
            <div class="flip-card">
                <div class="flip-card-inner">
                    <div class="flip-card-front">
                        <div>
                            <div style="font-size: 2.1em; font-weight: bold; margin-bottom: 5px;">📊 Bilgi Kartı</div>
                            <div style="font-size: 1.9em;">{method_info['name']}</div>
                        </div>
                    </div>
                    <div class="flip-card-back">
                        <div>
                            <div style="font-weight: bold; margin-bottom: 8px; text-align: center;">{method_info['name']}</div>
                            <div style="text-align: center;">{method_info['description']}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            method = {'numeric': method, 'categorical': None, 'numeric_cols': selected_numeric, 'categorical_cols': []}
        elif selected_categorical:
            # Only categorical
            method = st.selectbox(
                "Kategorik sütunlar için yöntem",
                options=['mode', 'forward_fill', 'backward_fill', 'drop'],
                key="method_select_categorical_only",
                help="Kategorik sütunlar için uygun yöntemler",
                label_visibility="collapsed"
            )
            categorical_method_info = {
                'mode': {
                    'name': 'Mod (En Sık Görülen)',
                    'description': 'Eksik değerler, sütunda en sık görülen (mod) değer ile doldurulur. Kategorik veriler için en yaygın yöntemdir.<br><br><strong>✓ Avantajları:</strong> Basit ve hızlı, kategorik veriler için mantıklı, veri dağılımını korur.<br><strong>✗ Dezavantajları:</strong> Çok sayıda benzersiz değer varsa yetersiz kalabilir.<br><strong>📌 Kullanım:</strong> Şehir, kategori, durum gibi nominal değişkenler için idealdir.'
                },
                'forward_fill': {
                    'name': 'İleri Doldurma (Forward Fill)',
                    'description': 'Eksik değerler, bir önceki satırdaki değer ile ileriye doğru (aşağıya) doldurulur. Sıralı kategorik veriler için uygundur.<br><br><strong>✓ Avantajları:</strong> Sıralı verilerde mantıklı, hızlı uygulanır.<br><strong>✗ Dezavantajları:</strong> İlk satırlar eksikse doldurulamaz, sıralı olmayan verilerde anlamsız olabilir.<br><strong>📌 Kullanım:</strong> Zaman serisi kategorileri, sıralı durumlar için uygundur.'
                },
                'backward_fill': {
                    'name': 'Geri Doldurma (Backward Fill)',
                    'description': 'Eksik değerler, bir sonraki satırdaki değer ile geriye doğru (yukarıya) doldurulur. Sıralı kategorik veriler için uygundur.<br><br><strong>✓ Avantajları:</strong> Son satırlardaki eksikleri doldurur, forward fill ile birlikte kullanılabilir.<br><strong>✗ Dezavantajları:</strong> Son satırlar eksikse doldurulamaz, sıralı olmayan verilerde anlamsız olabilir.<br><strong>📌 Kullanım:</strong> Zaman serisi kategorileri, forward fill ile birlikte kullanım için idealdir.'
                },
                'drop': {
                    'name': 'Sütunu Sil (Drop Column)',
                    'description': 'Eksik değer içeren sütun tamamen silinir. Veri setinden kaldırılır.<br><br><strong>✓ Avantajları:</strong> Çok fazla eksik değer içeren sütunları temizler, model performansını artırabilir.<br><strong>✗ Dezavantajları:</strong> Sütun tamamen kaybolur, önemli bilgi kaybına neden olabilir.<br><strong>📌 Kullanım:</strong> Eksik değer yüzdesi >50% olan sütunlar için idealdir.'
                }
            }
            method_info = categorical_method_info.get(method, {'name': method, 'description': 'Yöntem bilgisi bulunamadı'})
            st.markdown(f"""
            <div class="flip-card">
                <div class="flip-card-inner">
                    <div class="flip-card-front">
                        <div>
                            <div style="font-size: 2.1em; font-weight: bold; margin-bottom: 5px;">📊 Bilgi Kartı</div>
                            <div style="font-size: 1.9em;">{method_info['name']}</div>
                        </div>
                    </div>
                    <div class="flip-card-back">
                        <div>
                            <div style="font-weight: bold; margin-bottom: 8px; text-align: center;">{method_info['name']}</div>
                            <div style="text-align: center;">{method_info['description']}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            method = {'numeric': None, 'categorical': method, 'numeric_cols': [], 'categorical_cols': selected_categorical}
        else:
            method = None
            st.warning("⚠️ Seçilen sütunların tipi belirlenemedi")
    else:
        method = None
        # Check if all missing value columns have been processed
        if all_columns_processed:
            st.info("ℹ️ Bütün eksik değer içeren sütunlar işlenmiştir. Sonraki adıma geçebilirsiniz.")
        else:
            st.info("ℹ️ Önce sütun seçin")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Action buttons - Uygula butonu tüm satırı kaplar
    # Uygula butonu sadece yöntem seçildiğinde gösterilir (adım 1 mantığı)
    if selected_columns and method:
        if st.button("✅ Uygula", key="apply_missing", type="primary", use_container_width=True):
                try:
                    df_processed = current_df.copy()
                    total_filled = 0
                    processed_columns = []
                    
                    # Process numeric columns
                    if isinstance(method, dict) and method.get('numeric') and method.get('numeric_cols'):
                        numeric_cols_to_process = method['numeric_cols']
                        numeric_method = method['numeric']
                        
                        if numeric_cols_to_process:
                            if numeric_method == 'drop':
                                # Drop columns
                                df_processed = apply_missing_values_method(df_processed, numeric_cols_to_process, numeric_method)
                                processed_columns.extend(numeric_cols_to_process)
                            else:
                                missing_before = df_processed[numeric_cols_to_process].isnull().sum().sum()
                                df_processed = apply_missing_values_method(df_processed, numeric_cols_to_process, numeric_method)
                                missing_after = df_processed[numeric_cols_to_process].isnull().sum().sum()
                                filled_numeric = missing_before - missing_after
                                total_filled += filled_numeric
                                processed_columns.extend(numeric_cols_to_process)
                    
                    # Process categorical columns
                    if isinstance(method, dict) and method.get('categorical') and method.get('categorical_cols'):
                        categorical_cols_to_process = method['categorical_cols']
                        categorical_method = method['categorical']
                        
                        if categorical_cols_to_process:
                            if categorical_method == 'drop':
                                # Drop columns
                                df_processed = apply_missing_values_method(df_processed, categorical_cols_to_process, categorical_method)
                                processed_columns.extend(categorical_cols_to_process)
                            else:
                                missing_before = df_processed[categorical_cols_to_process].isnull().sum().sum()
                                df_processed = apply_missing_values_method(df_processed, categorical_cols_to_process, categorical_method)
                                missing_after = df_processed[categorical_cols_to_process].isnull().sum().sum()
                                filled_categorical = missing_before - missing_after
                                total_filled += filled_categorical
                                processed_columns.extend(categorical_cols_to_process)
                    
                    # If method is a simple string (backward compatibility)
                    elif isinstance(method, str):
                        # Use current_df to get numeric and categorical columns (not global variables)
                        current_numeric_cols = current_df.select_dtypes(include=[np.number]).columns.tolist()
                        current_categorical_cols = current_df.select_dtypes(include=['object', 'category']).columns.tolist()
                        selected_numeric = [col for col in selected_columns if col in current_numeric_cols]
                        selected_categorical = [col for col in selected_columns if col in current_categorical_cols]
                        
                        if method in ['mean', 'median', 'interpolation', 'knn'] and selected_numeric:
                            missing_before = df_processed[selected_numeric].isnull().sum().sum()
                            df_processed = apply_missing_values_method(df_processed, selected_numeric, method)
                            missing_after = df_processed[selected_numeric].isnull().sum().sum()
                            total_filled = missing_before - missing_after
                            processed_columns = selected_numeric
                        elif method in ['mode'] and selected_categorical:
                            missing_before = df_processed[selected_categorical].isnull().sum().sum()
                            df_processed = apply_missing_values_method(df_processed, selected_categorical, method)
                            missing_after = df_processed[selected_categorical].isnull().sum().sum()
                            total_filled = missing_before - missing_after
                            processed_columns = selected_categorical
                        elif method == 'drop':
                            # Drop columns - no need to count missing values
                            df_processed = apply_missing_values_method(df_processed, selected_columns, method)
                            processed_columns = selected_columns
                        elif method in ['forward_fill', 'backward_fill']:
                            missing_before = df_processed[selected_columns].isnull().sum().sum()
                            df_processed = apply_missing_values_method(df_processed, selected_columns, method)
                            missing_after = df_processed[selected_columns].isnull().sum().sum()
                            total_filled = missing_before - missing_after
                            processed_columns = selected_columns
                    
                    if processed_columns:
                        # Save to session state
                        st.session_state.preprocessed_data = df_processed
                        
                        # Store method info for history
                        if isinstance(method, dict):
                            method_str = f"Sayısal: {method.get('numeric', 'N/A')}, Kategorik: {method.get('categorical', 'N/A')}"
                        else:
                            method_str = method
                        
                        # Add to history
                        st.session_state.preprocessing_history.append({
                            'step': current_step,
                            'step_key': step_key,
                            'type': step_key,
                            'method': method_str if isinstance(method, dict) else method,
                            'method_dict': method if isinstance(method, dict) else None,  # Store dict for undo
                            'columns': processed_columns,
                            'timestamp': datetime.now().isoformat(),
                            'before_data': df.copy()  # Store before state for undo
                        })
                        
                        # Check if any method is drop
                        is_drop = False
                        if isinstance(method, dict):
                            is_drop = (method.get('numeric') == 'drop') or (method.get('categorical') == 'drop')
                        else:
                            is_drop = (method == 'drop')
                        
                        if is_drop:
                            st.success(f"✅ İşlem başarıyla uygulandı! {len(processed_columns)} sütun silindi: {', '.join(processed_columns)}")
                        elif total_filled > 0:
                            st.success(f"✅ İşlem başarıyla uygulandı! {total_filled:,} eksik değer dolduruldu ({len(processed_columns)} sütun).")
                        else:
                            st.warning(f"⚠️ İşlem uygulandı ancak eksik değer bulunamadı veya doldurulamadı.")
                        st.rerun()
                    else:
                        st.error("❌ İşlenecek sütun bulunamadı. Lütfen sütun tiplerini kontrol edin.")
                except Exception as e:
                    st.error(f"❌ Hata oluştu: {str(e)}")
                    logger.error(f"Error applying missing values method: {e}", exc_info=True)
                    import traceback
                    logger.error(traceback.format_exc())
        elif not selected_columns:
            st.warning("⚠️ Lütfen en az bir sütun seçin")
        elif not method:
            st.warning("⚠️ Lütfen bir yöntem seçin")
    
    # Show applied operations for this step with undo functionality - ALWAYS SHOW
    st.markdown("### 📋 Uygulanan İşlemler")
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
    if step_history:
        for idx, hist in enumerate(step_history):
            method = hist.get('method', '')
            columns = hist.get('columns', [])
            
            # Format method display
            # Helper function to get action verb based on method
            def get_action_verb(method_name):
                return "ile silindi" if method_name == 'drop' else "ile dolduruldu"
            
            if isinstance(method, dict):
                # Handle dict method (numeric and categorical separately)
                method_parts = []
                if method.get('numeric') and method.get('numeric_cols'):
                    numeric_cols_list = method.get('numeric_cols', [])
                    numeric_method = method.get('numeric', '')
                    action_verb = get_action_verb(numeric_method)
                    for col in numeric_cols_list:
                        method_parts.append(f"{col} sütunu - {numeric_method} {action_verb}")
                if method.get('categorical') and method.get('categorical_cols'):
                    categorical_cols_list = method.get('categorical_cols', [])
                    categorical_method = method.get('categorical', '')
                    action_verb = get_action_verb(categorical_method)
                    for col in categorical_cols_list:
                        method_parts.append(f"{col} sütunu - {categorical_method} {action_verb}")
                display_text = '<br>'.join(method_parts) if method_parts else 'İşlem uygulandı'
            else:
                # Handle string method
                action_verb = get_action_verb(method)
                if columns:
                    if len(columns) == 1:
                        display_text = f"{columns[0]} sütunu - {method} {action_verb}"
                    else:
                        columns_str = ', '.join(columns)
                        display_text = f"{columns_str} sütunları - {method} {action_verb}"
                else:
                    display_text = f"Tüm sütunlar - {method} {action_verb}"
            
            # Create a styled card for each operation
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 5px 0;
                    color: white;
                '>
                    <span style='font-size: 1.2em; margin-right: 10px;'>✅</span>
                    {display_text}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("↶ Geri Al", key=f"undo_{current_step}_{idx}", width='stretch'):
                    # Remove this operation from history
                    operation_to_remove = step_history[idx]
                    remove_method = operation_to_remove.get('method', '')
                    remove_columns = operation_to_remove.get('columns', [])
                    
                    st.session_state.preprocessing_history.remove(operation_to_remove)
                    
                    # Rebuild the dataframe by reapplying ALL operations in order (all steps)
                    # Suppress INFO logs during rebuild
                    original_log_level = logger.level
                    logger.setLevel(logging.WARNING)
                    try:
                        df_rebuilt = st.session_state.original_data.copy()
                        
                        # Apply all operations in correct order: feature_engineering -> missing_values -> outlier -> encoding
                        for op in st.session_state.preprocessing_history:
                            op_type = op.get('type', '')
                            
                            if op_type == 'feature_engineering':
                                op_method = op.get('method', '')
                                if op_method == 'remove_duplicates':
                                    df_rebuilt = remove_duplicate_rows(df_rebuilt, keep=op.get('keep', 'first'))
                                elif op_method == 'drop_column':
                                    df_rebuilt = drop_columns(df_rebuilt, op.get('columns', []))
                                elif op_method == 'create_numeric_feature':
                                    df_rebuilt = create_numeric_feature(
                                        df_rebuilt,
                                        op.get('operation', 'add'),
                                        op.get('columns', []),
                                        op.get('new_column_name', '')
                                    )
                                elif op_method == 'create_datetime_feature':
                                    df_rebuilt = create_datetime_feature(
                                        df_rebuilt,
                                        op.get('columns', [])[0] if op.get('columns') else '',
                                        op.get('feature_type', 'year'),
                                        op.get('new_column_name', '')
                                    )
                                elif op_method == 'create_categorical_combination':
                                    df_rebuilt = create_categorical_combination(
                                        df_rebuilt,
                                        op.get('columns', []),
                                        op.get('new_column_name', ''),
                                        op.get('separator', '_')
                                    )
                            elif op_type == 'missing_values':
                                op_method_dict = op.get('method_dict')
                                if op_method_dict:
                                    # Handle dict method (numeric and categorical separately)
                                    if op_method_dict.get('numeric') and op_method_dict.get('numeric_cols'):
                                        df_rebuilt = apply_missing_values_method(
                                            df_rebuilt, 
                                            op_method_dict['numeric_cols'], 
                                            op_method_dict['numeric']
                                        )
                                    if op_method_dict.get('categorical') and op_method_dict.get('categorical_cols'):
                                        df_rebuilt = apply_missing_values_method(
                                            df_rebuilt, 
                                            op_method_dict['categorical_cols'], 
                                            op_method_dict['categorical']
                                        )
                                else:
                                    # Handle string method
                                    df_rebuilt = apply_missing_values_method(
                                        df_rebuilt, 
                                        op.get('columns', []), 
                                        op.get('method', '')
                                    )
                            elif op_type == 'outlier':
                                outlier_method = op.get('method', '')
                                method_parts = outlier_method.split('_')
                                if len(method_parts) >= 2:
                                    detection_method = '_'.join(method_parts[:-1])
                                    action = method_parts[-1]
                                    df_rebuilt = apply_outlier_method_wrapper(
                                        df_rebuilt,
                                        op.get('columns', []),
                                        detection_method,
                                        action
                                    )
                            elif op_type == 'encoding':
                                df_rebuilt = apply_encoding_method(
                                    df_rebuilt,
                                    op.get('columns', []),
                                    op.get('method', '')
                                )
                    finally:
                        # Restore original log level
                        logger.setLevel(original_log_level)
                    
                    # Update preprocessed data
                    st.session_state.preprocessed_data = df_rebuilt
                    
                    # Remove from applied_suggestion_ids if it was from LLM
                    if operation_to_remove.get('from_llm'):
                        suggestion_id = f"{step_key}_{remove_method}_{'_'.join(remove_columns) if remove_columns else 'all'}"
                        if suggestion_id in st.session_state.applied_suggestion_ids:
                            st.session_state.applied_suggestion_ids.remove(suggestion_id)
                    
                    st.success("✅ İşlem geri alındı!")
                    st.rerun()
    else:
        st.info("ℹ️ Henüz bu adımda işlem uygulanmadı.")
    
    # Add spacing before navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Action buttons - right aligned at bottom
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([3, 1, 1, 1])
    with col_nav2:
        if current_step > 1:
            if st.button("← Geri", key="prev_step_missing_values", width='stretch'):
                st.session_state.preprocessing_step -= 1
                st.rerun()
    with col_nav3:
        # Atla butonu - son adımda (Summary) gösterilmez
        if current_step < len(steps):
            if st.button("Atla", key="skip_step_missing_values", width='stretch'):
                st.session_state.preprocessing_step += 1
                st.rerun()
    with col_nav4:
        has_operation = check_step_has_operation(current_step)
        if st.button("İleri →", key="next_step_manual", disabled=not has_operation, width='stretch'):
            st.session_state.preprocessing_step += 1
            st.rerun()


def apply_missing_values_method(df, columns, method):
    """Apply missing values method."""
    if not columns:
        logger.warning("No columns provided to apply_missing_values_method")
        return df
    
    logger.debug(f"Applying method '{method}' to columns: {columns}")
    
    try:
        # Count missing before
        missing_before = df[columns].isnull().sum().sum()
        logger.debug(f"Missing values before: {missing_before}")
        
        if method == 'mean':
            result = fill_missing_values_mean(df, columns)
        elif method == 'median':
            result = fill_missing_values_median(df, columns)
        elif method == 'mode':
            result = fill_missing_values_mode(df, columns)
        elif method == 'forward_fill':
            result = fill_missing_values_forward_fill(df, columns)
        elif method == 'backward_fill':
            result = fill_missing_values_backward_fill(df, columns)
        elif method == 'interpolation':
            result = fill_missing_values_interpolation(df, columns)
        elif method == 'knn':
            result = fill_missing_values_knn(df, columns)
        elif method == 'drop':
            result = fill_missing_values_drop(df, columns)
            # For drop method, columns are removed, so we can't check them
            # Just verify that columns were actually dropped
            dropped_cols = [col for col in columns if col not in result.columns]
            logger.debug(f"Dropped columns: {dropped_cols}")
            return result
        else:
            logger.warning(f"Unknown method: {method}")
            return df
        
        # Count missing after (only for fill methods, not drop)
        missing_after = result[columns].isnull().sum().sum()
        filled = missing_before - missing_after
        logger.debug(f"Missing values after: {missing_after}, Filled: {filled}")
        
        if filled == 0 and missing_before > 0:
            logger.warning(f"Method {method} did not fill any values. Missing before: {missing_before}")
        
        return result
    except Exception as e:
        logger.error(f"Error in apply_missing_values_method: {e}", exc_info=True)
        raise


def apply_encoding_method(df, columns, method):
    """Apply encoding method."""
    if not columns:
        logger.warning("No columns provided to apply_encoding_method")
        return df
    
    logger.debug(f"Applying encoding method '{method}' to columns: {columns}")
    
    try:
        # Store original column count
        original_col_count = len(df.columns)
        logger.debug(f"Original column count: {original_col_count}")
        
        if method == 'label_encoding':
            result = label_encode(df, columns)
        elif method == 'one_hot_encoding':
            result = one_hot_encode(df, columns)
        elif method == 'ordinal_encoding':
            result = ordinal_encode(df, columns)
        elif method == 'binary_encoding':
            result = binary_encode(df, columns)
        elif method == 'frequency_encoding':
            result = frequency_encode(df, columns)
        else:
            logger.warning(f"Unknown encoding method: {method}")
            return df
        
        # Check column count change
        new_col_count = len(result.columns)
        col_diff = new_col_count - original_col_count
        logger.debug(f"Column count after: {new_col_count}, Difference: {col_diff}")
        
        if col_diff > 0:
            logger.info(f"✅ Encoding method {method} added {col_diff} new columns")
        elif col_diff < 0:
            logger.info(f"✅ Encoding method {method} removed {abs(col_diff)} columns")
        else:
            logger.info(f"✅ Encoding method {method} applied (column count unchanged)")
        
        return result
    except Exception as e:
        logger.error(f"Error in apply_encoding_method: {e}", exc_info=True)
        raise


def apply_scaling_method_wrapper(df, columns, method, **kwargs):
    """Apply scaling method to specified columns."""
    if not columns:
        logger.warning("No columns provided to apply_scaling_method_wrapper")
        return df
    
    logger.debug(f"Applying scaling method '{method}' to columns: {columns}")
    
    try:
        result = apply_scaling_method(df, columns, method, **kwargs)
        logger.info(f"✅ Scaling method {method} applied to {len(columns)} columns")
        return result
    except Exception as e:
        logger.error(f"Error in apply_scaling_method_wrapper: {e}", exc_info=True)
        raise


def apply_outlier_method_wrapper(df, columns, detection_method, action, **kwargs):
    """Wrapper function to apply outlier method."""
    logger.debug(f"🔍 [OUTLIER WRAPPER] Called with detection_method: {detection_method}, action: {action}, columns: {columns}")
    logger.debug(f"🔍 [OUTLIER WRAPPER] df shape before: {df.shape if df is not None else 'None'}")
    logger.debug(f"🔍 [OUTLIER WRAPPER] df columns before: {list(df.columns) if df is not None else 'None'}")
    
    if not columns:
        logger.warning("⚠️ [OUTLIER WRAPPER] No columns provided")
        return df
    
    # Filter columns to only those that exist in dataframe
    valid_columns = [col for col in columns if col in df.columns]
    if len(valid_columns) != len(columns):
        logger.warning(f"⚠️ [OUTLIER WRAPPER] Some columns not found in dataframe. Requested: {columns}, Found: {valid_columns}")
        columns = valid_columns
    
    if not columns:
        logger.error("❌ [OUTLIER WRAPPER] No valid columns found in dataframe")
        return df
    
    try:
        logger.debug(f"🔍 [OUTLIER WRAPPER] Calling apply_outlier_method with columns: {columns}")
        result = apply_outlier_method(df, columns, detection_method, action, **kwargs)
        logger.debug(f"🔍 [OUTLIER WRAPPER] df shape after: {result.shape if result is not None else 'None'}")
        logger.debug(f"🔍 [OUTLIER WRAPPER] df columns after: {list(result.columns) if result is not None else 'None'}")
        logger.info(f"✅ [OUTLIER WRAPPER] Outlier method {detection_method} with action {action} applied to columns: {columns}")
        return result
    except Exception as e:
        logger.error(f"❌ [OUTLIER WRAPPER] Error in apply_outlier_method: {e}", exc_info=True)
        import traceback
        logger.error(f"❌ [OUTLIER WRAPPER] Traceback: {traceback.format_exc()}")
        raise


def apply_preprocessing_suggestion(df, suggestion, step_type):
    """Apply LLM preprocessing suggestion."""
    method = suggestion.get('method', '')
    columns = suggestion.get('columns', [])
    
    # Convert to Python list if it's a protobuf object
    if not isinstance(columns, list):
        columns = list(columns)
    
    logger.debug(f"🔍 [APPLY SUGGESTION] step_type: {step_type}, method: {method}, columns: {columns}")
    logger.debug(f"🔍 [APPLY SUGGESTION] df shape before: {df.shape if df is not None else 'None'}")
    
    # Normalize columns list - filter out empty strings and None values
    if isinstance(columns, list):
        columns = [col for col in columns if col and col.strip()]
    suggestion_id = f"{step_type}_{method}_{'_'.join(columns) if columns else 'all'}"
    logger.debug(f"🔍 [APPLY SUGGESTION] Checking suggestion_id: {suggestion_id}")
    logger.debug(f"🔍 [APPLY SUGGESTION] step_type: {step_type}, method: {method}, columns: {columns}")
    logger.debug(f"🔍 [APPLY SUGGESTION] Current applied_suggestion_ids: {st.session_state.applied_suggestion_ids}")
    if suggestion_id in st.session_state.applied_suggestion_ids:
        st.warning("Bu öneri zaten uygulandı")
        logger.warning(f"⚠️ [APPLY SUGGESTION] Suggestion already applied: {suggestion_id}")
        return
    
    # Apply based on step type and method
    df_processed = df.copy()
    
    if step_type == 'missing_values':
        logger.debug(f"🔍 [APPLY SUGGESTION] Applying missing_values method: {method}")
        df_processed = apply_missing_values_method(df_processed, columns, method)
        logger.debug(f"🔍 [APPLY SUGGESTION] df shape after missing_values: {df_processed.shape}")
    elif step_type == 'outlier':
        # Outlier method format: "detection_method_action" (e.g., "iqr_remove", "zscore_cap")
        # Parse method to get detection method and action
        method_parts = method.split('_')
        logger.debug(f"🔍 [APPLY SUGGESTION] Outlier method parts: {method_parts}")
        if len(method_parts) >= 2:
            detection_method = '_'.join(method_parts[:-1])  # e.g., "isolation_forest"
            action = method_parts[-1]  # "remove" or "cap"
            logger.debug(f"🔍 [APPLY SUGGESTION] Parsed - detection_method: {detection_method}, action: {action}")
            logger.debug(f"🔍 [APPLY SUGGESTION] df shape before outlier method: {df_processed.shape}")
            logger.debug(f"🔍 [APPLY SUGGESTION] df columns before: {list(df_processed.columns)}")
            try:
                df_processed = apply_outlier_method_wrapper(df_processed, columns, detection_method, action)
                logger.debug(f"🔍 [APPLY SUGGESTION] df shape after outlier method: {df_processed.shape}")
                logger.debug(f"🔍 [APPLY SUGGESTION] df columns after: {list(df_processed.columns)}")
            except Exception as e:
                logger.error(f"❌ [APPLY SUGGESTION] Error in apply_outlier_method_wrapper: {e}", exc_info=True)
                st.error(f"❌ Hata: {str(e)}")
                return
        else:
            logger.warning(f"⚠️ [APPLY SUGGESTION] Invalid outlier method format: {method}")
            st.error(f"❌ Geçersiz yöntem formatı: {method}")
            return
    elif step_type == 'encoding':
        logger.debug(f"🔍 [APPLY SUGGESTION] Applying encoding method: {method}")
        df_processed = apply_encoding_method(df_processed, columns, method)
        logger.debug(f"🔍 [APPLY SUGGESTION] df shape after encoding: {df_processed.shape}")
    elif step_type == 'scaling':
        logger.debug(f"🔍 [APPLY SUGGESTION] Applying scaling method: {method}")
        df_processed = apply_scaling_method_wrapper(df_processed, columns, method)
        logger.debug(f"🔍 [APPLY SUGGESTION] df shape after scaling: {df_processed.shape}")
    elif step_type == 'feature_engineering':
        logger.debug(f"🔍 [APPLY SUGGESTION] Applying feature_engineering method: {method}")
        # Parse method and extract parameters from suggestion
        if method == 'remove_duplicates':
            keep = suggestion.get('keep', 'first')
            df_processed = remove_duplicate_rows(df_processed, keep=keep)
        elif method == 'drop_column':
            df_processed = drop_columns(df_processed, columns)
        elif method == 'create_numeric_feature':
            operation = suggestion.get('operation', 'add')
            new_column_name = suggestion.get('new_column_name', '')
            df_processed = create_numeric_feature(df_processed, operation, columns, new_column_name)
        elif method == 'create_datetime_feature':
            column = columns[0] if columns else ''
            feature_type = suggestion.get('feature_type', 'year')
            new_column_name = suggestion.get('new_column_name', '')
            df_processed = create_datetime_feature(df_processed, column, feature_type, new_column_name)
        elif method == 'create_categorical_combination':
            separator = suggestion.get('separator', '_')
            new_column_name = suggestion.get('new_column_name', '')
            df_processed = create_categorical_combination(df_processed, columns, new_column_name, separator)
        logger.debug(f"🔍 [APPLY SUGGESTION] df shape after feature_engineering: {df_processed.shape}")
    
    # Save to session state
    st.session_state.preprocessed_data = df_processed
    st.session_state.applied_suggestion_ids.append(suggestion_id)
    
    history_item = {
        'step': current_step,
        'step_key': step_type,
        'type': step_type,
        'method': method,
        'columns': columns,
        'timestamp': datetime.now().isoformat(),
        'from_llm': True,
        'before_data': df.copy()  # Store before state for undo
    }
    st.session_state.preprocessing_history.append(history_item)
    
    logger.info(f"✅ [APPLY] {step_type} - {method} applied")
    if step_type == 'feature_engineering':
        if method == 'remove_duplicates':
            st.success(f"✅ Tekrarlayan satırlar başarıyla kaldırıldı!")
        elif method == 'drop_column':
            st.success(f"✅ {len(columns)} sütun başarıyla silindi: {', '.join(columns)}")
        elif method in ['create_numeric_feature', 'create_datetime_feature', 'create_categorical_combination']:
            new_column_name = suggestion.get('new_column_name', '')
            st.success(f"✅ Yeni özellik '{new_column_name}' başarıyla oluşturuldu!")
        else:
            st.success(f"✅ Feature engineering işlemi başarıyla uygulandı!")
    elif step_type == 'encoding':
        st.success(f"✅ Encoding başarıyla uygulandı! {len(columns)} sütun işlendi: {', '.join(columns)}")
    else:
        st.success(f"✅ İşlem başarıyla uygulandı!")
    st.rerun()


def get_processed_encoding_columns():
    """Helper function to get all processed encoding columns from history."""
    processed_columns = set()
    encoding_methods = {}  # Store method used for each column
    
    # Check ALL preprocessing history for encoding operations
    all_history = st.session_state.preprocessing_history
    encoding_count = 0
    
    for hist in all_history:
        hist_type = hist.get('type', '')
        hist_step_key = hist.get('step_key', '')
        is_encoding = (hist_type == 'encoding' or hist_step_key == 'encoding')
        
        if is_encoding:
            hist_columns = hist.get('columns', [])
            # Convert to Python list if it's a protobuf object
            if not isinstance(hist_columns, list):
                hist_columns = list(hist_columns)
            hist_method = hist.get('method', '')
            
            if isinstance(hist_columns, list) and len(hist_columns) > 0:
                encoding_count += 1
                processed_columns.update(hist_columns)
                # Store method for each column (keep first method if multiple)
                for col in hist_columns:
                    if col not in encoding_methods:
                        encoding_methods[col] = hist_method
    
    logger.info(f"📊 [ENCODING] Found {encoding_count} encoding operation(s) → Processed columns: {sorted(processed_columns)}")
    return processed_columns, encoding_methods


def apply_feature_engineering_method_wrapper(df, method, **kwargs):
    """Wrapper function to apply feature engineering method."""
    logger.debug(f"🔍 [FEATURE ENGINEERING WRAPPER] Applying method: {method}")
    from backend.modules.data_preprocessing.feature_engineering.processor import apply_feature_engineering_method as fe_apply
    return fe_apply(df, method, **kwargs)


def get_processed_feature_engineering_columns():
    """Helper function to get all columns affected by feature engineering operations."""
    processed_columns = set()
    dropped_columns = set()
    created_columns = set()
    
    # Check ALL preprocessing history for feature engineering operations
    all_history = st.session_state.preprocessing_history
    
    for hist in all_history:
        hist_type = hist.get('type', '')
        hist_step_key = hist.get('step_key', '')
        is_fe = (hist_type == 'feature_engineering' or hist_step_key == 'feature_engineering')
        
        if is_fe:
            method = hist.get('method', '')
            if method == 'drop_column':
                hist_columns = hist.get('columns', [])
                if not isinstance(hist_columns, list):
                    hist_columns = list(hist_columns)
                dropped_columns.update(hist_columns)
            elif method in ['create_numeric_feature', 'create_datetime_feature', 'create_categorical_combination']:
                new_column_name = hist.get('new_column_name', '')
                if new_column_name:
                    created_columns.add(new_column_name)
    
    processed_columns = dropped_columns | created_columns
    logger.debug(f"🔍 [FEATURE ENGINEERING] Dropped columns: {sorted(dropped_columns)}, Created columns: {sorted(created_columns)}")
    return processed_columns, dropped_columns, created_columns


def render_scaling_step(df):
    """Render scaling preprocessing step."""
    st.subheader(f"📏 {steps[4]['name']}")
    
    # CRITICAL: Use current preprocessed_data directly
    current_df = st.session_state.preprocessed_data.copy()
    
    # Recalculate numeric_cols from CURRENT dataframe
    current_numeric_cols = current_df.select_dtypes(include=[np.number]).columns.tolist()
    
    logger.debug(f"🔍 [SCALING STEP] render_scaling_step called")
    logger.debug(f"🔍 [SCALING STEP] current_df shape: {current_df.shape}")
    logger.debug(f"🔍 [SCALING STEP] current_numeric_cols: {current_numeric_cols}")
    
    # Scaling analysis section
    st.markdown("### 📊 Sayısal Sütun Analizi")
    
    # Check if any operations were applied
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
    if step_history:
        st.info("ℹ️ İşlemler uygulandıktan sonra sayısal sütun analizi güncellenmiştir.")
    
    # Analyze numeric columns
    try:
        numeric_analysis = analyze_numeric_columns(current_df)
        logger.debug(f"🔍 [SCALING STEP] Analysis complete: {numeric_analysis['total_numeric']} numeric columns")
    except Exception as e:
        logger.error(f"❌ [SCALING STEP] Error in analyze_numeric_columns: {e}", exc_info=True)
        st.error(f"❌ Sayısal sütun analizi sırasında hata oluştu: {str(e)}")
        return
    
    # Get processed scaling columns from history
    processed_columns_for_count = set()
    for hist in st.session_state.preprocessing_history:
        hist_type = hist.get('type', '')
        hist_step_key = hist.get('step_key', '')
        is_scaling = (hist_type == 'scaling' or hist_step_key == 'scaling')
        
        if is_scaling:
            hist_columns = hist.get('columns', [])
            # Convert to Python list if it's a protobuf object
            if not isinstance(hist_columns, list):
                hist_columns = list(hist_columns)
            if isinstance(hist_columns, list) and len(hist_columns) > 0:
                processed_columns_for_count.update(hist_columns)
    
    # Summary metrics - in purple cards
    total_numeric = len(current_numeric_cols)
    total_rows = len(current_df)
    scaled_count = len(processed_columns_for_count)
    unscaled_count = max(0, total_numeric - scaled_count)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Toplam Sayısal Sütun</div>
            <div style='font-size: 2em; font-weight: bold;'>{total_numeric}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Ölçeklenen Sütun</div>
            <div style='font-size: 2em; font-weight: bold;'>{scaled_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Ölçeklenmemiş Sütun</div>
            <div style='font-size: 2em; font-weight: bold;'>{unscaled_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Toplam Satır Sayısı</div>
            <div style='font-size: 2em; font-weight: bold;'>{total_rows:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Column-based detail table
    st.markdown("#### 📋 Sütun Bazlı Detay")
    scaling_detail_data = []
    
    # Get detailed statistics for outlier percentage and median
    scaling_stats = get_scaling_statistics(current_df)
    
    for col_info in numeric_analysis.get('numeric_columns', []):
        col_name = col_info.get('column_name', '')
        is_scaled = col_name in processed_columns_for_count
        scaling_status = '✅ Ölçeklendi' if is_scaled else '⏳ Bekliyor'
        
        # Get additional stats from get_scaling_statistics
        col_stats = scaling_stats.get(col_name, {})
        median_val = col_stats.get('median')
        outlier_pct = col_stats.get('outlier_percentage', 0)
        
        # Get CV and Range from col_info
        cv = col_info.get('coefficient_of_variation')
        range_val = col_info.get('range')
        
        scaling_detail_data.append({
            'Sütun': col_name,
            'Ortalama': f"{col_info.get('mean', 0):.2f}" if col_info.get('mean') is not None else 'N/A',
            'Medyan': f"{median_val:.2f}" if median_val is not None else 'N/A',
            'Std Sapma': f"{col_info.get('std', 0):.2f}" if col_info.get('std') is not None else 'N/A',
            'CV': f"{cv:.2f}" if cv is not None and not np.isinf(cv) else 'N/A',
            'Min': f"{col_info.get('min', 0):.2f}" if col_info.get('min') is not None else 'N/A',
            'Max': f"{col_info.get('max', 0):.2f}" if col_info.get('max') is not None else 'N/A',
            'Aralık': f"{range_val:.2f}" if range_val is not None else 'N/A',
            'Çarpıklık': f"{col_info.get('skewness', 0):.2f}" if col_info.get('skewness') is not None else 'N/A',
            'Aykırı %': f"{outlier_pct:.2f}%" if outlier_pct is not None else 'N/A',
            'Durum': scaling_status
        })
    
    if scaling_detail_data:
        scaling_df = pd.DataFrame(scaling_detail_data)
        st.dataframe(scaling_df, width='stretch', hide_index=True)
    else:
        st.success("✅ Veri setinde sayısal sütun bulunmuyor!")
    
    st.markdown("---")
    
    # LLM suggestions section
    if llm_enabled:
        step_key = 'scaling'
        suggestions_key = f'step_{current_step}_{step_key}'
        index_key = f'preprocessing_suggestion_index_{step_key}'
        
        # Initialize suggestion index for this step
        if index_key not in st.session_state:
            st.session_state[index_key] = 0
        
        with st.expander("🤖 LLM Önerileri", expanded=True):
            if not current_numeric_cols:
                st.info("ℹ️ Sayısal sütun bulunmadığı için LLM önerisi alınamaz.")
            elif suggestions_key not in st.session_state.preprocessing_suggestions:
                if st.button("💡 LLM Önerilerini Al", key=f"get_suggestions_{step_key}"):
                    with st.spinner("🤖 LLM önerileri oluşturuluyor..."):
                        # Recalculate data_summary from current_df
                        current_data_summary = get_data_summary(current_df)
                        
                        # Get scaling statistics to filter binary columns
                        scaling_stats = get_scaling_statistics(current_df)
                        
                        # Filter out binary columns (Min=0, Max=1)
                        non_binary_numeric_cols = []
                        binary_cols_filtered = []
                        for col in current_numeric_cols:
                            col_stats = scaling_stats.get(col, {})
                            min_val = col_stats.get('min')
                            max_val = col_stats.get('max')
                            # Binary sütun kontrolü: Min=0 ve Max=1 ise atla
                            if isinstance(min_val, (int, float)) and isinstance(max_val, (int, float)):
                                if min_val == 0 and max_val == 1:
                                    binary_cols_filtered.append(col)
                                    continue  # Binary sütun, LLM'e gönderme
                            non_binary_numeric_cols.append(col)
                        
                        # Show info if binary columns were filtered
                        if binary_cols_filtered:
                            st.info(f"ℹ️ {len(binary_cols_filtered)} binary sütun (Min=0, Max=1) LLM önerilerinden çıkarıldı: {', '.join(binary_cols_filtered[:5])}{'...' if len(binary_cols_filtered) > 5 else ''}")
                        
                        # Update data_summary with scaling statistics for detailed metrics
                        if 'scaling_statistics' not in current_data_summary:
                            current_data_summary['scaling_statistics'] = {}
                        current_data_summary['scaling_statistics'] = scaling_stats
                        
                        suggestions_result = suggest_scaling_steps(
                            data_summary=current_data_summary,
                            numeric_columns=non_binary_numeric_cols,  # Filtrelenmiş: binary sütunlar hariç
                            categorical_columns=[],
                            analysis_level=analysis_level
                        )
                        
                        if suggestions_result.get('error'):
                            st.error(f"❌ LLM önerisi alınamadı: {suggestions_result.get('error')}")
                        else:
                            suggestions = suggestions_result.get('suggestions', [])
                            # Filter suggestions for scaling step and exclude binary columns
                            filtered_suggestions = [
                                s for s in suggestions 
                                if s.get('preprocessing_type') == step_key
                                and all(col in non_binary_numeric_cols for col in s.get('columns', []))
                            ]
                            
                            st.session_state.preprocessing_suggestions[suggestions_key] = filtered_suggestions
                            st.session_state[index_key] = 0
                            if filtered_suggestions:
                                st.success(f"✅ {len(filtered_suggestions)} öneri alındı")
                            st.rerun()
            else:
                # Refresh button
                if st.button("🔄 Yeni Öneriler Al", key=f"refresh_suggestions_{step_key}"):
                    del st.session_state.preprocessing_suggestions[suggestions_key]
                    st.session_state[index_key] = 0
                    st.rerun()
            
            # Display suggestions in carousel format
            if suggestions_key in st.session_state.preprocessing_suggestions:
                suggestions = st.session_state.preprocessing_suggestions[suggestions_key]
                if suggestions:
                    current_index = st.session_state[index_key]
                    
                    st.markdown(f"<div style='text-align: center; margin: 10px 0;'><strong>{len(suggestions)} öneri sunuldu</strong> | <em>Öneri {current_index + 1}/{len(suggestions)}</em></div>", unsafe_allow_html=True)
                    
                    # Navigation buttons and current suggestion
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        if st.button("◀️ Önceki", key=f"prev_suggestion_{step_key}", disabled=(current_index == 0), width='stretch'):
                            st.session_state[index_key] = max(0, current_index - 1)
                            st.rerun()
                    
                    with col2:
                        # Current suggestion - kart tasarımı
                        suggestion = suggestions[current_index]
                        method = suggestion.get('method', 'Bilinmeyen')
                        columns = suggestion.get('columns', [])
                        reason = suggestion.get('reason', '')
                        priority = suggestion.get('priority', 'orta')
                        analysis_level_sugg = suggestion.get('analysis_level', 'Temel')
                        
                        # HTML tag'lerini temizle
                        import html as html_module
                        import re
                        if reason:
                            try:
                                reason = html_module.unescape(reason)
                            except:
                                pass
                            reason = re.sub(r'<[^>]+>', '', reason, flags=re.DOTALL | re.IGNORECASE)
                            reason = ' '.join(reason.split()).strip()
                        
                        # Priority ve level renkleri
                        priority_colors = {'yüksek': '#f44336', 'orta': '#ff9800', 'düşük': '#4caf50'}
                        level_colors = {'Temel': '#4CAF50', 'Orta': '#FF9800', 'Gelişmiş': '#F44336'}
                        priority_color = priority_colors.get(priority, '#ff9800')
                        level_color = level_colors.get(analysis_level_sugg, '#4CAF50')
                        
                        # Güvenli HTML
                        method_safe = html_module.escape(str(method))
                        reason_safe = html_module.escape(reason) if reason else 'Açıklama bulunamadı.'
                        priority_safe = html_module.escape(priority)
                        level_safe = html_module.escape(analysis_level_sugg)
                        columns_display = ', '.join(columns) if columns else 'Tüm sütunlar'
                        columns_safe = html_module.escape(columns_display)
                        
                        # Kart tasarımı
                        card_html = f"""
                        <div style='
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 25px;
                            border-radius: 15px;
                            margin: 10px 0;
                            color: white;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            min-height: 180px;
                            border-left: 5px solid #f0f0f0;
                        '>
                            <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;'>
                                <h3 style='color: white; margin: 0; margin-right: 10px; font-size: 1.3em;'>
                                    🎯 {method_safe}
                                </h3>
                                <div style='display: flex; gap: 10px;'>
                                    <span style='
                                        background: {priority_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                    '>
                                        Öncelik: {priority_safe}
                                    </span>
                                    <span style='
                                        background: {level_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                        text-transform: uppercase;
                                    '>
                                        {level_safe}
                                    </span>
                                </div>
                            </div>
                            <div style='
                                background: rgba(255, 255, 255, 0.15);
                                padding: 10px 15px;
                                border-radius: 8px;
                                margin-bottom: 15px;
                                display: inline-block;
                            '>
                                <span style='color: #f0f0f0; font-size: 0.95em;'>
                                    <strong>📍 Sütunlar:</strong> {columns_safe}
                                </span>
                            </div>
                            <p style='
                                color: white; 
                                margin: 15px 0 0 0; 
                                line-height: 1.7; 
                                font-size: 1em;
                                padding: 10px;
                                background: rgba(255, 255, 255, 0.1);
                                border-radius: 8px;
                            '>
                                {reason_safe}
                            </p>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Uygula butonu
                        method = suggestion.get('method', '')
                        columns = suggestion.get('columns', [])
                        
                        # Check if already applied
                        is_applied = False
                        for col in columns:
                            for history_item in st.session_state.preprocessing_history:
                                if (history_item.get('step') == current_step and 
                                    history_item.get('type') == step_key and
                                    history_item.get('method') == method and
                                    col in history_item.get('columns', [])):
                                    is_applied = True
                                    break
                            if is_applied:
                                break
                        
                        if is_applied:
                            st.button("✅ Zaten Uygulandı", key=f"apply_suggestion_{step_key}_{current_index}", width='stretch', disabled=True)
                        else:
                            if st.button("✅ Uygula", key=f"apply_suggestion_{step_key}_{current_index}", width='stretch', type="primary"):
                                apply_preprocessing_suggestion(current_df, suggestion, step_key)
                    
                    with col3:
                        if st.button("Sonraki ▶️", key=f"next_suggestion_{step_key}", disabled=(current_index == len(suggestions) - 1), width='stretch'):
                            st.session_state[index_key] = min(len(suggestions) - 1, current_index + 1)
                            st.rerun()
                    
                    # Dots indicator
                    dots_html = "<div style='text-align: center; margin-top: 15px;'>"
                    for i in range(len(suggestions)):
                        if i == current_index:
                            dots_html += "🔵 "
                        else:
                            dots_html += "⚪ "
                    dots_html += "</div>"
                    st.markdown(dots_html, unsafe_allow_html=True)
                else:
                    st.info("ℹ️ Henüz öneri bulunmuyor.")
    
    st.markdown("---")
    
    # Manual operations section
    st.markdown("### 🔧 Manuel İşlemler")
    
    # Create a styled container for manual operations
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    '>
    """, unsafe_allow_html=True)
    
    # Sütun Seçimi
    st.markdown("#### 📌 Sütun Seçimi")
    
    # Get already processed columns from step history
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
    processed_columns = set()
    for hist in step_history:
        hist_columns = hist.get('columns', [])
        if isinstance(hist_columns, list):
            processed_columns.update(hist_columns)
    
    # Filter out already processed columns from selection options
    available_columns = [col for col in current_numeric_cols if col not in processed_columns]
    
    if available_columns:
        selected_columns = st.multiselect(
            "Ölçeklemek istediğiniz sütunları seçin",
            options=available_columns,
            help=f"Ölçeklenebilir {len(available_columns)} sütun gösteriliyor (Daha önce işlenen {len(processed_columns)} sütun gizlendi)",
            label_visibility="collapsed"
        )
        
        if selected_columns:
            st.info(f"✅ {len(selected_columns)} sayısal sütun seçildi")
        else:
            st.info("ℹ️ Lütfen ölçeklemek istediğiniz sütunları seçin")
    else:
        if current_numeric_cols:
            st.success(f"✅ Tüm sayısal sütunlar ölçeklendi! ({len(processed_columns)} sütun)")
        else:
            st.success("✅ Veri setinde sayısal sütun bulunmuyor!")
        selected_columns = []
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Yöntem Seçimi
    st.markdown("#### ⚙️ Yöntem Seçimi")
    
    all_columns_processed = len(current_numeric_cols) > 0 and len(available_columns) == 0
    
    if selected_columns:
        method = st.selectbox(
            "Scaling Yöntemi",
            options=['standard_scaler', 'minmax_scaler', 'robust_scaler', 'normalizer', 'power_transform'],
            key="scaling_method",
            help="Sayısal sütunları ölçeklemek için yöntem seçin",
            label_visibility="collapsed"
        )
        
        # Method info card
        method_info = {
            'standard_scaler': {
                'name': 'Standard Scaler',
                'description': '<strong>Nasıl Çalışır:</strong> Ortalama=0, Standart sapma=1 olacak şekilde ölçekler. Formül: (x - mean) / std<br><br><strong>✓ Avantajları:</strong> Çoğu ML algoritması için uygun, normal dağılımlı veriler için ideal<br><strong>✗ Dezavantajları:</strong> Aykırı değerlerden etkilenir<br><strong>📌 Kullanım:</strong> Normal dağılıma yakın veriler için'
            },
            'minmax_scaler': {
                'name': 'Min-Max Scaler',
                'description': '<strong>Nasıl Çalışır:</strong> Verileri 0-1 aralığına ölçekler. Formül: (x - min) / (max - min)<br><br><strong>✓ Avantajları:</strong> Sinir ağları için ideal, sınırlı aralık<br><strong>✗ Dezavantajları:</strong> Aykırı değerlerden etkilenir<br><strong>📌 Kullanım:</strong> Sinir ağları ve 0-1 aralığı gerektiren algoritmalar için'
            },
            'robust_scaler': {
                'name': 'Robust Scaler',
                'description': '<strong>Nasıl Çalışır:</strong> Median ve IQR kullanarak ölçekler. Formül: (x - median) / IQR<br><br><strong>✓ Avantajları:</strong> Aykırı değerlere dayanıklı<br><strong>✗ Dezavantajları:</strong> Normal dağılımdan uzaklaşabilir<br><strong>📌 Kullanım:</strong> Aykırı değer içeren veriler için'
            },
            'normalizer': {
                'name': 'Normalizer',
                'description': '<strong>Nasıl Çalışır:</strong> Her satırı (örnek) birim normuna ölçekler (l2 norm)<br><br><strong>✓ Avantajları:</strong> Satır bazlı normalizasyon, metin sınıflandırma için uygun<br><strong>✗ Dezavantajları:</strong> Sütun bazlı değil, satır bazlı<br><strong>📌 Kullanım:</strong> Metin sınıflandırma, kümeleme için'
            },
            'power_transform': {
                'name': 'Power Transform',
                'description': '<strong>Nasıl Çalışır:</strong> Veriyi normal dağılıma yaklaştırır (Yeo-Johnson veya Box-Cox)<br><br><strong>✓ Avantajları:</strong> Çarpık verileri düzeltir, normal dağılıma yaklaştırır<br><strong>✗ Dezavantajları:</strong> Daha yavaş, parametre ayarı gerekir<br><strong>📌 Kullanım:</strong> Çarpık veriler için'
            }
        }
        
        method_info_text = method_info.get(method, {'name': method, 'description': 'İşlem bilgisi bulunamadı'})
        
        # Show method info card
        card_id = f"method_card_{method}"
        col_left, col_center, col_right = st.columns([1, 3, 1])
        with col_center:
            st.markdown(f"""
            <div id="{card_id}" style="width: 100%; height: 180px; perspective: 1000px; margin: 10px 0;">
                <div class="method-card-inner" style="position: relative; width: 100%; height: 100%; text-align: center; transition: transform 0.6s; transform-style: preserve-3d;">
                    <div class="method-card-front" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 10px; display: flex; align-items: center; justify-content: center; padding: 15px 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                        <div style="text-align: center; width: 100%;">
                            <div style="font-size: 1.5em; font-weight: bold; margin-bottom: 5px;">📊 Bilgi Kartı</div>
                            <div style="font-size: 1.4em;">{method_info_text['name']}</div>
                        </div>
                    </div>
                    <div class="method-card-back" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 10px; display: flex; align-items: center; justify-content: center; padding: 15px 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); background: linear-gradient(135deg, #764ba2 0%, #667eea 100%); color: white; transform: rotateY(180deg); font-size: 0.9em; line-height: 1.5; text-align: center; overflow-y: auto;">
                        <div style="width: 100%;">
                            <div style="font-weight: bold; margin-bottom: 8px; font-size: 1.1em;">{method_info_text['name']}</div>
                            <div style="padding: 0 10px; font-size: 0.9em; line-height: 1.5;">{method_info_text['description']}</div>
                        </div>
                    </div>
                </div>
            </div>
            <style>
                #{card_id}:hover .method-card-inner {{
                    transform: rotateY(180deg);
                }}
            </style>
            """, unsafe_allow_html=True)
    else:
        method = None
        if all_columns_processed:
            st.info("ℹ️ Bütün sayısal sütunlar ölçeklenmiştir. Sonraki adıma geçebilirsiniz.")
        else:
            st.info("ℹ️ Önce sütun seçin")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Action buttons - Uygula butonu
    if selected_columns and method:
        if st.button("✅ Uygula", key="apply_scaling", type="primary", use_container_width=True):
            try:
                df_processed = current_df.copy()
                df_processed = apply_scaling_method_wrapper(df_processed, selected_columns, method)
                
                # Save to session state
                st.session_state.preprocessed_data = df_processed
                
                # Add to history
                st.session_state.preprocessing_history.append({
                    'step': current_step,
                    'step_key': 'scaling',
                    'type': 'scaling',
                    'method': method,
                    'columns': selected_columns,
                    'timestamp': datetime.now().isoformat(),
                    'before_data': current_df.copy()
                })
                
                st.success(f"✅ İşlem başarıyla uygulandı! {len(selected_columns)} sütun ölçeklendi: {', '.join(selected_columns)}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Hata oluştu: {str(e)}")
                logger.error(f"Error applying scaling method: {e}", exc_info=True)
    elif not method:
        pass
    
    # Show applied operations for this step with undo functionality
    st.markdown("### 📋 Uygulanan İşlemler")
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
    if step_history:
        for i, operation in enumerate(step_history):
            col1, col2 = st.columns([4, 1])
            with col1:
                method_op = operation.get('method', 'Bilinmeyen')
                columns_op = operation.get('columns', [])
                display_text = f"{', '.join(columns_op)} sütunları - {method_op} ile ölçeklendi" if columns_op else f"Tüm sütunlar - {method_op} ile ölçeklendi"
                
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 5px 0;
                    color: white;
                '>
                    <span style='font-size: 1.2em; margin-right: 10px;'>✅</span>
                    {display_text}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("↶ Geri Al", key=f"undo_scaling_{i}", width='stretch'):
                    # Remove from history
                    operation_to_remove = step_history[i]
                    
                    # Remove from preprocessing_history
                    st.session_state.preprocessing_history.remove(operation_to_remove)
                    
                    # Rebuild the dataframe by reapplying ALL operations in order
                    original_log_level = logger.level
                    logger.setLevel(logging.WARNING)
                    try:
                        df_rebuilt = st.session_state.original_data.copy()
                        
                        # Apply all operations in correct order
                        for op in st.session_state.preprocessing_history:
                            op_type = op.get('type', '')
                            
                            if op_type == 'feature_engineering':
                                op_method = op.get('method', '')
                                if op_method == 'remove_duplicates':
                                    df_rebuilt = remove_duplicate_rows(df_rebuilt, keep=op.get('keep', 'first'))
                                elif op_method == 'drop_column':
                                    df_rebuilt = drop_columns(df_rebuilt, op.get('columns', []))
                                elif op_method == 'create_numeric_feature':
                                    df_rebuilt = create_numeric_feature(
                                        df_rebuilt,
                                        op.get('operation', 'add'),
                                        op.get('columns', []),
                                        op.get('new_column_name', '')
                                    )
                                elif op_method == 'create_datetime_feature':
                                    df_rebuilt = create_datetime_feature(
                                        df_rebuilt,
                                        op.get('columns', [])[0] if op.get('columns') else '',
                                        op.get('feature_type', 'year'),
                                        op.get('new_column_name', '')
                                    )
                                elif op_method == 'create_categorical_combination':
                                    df_rebuilt = create_categorical_combination(
                                        df_rebuilt,
                                        op.get('columns', []),
                                        op.get('new_column_name', ''),
                                        op.get('separator', '_')
                                    )
                            elif op_type == 'missing_values':
                                op_method_dict = op.get('method_dict')
                                if op_method_dict:
                                    if op_method_dict.get('numeric') and op_method_dict.get('numeric_cols'):
                                        df_rebuilt = apply_missing_values_method(
                                            df_rebuilt, 
                                            op_method_dict['numeric_cols'], 
                                            op_method_dict['numeric']
                                        )
                                    if op_method_dict.get('categorical') and op_method_dict.get('categorical_cols'):
                                        df_rebuilt = apply_missing_values_method(
                                            df_rebuilt, 
                                            op_method_dict['categorical_cols'], 
                                            op_method_dict['categorical']
                                        )
                                else:
                                    df_rebuilt = apply_missing_values_method(
                                        df_rebuilt, 
                                        op.get('columns', []), 
                                        op.get('method', '')
                                    )
                            elif op_type == 'outlier':
                                outlier_method = op.get('method', '')
                                method_parts = outlier_method.split('_')
                                if len(method_parts) >= 2:
                                    detection_method = '_'.join(method_parts[:-1])
                                    action = method_parts[-1]
                                    df_rebuilt = apply_outlier_method_wrapper(
                                        df_rebuilt,
                                        op.get('columns', []),
                                        detection_method,
                                        action
                                    )
                            elif op_type == 'encoding':
                                df_rebuilt = apply_encoding_method(
                                    df_rebuilt,
                                    op.get('columns', []),
                                    op.get('method', '')
                                )
                            elif op_type == 'scaling':
                                df_rebuilt = apply_scaling_method_wrapper(
                                    df_rebuilt,
                                    op.get('columns', []),
                                    op.get('method', '')
                                )
                    finally:
                        logger.setLevel(original_log_level)
                    
                    st.session_state.preprocessed_data = df_rebuilt
                    
                    # Remove from applied_suggestion_ids if it was from LLM
                    if operation_to_remove.get('from_llm'):
                        remove_method = operation_to_remove.get('method', '')
                        remove_columns = operation_to_remove.get('columns', [])
                        # Use 'scaling' as step_key since we're in scaling step
                        step_key_undo = 'scaling'
                        suggestion_id = f"{step_key_undo}_{remove_method}_{'_'.join(remove_columns) if remove_columns else 'all'}"
                        if suggestion_id in st.session_state.applied_suggestion_ids:
                            st.session_state.applied_suggestion_ids.remove(suggestion_id)
                    
                    st.success("✅ İşlem geri alındı!")
                    st.rerun()
    else:
        st.info("ℹ️ Henüz bu adımda işlem uygulanmadı.")
    
    # Add spacing before navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Action buttons - right aligned at bottom
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([3, 1, 1, 1])
    with col_nav2:
        if current_step > 1:
            if st.button("← Geri", key="prev_step_scaling", width='stretch'):
                st.session_state.preprocessing_step -= 1
                st.rerun()
    with col_nav3:
        if current_step < len(steps):
            if st.button("Atla", key="skip_step_scaling", width='stretch'):
                st.session_state.preprocessing_step += 1
                st.rerun()
    with col_nav4:
        has_operation = check_step_has_operation(current_step)
        if st.button("İleri →", key="next_step_scaling", disabled=not has_operation, width='stretch'):
            st.session_state.preprocessing_step += 1
            st.rerun()


def render_encoding_step(df):
    """Render encoding preprocessing step."""
    st.subheader(f"🔤 {steps[3]['name']}")
    
    # CRITICAL: Use current preprocessed_data directly (like outlier step does)
    # Don't rely on df parameter - get fresh copy from session state
    current_df = st.session_state.preprocessed_data.copy()
    
    # Get categorical columns from CURRENT dataframe ONLY (object and category types)
    # IMPORTANT: We only work with columns that exist in current_df
    current_categorical_cols = current_df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    logger.debug(f"🔍 [ENCODING STEP] render_encoding_step called")
    logger.debug(f"🔍 [ENCODING STEP] current_df shape: {current_df.shape}")
    logger.debug(f"🔍 [ENCODING STEP] current_df columns: {list(current_df.columns)}")
    logger.debug(f"🔍 [ENCODING STEP] current_categorical_cols: {current_categorical_cols}")
    
    # Get processed encoding columns ONCE at the beginning (reusable everywhere)
    processed_columns, encoding_methods = get_processed_encoding_columns()
    
    logger.debug(f"🔍 [ENCODING STEP] Processed columns: {processed_columns}")
    logger.debug(f"🔍 [ENCODING STEP] Encoding methods: {encoding_methods}")
    
    # Encoding analysis section
    st.markdown("### 📊 Kategorik Sütun Analizi")
    
    # Check if any operations were applied
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
    if step_history:
        st.info("ℹ️ İşlemler uygulandıktan sonra kategorik sütun analizi güncellenmiştir.")
    
    # Analyze categorical columns from current dataframe
    try:
        categorical_analysis = analyze_categorical_columns(current_df)
        logger.debug(f"🔍 [ENCODING STEP] Analysis complete: {categorical_analysis['total_categorical']} categorical columns")
    except Exception as e:
        logger.error(f"❌ [ENCODING STEP] Error in analyze_categorical_columns: {e}", exc_info=True)
        st.error(f"❌ Kategorik sütun analizi sırasında hata oluştu: {str(e)}")
        return
    
    # Summary metrics - in purple cards
    # Calculate processed columns directly from preprocessing_history (like manual operations)
    processed_columns_for_count = set()
    for hist in st.session_state.preprocessing_history:
        hist_type = hist.get('type', '')
        hist_step_key = hist.get('step_key', '')
        is_encoding = (hist_type == 'encoding' or hist_step_key == 'encoding')
        
        if is_encoding:
            hist_columns = hist.get('columns', [])
            # Convert to Python list if it's a protobuf object
            if not isinstance(hist_columns, list):
                hist_columns = list(hist_columns)
            if isinstance(hist_columns, list) and len(hist_columns) > 0:
                processed_columns_for_count.update(hist_columns)
    
    logger.info(f"📊 [CARDS] Encoded columns count: {len(processed_columns_for_count)} → {sorted(processed_columns_for_count)}")
    
    # Get categorical columns from CURRENT dataframe (before encoding step)
    # This is the dataframe that came from previous steps (feature_engineering, missing values, outlier, etc.)
    # We need to rebuild the state BEFORE encoding to get accurate count
    # Temporarily suppress INFO logs during rebuild to avoid noise
    original_log_level = logger.level
    logger.setLevel(logging.WARNING)
    try:
        df_before_encoding = st.session_state.original_data.copy()
        # Apply all operations EXCEPT encoding to get the state before encoding step
        for hist in st.session_state.preprocessing_history:
            hist_type = hist.get('type', '')
            hist_step_key = hist.get('step_key', '')
            # Skip encoding operations - we want state BEFORE encoding
            if hist_type == 'encoding' or hist_step_key == 'encoding':
                continue
            
            # Apply feature_engineering operations
            if hist_type == 'feature_engineering':
                op_method = hist.get('method', '')
                if op_method == 'remove_duplicates':
                    df_before_encoding = remove_duplicate_rows(df_before_encoding, keep=hist.get('keep', 'first'))
                elif op_method == 'drop_column':
                    df_before_encoding = drop_columns(df_before_encoding, hist.get('columns', []))
                elif op_method == 'create_numeric_feature':
                    df_before_encoding = create_numeric_feature(
                        df_before_encoding,
                        hist.get('operation', 'add'),
                        hist.get('columns', []),
                        hist.get('new_column_name', '')
                    )
                elif op_method == 'create_datetime_feature':
                    df_before_encoding = create_datetime_feature(
                        df_before_encoding,
                        hist.get('columns', [])[0] if hist.get('columns') else '',
                        hist.get('feature_type', 'year'),
                        hist.get('new_column_name', '')
                    )
                elif op_method == 'create_categorical_combination':
                    df_before_encoding = create_categorical_combination(
                        df_before_encoding,
                        hist.get('columns', []),
                        hist.get('new_column_name', ''),
                        hist.get('separator', '_')
                    )
            # Apply missing_values operations
            elif hist_type == 'missing_values':
                op_method_dict = hist.get('method_dict')
                if op_method_dict:
                    # Handle dict method (numeric and categorical separately)
                    if op_method_dict.get('numeric') and op_method_dict.get('numeric_cols'):
                        df_before_encoding = apply_missing_values_method(
                            df_before_encoding, 
                            op_method_dict['numeric_cols'], 
                            op_method_dict['numeric']
                        )
                    if op_method_dict.get('categorical') and op_method_dict.get('categorical_cols'):
                        df_before_encoding = apply_missing_values_method(
                            df_before_encoding, 
                            op_method_dict['categorical_cols'], 
                            op_method_dict['categorical']
                        )
                else:
                    # Handle string method
                    df_before_encoding = apply_missing_values_method(
                        df_before_encoding,
                        hist.get('columns', []),
                        hist.get('method', '')
                    )
            # Apply outlier operations
            elif hist_type == 'outlier':
                outlier_method = hist.get('method', '')
                method_parts = outlier_method.split('_')
                if len(method_parts) >= 2:
                    detection_method = '_'.join(method_parts[:-1])
                    action = method_parts[-1]
                    df_before_encoding = apply_outlier_method_wrapper(
                        df_before_encoding,
                        hist.get('columns', []),
                        detection_method,
                        action
                    )
    finally:
        # Restore original log level
        logger.setLevel(original_log_level)
    
    # Get categorical columns from dataframe BEFORE encoding step
    categorical_cols_before_encoding = df_before_encoding.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Total categorical = categorical columns in dataframe BEFORE encoding step
    total_categorical = len(categorical_cols_before_encoding)
    total_rows = len(current_df)
    
    # Count: encoded = all processed columns (even if removed), unencoded = total - encoded
    encoded_count = len(processed_columns_for_count)
    unencoded_count = max(0, total_categorical - encoded_count)  # Ensure non-negative
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Toplam Kategorik Sütun</div>
            <div style='font-size: 2em; font-weight: bold;'>{total_categorical}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Encoding Yapılmamış</div>
            <div style='font-size: 2em; font-weight: bold;'>{unencoded_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Encoding Yapılmış</div>
            <div style='font-size: 2em; font-weight: bold;'>{encoded_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Toplam Sütun Sayısı</div>
            <div style='font-size: 2em; font-weight: bold;'>{len(current_df.columns)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Categorical columns table
    st.markdown("#### 📋 Kategorik Sütun Detayları")
    
    # Use processed_columns and encoding_methods already calculated at the beginning
    # No need to recalculate - already available from get_processed_encoding_columns()
    
    logger.debug(f"🔍 [ENCODING TABLE] Processed columns: {processed_columns}")
    logger.debug(f"🔍 [ENCODING TABLE] Encoding methods: {encoding_methods}")
    
    # Create table data - include both current categorical columns AND encoded columns that were removed
    # This ensures encoded columns (even if removed) are shown with "Yapıldı" status
    # Use categorical_cols_before_encoding instead of current_categorical_cols to include columns that were removed by encoding
    all_columns_to_show = set(categorical_cols_before_encoding) | processed_columns
    
    # Get original data for columns that were removed (only for display purposes)
    original_df = st.session_state.original_data if 'original_data' in st.session_state else current_df
    
    table_data = []
    for col_name in all_columns_to_show:
        # Check if column exists in current dataframe
        if col_name in current_df.columns:
            # Column exists in current dataframe - get current info
            if col_name in current_categorical_cols:
                # Still categorical - get from analysis
                col_info = next((c for c in categorical_analysis['categorical_columns'] if c['column_name'] == col_name), None)
                if col_info:
                    unique_count = col_info['unique_count']
                    cardinality = col_info['cardinality']
                    data_type = col_info['data_type']
                else:
                    unique_count = current_df[col_name].nunique()
                    cardinality = 'Yüksek' if unique_count > 10 else 'Düşük'
                    data_type = str(current_df[col_name].dtype)
            else:
                # Column was encoded but still exists (e.g., frequency encoding keeps original)
                # Get info from current_df
                unique_count = current_df[col_name].nunique()
                cardinality = 'Yüksek' if unique_count > 10 else 'Düşük'
                data_type = str(current_df[col_name].dtype)
        else:
            # Column was removed (e.g., one-hot, binary encoding removed original)
            # Get original info for display (only for showing encoding status)
            if col_name in original_df.columns:
                unique_count = original_df[col_name].nunique()
                cardinality = 'Yüksek' if unique_count > 10 else 'Düşük'
                data_type = str(original_df[col_name].dtype)
            else:
                # Fallback if column not in original either
                unique_count = 0
                cardinality = 'Bilinmiyor'
                data_type = 'object'
        
        # Check encoding status - directly from preprocessing_history (like manual operations)
        encoding_status = 'Yapılmadı'
        
        for hist in st.session_state.preprocessing_history:
            hist_type = hist.get('type', '')
            hist_step_key = hist.get('step_key', '')
            is_encoding = (hist_type == 'encoding' or hist_step_key == 'encoding')
            
            if is_encoding:
                hist_columns = hist.get('columns', [])
                # Convert to Python list if it's a protobuf object
                if not isinstance(hist_columns, list):
                    hist_columns = list(hist_columns)
                if isinstance(hist_columns, list) and col_name in hist_columns:
                    encoding_status = 'Yapıldı'
                    break
        
        logger.info(f"📋 [TABLE] {col_name}: {encoding_status}")
        
        table_data.append({
            'Sütun Adı': col_name,
            'Veri Türü': data_type,
            'Unique Değer Sayısı': unique_count,
            'Cardinality': cardinality,
            'Encoding Durumu': encoding_status
        })
    
    if table_data:
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, width='stretch', hide_index=True)
    else:
        st.success("✅ Veri setinde kategorik sütun bulunmuyor!")
    
    st.markdown("---")
    
    # DataFrame Önizleme
    st.markdown("#### 📊 Veri Önizlemesi")
    st.caption("Encoding işlemlerinden sonra veri setinin güncel durumu")
    
    # Show preview of current dataframe
    preview_rows = min(10, len(current_df))
    st.dataframe(
        current_df.head(preview_rows),
        width='stretch',
        hide_index=False
    )
    st.caption(f"Gösterilen: İlk {preview_rows} satır (Toplam: {len(current_df):,} satır, {len(current_df.columns)} sütun)")
    
    # Show column info
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"📊 **Toplam Sütun:** {len(current_df.columns)} | **Toplam Satır:** {len(current_df):,}")
    with col2:
        # Show encoding status summary
        # Use processed_columns already calculated at the beginning
        if processed_columns:
            st.success(f"✅ **Encoding Yapıldı:** {len(processed_columns)} sütun encode edildi")
        else:
            st.info("ℹ️ Henüz encoding yapılmadı")
    
    st.markdown("---")
    
    # LLM suggestions - EXACTLY like missing_values and outlier steps (moved here, after analysis, before manual operations)
    if llm_enabled:
        step_key = 'encoding'
        suggestions_key = f'step_{current_step}_{step_key}'
        index_key = f'preprocessing_suggestion_index_{step_key}'
        
        # Initialize suggestion index for this step
        if index_key not in st.session_state:
            st.session_state[index_key] = 0
        
        with st.expander("🤖 LLM Önerileri", expanded=True):
            # Button to get suggestions
            if suggestions_key not in st.session_state.preprocessing_suggestions:
                if st.button("💡 LLM Önerilerini Al", key=f"get_suggestions_{step_key}"):
                    with st.spinner("🤖 LLM önerileri oluşturuluyor..."):
                        # Get categorical columns info for prompt
                        categorical_analysis_step = analyze_categorical_columns(current_df)
                        categorical_cols_step = [col['column_name'] for col in categorical_analysis_step.get('categorical_columns', [])]
                        
                        # Update data_summary with categorical columns info
                        data_summary_with_encoding = data_summary.copy()
                        
                        # IMPORTANT: categorical_columns might be an integer (count) in data_summary
                        # We need to convert it to a dictionary structure for prompts
                        # Save the original count if it exists
                        categorical_columns_count = data_summary_with_encoding.get('categorical_columns', 0)
                        if isinstance(categorical_columns_count, int):
                            # If it's an integer, create a new dictionary structure
                            data_summary_with_encoding['categorical_columns'] = {}
                            # Optionally save the count in a separate key
                            data_summary_with_encoding['categorical_columns_count'] = categorical_columns_count
                        elif not isinstance(data_summary_with_encoding.get('categorical_columns'), dict):
                            # If it's not a dict, initialize it
                            data_summary_with_encoding['categorical_columns'] = {}
                        
                        # Add categorical statistics
                        categorical_stats = get_categorical_statistics(current_df)
                        for col in categorical_cols_step:
                            if col in categorical_stats:
                                data_summary_with_encoding['categorical_columns'][col] = {
                                    'unique_count': categorical_stats[col]['unique_count'],
                                    'cardinality': 'Yüksek' if categorical_stats[col]['unique_count'] > 10 else 'Düşük'
                                }
                        
                        if step_key == 'encoding':
                            suggestions_result = suggest_encoding_steps(
                                data_summary_with_encoding,
                                numeric_cols,
                                categorical_cols_step,
                                analysis_level
                            )
                        else:
                            suggestions_result = {"suggestions": []}
                        
                        if suggestions_result.get('error'):
                            st.error(f"❌ LLM önerisi alınamadı: {suggestions_result.get('error')}")
                        else:
                            suggestions = suggestions_result.get('suggestions', [])
                            # Filter suggestions for this step type
                            filtered_suggestions = [s for s in suggestions if s.get('preprocessing_type') == step_key]
                            
                            # Otomatik öncelik hesaplaması (LLM'in verdiği önceliği override et)
                            if step_key == 'encoding':
                                for suggestion in filtered_suggestions:
                                    # Önceliği kategorik sütun sayısına göre belirle
                                    total_categorical = len(categorical_cols_step)
                                    if total_categorical > 5:
                                        suggestion['priority'] = 'yüksek'
                                    elif total_categorical >= 2:
                                        suggestion['priority'] = 'orta'
                                    else:
                                        suggestion['priority'] = 'düşük'
                            
                            st.session_state.preprocessing_suggestions[suggestions_key] = filtered_suggestions
                            st.session_state[index_key] = 0  # Reset index
                            if filtered_suggestions:
                                st.success(f"✅ {len(filtered_suggestions)} öneri alındı")
                            st.rerun()
            else:
                # Yeniden öneri al butonu (öneriler varsa)
                if st.button("🔄 Yeni Öneriler Al", key=f"refresh_suggestions_{step_key}"):
                    # Önerileri temizle ve yeniden al
                    del st.session_state.preprocessing_suggestions[suggestions_key]
                    st.session_state[index_key] = 0
                    st.rerun()
            
            # Display suggestions in carousel format - EXACTLY like missing_values and outlier
            if suggestions_key in st.session_state.preprocessing_suggestions:
                suggestions = st.session_state.preprocessing_suggestions[suggestions_key]
                if suggestions:
                    current_index = st.session_state[index_key]
                    
                    st.markdown(f"<div style='text-align: center; margin: 10px 0;'><strong>{len(suggestions)} öneri sunuldu</strong> | <em>Öneri {current_index + 1}/{len(suggestions)}</em></div>", unsafe_allow_html=True)
                    
                    # Navigation buttons and current suggestion
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        if st.button("◀️ Önceki", key=f"prev_suggestion_{step_key}", disabled=(current_index == 0), width='stretch'):
                            st.session_state[index_key] = max(0, current_index - 1)
                            st.rerun()
                    
                    with col2:
                        # Current suggestion - kart tasarımı (EXACTLY like missing_values/outlier, sadece emoji değişir: 🔤)
                        suggestion = suggestions[current_index]
                        method = suggestion.get('method', 'Bilinmeyen')
                        columns = suggestion.get('columns', [])
                        reason = suggestion.get('reason', '')
                        priority = suggestion.get('priority', 'orta')
                        analysis_level_sugg = suggestion.get('analysis_level', 'Temel')
                        
                        # HTML tag'lerini temizle
                        import html as html_module
                        import re
                        if reason:
                            try:
                                reason = html_module.unescape(reason)
                            except:
                                pass
                            reason = re.sub(r'<[^>]+>', '', reason, flags=re.DOTALL | re.IGNORECASE)
                            reason = ' '.join(reason.split()).strip()
                        
                        # Priority ve level renkleri
                        priority_colors = {'yüksek': '#f44336', 'orta': '#ff9800', 'düşük': '#4caf50'}
                        level_colors = {'Temel': '#4CAF50', 'Orta': '#FF9800', 'Gelişmiş': '#F44336'}
                        priority_color = priority_colors.get(priority, '#ff9800')
                        level_color = level_colors.get(analysis_level_sugg, '#4CAF50')
                        
                        # Güvenli HTML
                        method_safe = html_module.escape(str(method))
                        reason_safe = html_module.escape(reason) if reason else 'Açıklama bulunamadı.'
                        priority_safe = html_module.escape(priority)
                        level_safe = html_module.escape(analysis_level_sugg)
                        columns_display = ', '.join(columns) if columns else 'Tüm sütunlar'
                        columns_safe = html_module.escape(columns_display)
                        
                        # Kart tasarımı (EXACTLY like missing_values/outlier, sadece emoji değişir: 🔤)
                        if columns:
                            card_html = f"""
                        <div style='
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 25px;
                            border-radius: 15px;
                            margin: 10px 0;
                            color: white;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            min-height: 180px;
                            border-left: 5px solid #f0f0f0;
                        '>
                            <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;'>
                                <h3 style='color: white; margin: 0; margin-right: 10px; font-size: 1.3em;'>
                                    🔤 {method_safe}
                                </h3>
                                <div style='display: flex; gap: 10px;'>
                                    <span style='
                                        background: {priority_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                    '>
                                        Öncelik: {priority_safe}
                                    </span>
                                    <span style='
                                        background: {level_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                        text-transform: uppercase;
                                    '>
                                        {level_safe}
                                    </span>
                                </div>
                            </div>
                            <div style='
                                background: rgba(255, 255, 255, 0.15);
                                padding: 10px 15px;
                                border-radius: 8px;
                                margin-bottom: 15px;
                                display: inline-block;
                            '>
                                <span style='color: #f0f0f0; font-size: 0.95em;'>
                                    <strong>📍 Sütunlar:</strong> {columns_safe}
                                </span>
                            </div>
                            <p style='
                                color: white; 
                                margin: 15px 0 0 0; 
                                line-height: 1.7; 
                                font-size: 1em;
                                padding: 10px;
                                background: rgba(255, 255, 255, 0.1);
                                border-radius: 8px;
                            '>
                                {reason_safe}
                            </p>
                        </div>
                        """
                            st.markdown(card_html, unsafe_allow_html=True)
                            
                            # Uygula butonu - Check if method+column combination already applied (EXACTLY like missing_values and outlier)
                            method = suggestion.get('method', '')
                            columns = suggestion.get('columns', [])
                            
                            # Check if this method+column combination is already applied
                            is_applied = False
                            is_manual_operation = False
                            button_text = "✅ Zaten Uygulandı"
                            
                            # First check by suggestion_id (this is the primary check for LLM suggestions)
                            suggestion_id = f"{step_key}_{method}_{'_'.join(columns) if columns else 'all'}"
                            is_applied = suggestion_id in st.session_state.applied_suggestion_ids
                            if is_applied:
                                button_text = "✅ Zaten Uygulandı"
                            
                            # If not found in applied_suggestion_ids, check history
                            if not is_applied and step_key == 'encoding' and columns:
                                # Get all processed columns from step history (step 4 = encoding)
                                step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
                                processed_columns = set()
                                for hist in step_history:
                                    hist_columns = hist.get('columns', [])
                                    if isinstance(hist_columns, list):
                                        processed_columns.update(hist_columns)
                                
                                # Check if any of the suggested columns are already processed (regardless of method)
                                already_processed_cols = [col for col in columns if col in processed_columns]
                                
                                if already_processed_cols:
                                    # Check if it was applied via LLM suggestion or manually
                                    # If the method in history matches the suggestion method AND from_llm is True, it's from LLM
                                    # Otherwise, it's manual
                                    is_llm_applied = False
                                    for col in already_processed_cols:
                                        for history_item in step_history:
                                            if (history_item.get('type') == step_key and
                                                history_item.get('method') == method and
                                                col in history_item.get('columns', []) and
                                                history_item.get('from_llm', False)):
                                                is_llm_applied = True
                                                break
                                        if is_llm_applied:
                                            break
                                    
                                    is_applied = True
                                    if not is_llm_applied:
                                        # Manual operation
                                        is_manual_operation = True
                                        button_text = f"ℹ️ Bu sütun üzerinde Manuel olarak işlem yapıldı: {', '.join(already_processed_cols)}"
                                    else:
                                        # LLM suggestion was applied (but not in applied_suggestion_ids - should not happen, but handle it)
                                        button_text = "✅ Zaten Uygulandı"
                                else:
                                    # Also check if this specific method+column combination is already applied
                                    for col in columns:
                                        # Check in preprocessing_history
                                        for history_item in st.session_state.preprocessing_history:
                                            if (history_item.get('step') == current_step and 
                                                history_item.get('type') == step_key and
                                                history_item.get('method') == method and
                                                col in history_item.get('columns', []) and
                                                history_item.get('from_llm', False)):
                                                is_applied = True
                                                button_text = "✅ Zaten Uygulandı"
                                                break
                                        if is_applied:
                                            break
                            
                            if is_applied:
                                st.button(button_text, key=f"apply_suggestion_{step_key}_{current_index}", width='stretch', disabled=True)
                            else:
                                if st.button("✅ Uygula", key=f"apply_suggestion_{step_key}_{current_index}", width='stretch', type="primary"):
                                    # Validate method for encoding step
                                    if step_key == 'encoding':
                                        valid_methods = ['label_encoding', 'one_hot_encoding', 'ordinal_encoding', 'binary_encoding', 'frequency_encoding']
                                        if method not in valid_methods:
                                            st.error(f"❌ Bilinmeyen yöntem: '{method}'. Lütfen geçerli bir yöntem seçin: {', '.join(valid_methods)}")
                                            logger.warning(f"Unknown method for encoding: {method}")
                                        else:
                                            apply_preprocessing_suggestion(current_df, suggestion, step_key)
                                    else:
                                        apply_preprocessing_suggestion(current_df, suggestion, step_key)
                        else:
                            # No columns case (shouldn't happen for encoding)
                            card_html = f"""
                        <div style='
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 25px;
                            border-radius: 15px;
                            margin: 10px 0;
                            color: white;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            min-height: 150px;
                            border-left: 5px solid #f0f0f0;
                        '>
                            <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;'>
                                <h3 style='color: white; margin: 0; font-size: 1.4em; font-weight: bold;'>
                                    🔤 {method_safe}
                                </h3>
                                <div style='display: flex; gap: 10px;'>
                                    <span style='
                                        background: {priority_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                    '>
                                        Öncelik: {priority_safe}
                                    </span>
                                    <span style='
                                        background: {level_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                        text-transform: uppercase;
                                    '>
                                        {level_safe}
                                    </span>
                                </div>
                            </div>
                            <p style='
                                color: white; 
                                margin: 0; 
                                line-height: 1.8; 
                                font-size: 1.05em;
                                padding: 15px;
                                background: rgba(255, 255, 255, 0.15);
                                border-radius: 8px;
                                font-weight: 500;
                            '>
                                {reason_safe}
                            </p>
                        </div>
                        """
                            st.markdown(card_html, unsafe_allow_html=True)
                            st.info("ℹ️ Bu öneri için sütun bilgisi bulunamadı.")
                    
                    with col3:
                        if st.button("Sonraki ▶️", key=f"next_suggestion_{step_key}", disabled=(current_index >= len(suggestions) - 1), width='stretch'):
                            st.session_state[index_key] = min(len(suggestions) - 1, current_index + 1)
                            st.rerun()
                    
                    # Dots indicator
                    dots_html = "<div style='text-align: center; margin-top: 15px;'>"
                    for i in range(len(suggestions)):
                        if i == current_index:
                            dots_html += "🔵 "
                        else:
                            dots_html += "⚪ "
                    dots_html += "</div>"
                    st.markdown(dots_html, unsafe_allow_html=True)
                else:
                    st.info("ℹ️ Henüz öneri bulunmuyor. 'LLM Önerilerini Al' butonuna tıklayın.")
    
    st.markdown("---")
    
    # Manual operations
    st.markdown("### 🔧 Manuel İşlemler")
    
    # Define step_key for encoding step (for manual operations)
    step_key = 'encoding'
    
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    '>
    """, unsafe_allow_html=True)
    
    # Column selection
    st.markdown("#### 📌 Sütun Seçimi")
    
    # Use processed_columns already calculated at the beginning (from get_processed_encoding_columns)
    # This includes ALL encoding operations from history, not just current step
    
    # Use CURRENT categorical columns ONLY - filter out already processed columns
    available_columns = [
        col for col in current_categorical_cols 
        if col not in processed_columns
    ]
    
    logger.debug(f"🔍 [ENCODING SELECTION] current_categorical_cols: {current_categorical_cols}")
    logger.debug(f"🔍 [ENCODING SELECTION] current_df.columns: {list(current_df.columns)}")
    logger.debug(f"🔍 [ENCODING SELECTION] processed_columns: {processed_columns}")
    logger.debug(f"🔍 [ENCODING SELECTION] available_columns: {available_columns}")
    
    if available_columns:
        selected_columns = st.multiselect(
            "Encoding yapmak istediğiniz kategorik sütunları seçin",
            options=available_columns,
            help=f"Encoding yapılabilir {len(available_columns)} sütun gösteriliyor (Daha önce işlenen {len(processed_columns)} sütun gizlendi)",
            label_visibility="collapsed"
        )
        
        if selected_columns:
            st.info(f"✅ {len(selected_columns)} sütun seçildi")
        else:
            st.info("ℹ️ Lütfen encoding yapmak istediğiniz sütunları seçin")
    else:
        if current_categorical_cols:
            if len(processed_columns) > 0:
                st.success(f"✅ Tüm kategorik sütunlar encode edildi! ({len(processed_columns)} sütun)")
            else:
                st.info("ℹ️ Mevcut DataFrame'de kategorik sütun bulunmuyor.")
        else:
            st.success("✅ Veri setinde kategorik sütun bulunmuyor!")
        selected_columns = []
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Method selection
    st.markdown("#### ⚙️ Yöntem Seçimi")
    
    if selected_columns:
        method = st.selectbox(
            "Encoding yöntemi",
            options=['label_encoding', 'one_hot_encoding', 'ordinal_encoding', 'binary_encoding', 'frequency_encoding'],
            key="encoding_method_select",
            help="Kategorik sütunlar için encoding yöntemleri"
        )
        
        method_info = {
            'label_encoding': {
                'name': 'Label Encoding',
                'description': 'Her kategoriye benzersiz bir tam sayı atar. Sıralı veriler veya kategoriler arasında doğal bir sıralama varsa uygundur.<br><br><strong>✓ Avantajları:</strong> Basit ve hızlı, sütun sayısını artırmaz, bellek kullanımı düşük.<br><strong>✗ Dezavantajları:</strong> Kategoriler arasında mesafe yaratır (örn: 0,1,2), nominal veriler için uygun değil.<br><strong>📌 Kullanım:</strong> Sıralı kategoriler (düşük, orta, yüksek), ağaç tabanlı modeller için idealdir.'
            },
            'one_hot_encoding': {
                'name': 'One-Hot Encoding',
                'description': 'Her kategori için ayrı bir binary sütun oluşturur. Nominal veriler için idealdir.<br><br><strong>✓ Avantajları:</strong> Kategoriler arasında mesafe yaratmaz, nominal veriler için mükemmel, doğrusal modeller için uygun.<br><strong>✗ Dezavantajları:</strong> Yüksek cardinality durumunda çok sayıda sütun oluşturur, bellek kullanımı artar.<br><strong>📌 Kullanım:</strong> Düşük cardinality (<10) nominal veriler, şehir, renk, kategori gibi değişkenler için idealdir.'
            },
            'ordinal_encoding': {
                'name': 'Ordinal Encoding',
                'description': 'Kategorilere özel bir sıralama atar. Manuel mapping veya otomatik sıralama kullanılabilir.<br><br><strong>✓ Avantajları:</strong> Sıralı veriler için mantıklı, sütun sayısını artırmaz, özel sıralama tanımlanabilir.<br><strong>✗ Dezavantajları:</strong> Manuel mapping gerektirebilir, nominal veriler için uygun değil.<br><strong>📌 Kullanım:</strong> Eğitim seviyesi (ilkokul, ortaokul, lise), derecelendirme (1-5 yıldız) gibi sıralı veriler için idealdir.'
            },
            'binary_encoding': {
                'name': 'Binary Encoding',
                'description': 'Kategorileri binary (ikili) formatta kodlar. Yüksek cardinality için one-hot encoding\'e alternatif.<br><br><strong>✓ Avantajları:</strong> Yüksek cardinality için uygun, one-hot\'tan daha az sütun oluşturur, bellek verimli.<br><strong>✗ Dezavantajları:</strong> One-hot kadar yaygın değil, bazı modeller için uygun olmayabilir.<br><strong>📌 Kullanım:</strong> Yüksek cardinality (>10) kategorik veriler, ZIP kodları, ürün kategorileri için idealdir.'
            },
            'frequency_encoding': {
                'name': 'Frequency Encoding',
                'description': 'Kategorileri frekans değerleriyle değiştirir. Orijinal sütun korunur, yeni bir frekans sütunu eklenir.<br><br><strong>✓ Avantajları:</strong> Veri kaybı olmaz, orijinal sütun korunur, frekans bilgisi model için yararlı olabilir.<br><strong>✗ Dezavantajları:</strong> Yeni sütun ekler, aynı frekansa sahip kategoriler aynı değeri alır.<br><strong>📌 Kullanım:</strong> Frekans bilgisinin önemli olduğu durumlar, nadir kategorilerin tespiti için idealdir.'
            }
        }
        
        method_info_display = method_info.get(method, {'name': method, 'description': 'Yöntem bilgisi bulunamadı'})
        st.markdown(f"""
        <div class="flip-card">
            <div class="flip-card-inner">
                <div class="flip-card-front">
                    <div>
                        <div style="font-size: 2.1em; font-weight: bold; margin-bottom: 5px;">📊 Bilgi Kartı</div>
                        <div style="font-size: 1.9em;">{method_info_display['name']}</div>
                    </div>
                </div>
                <div class="flip-card-back">
                    <div style="width: 100%;">
                        <div style="font-weight: bold; margin-bottom: 10px; font-size: 1.1em; text-align: center;">{method_info_display['name']}</div>
                        <div style="text-align: center; padding: 0 10px;">{method_info_display['description']}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        method = None
        if not current_categorical_cols:
            st.info("ℹ️ Encoding yapılacak kategorik sütun bulunmuyor.")
        else:
            st.info("ℹ️ Önce sütun seçin")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Action buttons - Uygula butonu tüm satırı kaplar
    # Uygula butonu sadece yöntem seçildiğinde gösterilir (adım 1 mantığı)
    if selected_columns and method:
        if st.button("✅ Uygula", key="apply_encoding", type="primary", use_container_width=True):
                try:
                    df_processed = current_df.copy()
                    
                    # Apply encoding
                    df_processed = apply_encoding_method(df_processed, selected_columns, method)
                    
                    # Save to session state
                    st.session_state.preprocessed_data = df_processed
                    
                    # Add to history
                    st.session_state.preprocessing_history.append({
                        'step': current_step,
                        'step_key': step_key,
                        'type': step_key,
                        'method': method,
                        'columns': selected_columns,
                        'timestamp': datetime.now().isoformat(),
                        'before_data': current_df.copy()
                    })
                    
                    st.success(f"✅ Encoding başarıyla uygulandı! {len(selected_columns)} sütun işlendi: {', '.join(selected_columns)}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Hata oluştu: {str(e)}")
                    logger.error(f"Error applying encoding method: {e}", exc_info=True)
        elif not selected_columns:
            st.warning("⚠️ Lütfen en az bir sütun seçin")
        elif not method:
            st.warning("⚠️ Lütfen bir yöntem seçin")
    
    # Show applied operations for this step with undo functionality - ALWAYS SHOW
    st.markdown("### 📋 Uygulanan İşlemler")
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
    if step_history:
        for idx, hist in enumerate(step_history):
            method_op = hist.get('method', '')
            columns_op = hist.get('columns', [])
            
            col1, col2 = st.columns([4, 1])
            with col1:
                if columns_op:
                    display_text = f"{', '.join(columns_op)} sütunları - {method_op} ile encode edildi"
                else:
                    display_text = f"Tüm sütunlar - {method_op} ile encode edildi"
                
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 5px 0;
                    color: white;
                '>
                    <span style='font-size: 1.2em; margin-right: 10px;'>✅</span>
                    {display_text}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("↶ Geri Al", key=f"undo_encoding_{idx}", width='stretch'):
                    # Remove from history
                    operation_to_remove = step_history[idx]
                    removed_method = operation_to_remove.get('method', '')
                    removed_columns = operation_to_remove.get('columns', [])
                    
                    st.session_state.preprocessing_history.remove(operation_to_remove)
                    
                    # Rebuild dataframe - suppress INFO logs during rebuild
                    original_log_level = logger.level
                    logger.setLevel(logging.WARNING)
                    try:
                        df_rebuilt = st.session_state.original_data.copy()
                        
                        # Apply all operations in correct order: feature_engineering -> missing_values -> outlier -> encoding
                        for op in st.session_state.preprocessing_history:
                            op_type = op.get('type', '')
                            
                            if op_type == 'feature_engineering':
                                op_method = op.get('method', '')
                                if op_method == 'remove_duplicates':
                                    df_rebuilt = remove_duplicate_rows(df_rebuilt, keep=op.get('keep', 'first'))
                                elif op_method == 'drop_column':
                                    df_rebuilt = drop_columns(df_rebuilt, op.get('columns', []))
                                elif op_method == 'create_numeric_feature':
                                    df_rebuilt = create_numeric_feature(
                                        df_rebuilt,
                                        op.get('operation', 'add'),
                                        op.get('columns', []),
                                        op.get('new_column_name', '')
                                    )
                                elif op_method == 'create_datetime_feature':
                                    df_rebuilt = create_datetime_feature(
                                        df_rebuilt,
                                        op.get('columns', [])[0] if op.get('columns') else '',
                                        op.get('feature_type', 'year'),
                                        op.get('new_column_name', '')
                                    )
                                elif op_method == 'create_categorical_combination':
                                    df_rebuilt = create_categorical_combination(
                                        df_rebuilt,
                                        op.get('columns', []),
                                        op.get('new_column_name', ''),
                                        op.get('separator', '_')
                                    )
                            elif op_type == 'missing_values':
                                op_method_dict = op.get('method_dict')
                                if op_method_dict:
                                    # Handle dict method (numeric and categorical separately)
                                    if op_method_dict.get('numeric') and op_method_dict.get('numeric_cols'):
                                        df_rebuilt = apply_missing_values_method(
                                            df_rebuilt, 
                                            op_method_dict['numeric_cols'], 
                                            op_method_dict['numeric']
                                        )
                                    if op_method_dict.get('categorical') and op_method_dict.get('categorical_cols'):
                                        df_rebuilt = apply_missing_values_method(
                                            df_rebuilt, 
                                            op_method_dict['categorical_cols'], 
                                            op_method_dict['categorical']
                                        )
                                else:
                                    # Handle string method
                                    df_rebuilt = apply_missing_values_method(
                                        df_rebuilt,
                                        op.get('columns', []),
                                        op.get('method', '')
                                    )
                            elif op_type == 'outlier':
                                outlier_method = op.get('method', '')
                                method_parts = outlier_method.split('_')
                                if len(method_parts) >= 2:
                                    detection_method = '_'.join(method_parts[:-1])
                                    action = method_parts[-1]
                                    df_rebuilt = apply_outlier_method_wrapper(
                                        df_rebuilt,
                                        op.get('columns', []),
                                        detection_method,
                                        action
                                    )
                            elif op_type == 'encoding':
                                # Check if columns exist before applying encoding
                                op_columns = op.get('columns', [])
                                op_method = op.get('method', '')
                                
                                # For binary/one-hot encoding, check if original columns exist
                                if op_method in ['binary_encoding', 'one_hot_encoding']:
                                    # Filter columns that exist in dataframe
                                    existing_columns = [col for col in op_columns if col in df_rebuilt.columns]
                                    if existing_columns:
                                        df_rebuilt = apply_encoding_method(
                                            df_rebuilt,
                                            existing_columns,
                                            op_method
                                        )
                                    else:
                                        logger.warning(f"⚠️ [UNDO ENCODING] Columns {op_columns} not found in dataframe, skipping encoding")
                                else:
                                    # For other encoding methods, apply normally
                                    df_rebuilt = apply_encoding_method(
                                        df_rebuilt,
                                        op_columns,
                                        op_method
                                    )
                    finally:
                        # Restore original log level
                        logger.setLevel(original_log_level)
                    
                    # If binary/one-hot encoding was removed, restore original columns from before_data
                    if removed_method in ['binary_encoding', 'one_hot_encoding'] and removed_columns:
                        before_data = operation_to_remove.get('before_data')
                        if before_data is not None:
                            for col in removed_columns:
                                # Remove binary/one-hot columns first
                                binary_cols = [c for c in df_rebuilt.columns if c.startswith(f"{col}_bin_")]
                                one_hot_cols = [c for c in df_rebuilt.columns if c.startswith(f"{col}_") and c != col]
                                cols_to_remove = binary_cols + one_hot_cols
                                if cols_to_remove:
                                    df_rebuilt = df_rebuilt.drop(columns=cols_to_remove)
                                
                                # Restore original column from before_data if it exists
                                if col in before_data.columns and col not in df_rebuilt.columns:
                                    df_rebuilt[col] = before_data[col]
                                    logger.debug(f"🔍 [UNDO ENCODING] Restored original column: {col}")
                    
                    st.session_state.preprocessed_data = df_rebuilt
                    
                    # Remove from applied_suggestion_ids if it was from LLM
                    if operation_to_remove.get('from_llm'):
                        remove_method = operation_to_remove.get('method', '')
                        remove_columns = operation_to_remove.get('columns', [])
                        # Use 'encoding' as step_key since we're in encoding step
                        step_key_undo = 'encoding'
                        suggestion_id = f"{step_key_undo}_{remove_method}_{'_'.join(remove_columns) if remove_columns else 'all'}"
                        if suggestion_id in st.session_state.applied_suggestion_ids:
                            st.session_state.applied_suggestion_ids.remove(suggestion_id)
                    
                    st.success("✅ İşlem geri alındı!")
                    st.rerun()
    else:
        st.info("ℹ️ Henüz bu adımda işlem uygulanmadı.")
    
    # Add spacing before navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Action buttons - right aligned at bottom
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([3, 1, 1, 1])
    with col_nav2:
        if current_step > 1:
            if st.button("← Geri", key="prev_step_encoding", width='stretch'):
                st.session_state.preprocessing_step -= 1
                st.rerun()
    with col_nav3:
        # Atla butonu - son adımda (Summary) gösterilmez
        if current_step < len(steps):
            if st.button("Atla", key="skip_step_encoding", width='stretch'):
                st.session_state.preprocessing_step += 1
                st.rerun()
    with col_nav4:
        has_operation = check_step_has_operation(current_step)
        if st.button("İleri →", key="next_step_encoding", disabled=not has_operation, width='stretch'):
            st.session_state.preprocessing_step += 1
            st.rerun()


def render_outlier_step(df):
    """Render outlier handling preprocessing step."""
    st.subheader(f"🎯 {steps[2]['name']}")
    
    # CRITICAL: Use current preprocessed_data directly (like missing values step does)
    # Don't rely on df parameter - get fresh copy from session state
    current_df = st.session_state.preprocessed_data.copy()
    
    # Recalculate numeric_cols from CURRENT dataframe
    current_numeric_cols = current_df.select_dtypes(include=[np.number]).columns.tolist()
    
    # DEBUG: Log current state
    logger.debug(f"🔍 [OUTLIER STEP] render_outlier_step called")
    logger.debug(f"🔍 [OUTLIER STEP] df param shape: {df.shape if df is not None else 'None'}")
    logger.debug(f"🔍 [OUTLIER STEP] current_df (from session) shape: {current_df.shape if current_df is not None else 'None'}")
    logger.debug(f"🔍 [OUTLIER STEP] current_df columns: {list(current_df.columns) if current_df is not None else 'None'}")
    logger.debug(f"🔍 [OUTLIER STEP] current_numeric_cols: {current_numeric_cols}")
    logger.debug(f"🔍 [OUTLIER STEP] numeric_cols (global): {numeric_cols}")
    
    # Outlier analysis section - EXACTLY like missing values step
    st.markdown("### 📊 Aykırı Değer Analizi")
    
    # Check if any operations were applied - if so, show updated analysis (EXACTLY like missing values)
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
    if step_history:
        st.info("ℹ️ İşlemler uygulandıktan sonra aykırı değer analizi güncellenmiştir.")
        logger.debug(f"🔍 [OUTLIER STEP] Step history found: {len(step_history)} operations")
        for i, op in enumerate(step_history):
            logger.debug(f"🔍 [OUTLIER STEP] Operation {i+1}: {op.get('method')} on {op.get('columns')}")
    
    # Get selected detection method from session state (default: iqr)
    detection_method_for_metrics = st.session_state.get('outlier_detection_method_for_table', 'iqr')
    
    # Analyze outliers using selected method for overview metrics - Use CURRENT dataframe
    logger.debug(f"🔍 [OUTLIER STEP] Calling analyze with {detection_method_for_metrics} method for {len(current_numeric_cols)} numeric columns")
    try:
        if detection_method_for_metrics == 'iqr':
            outlier_info = analyze_outliers_iqr(current_df, current_numeric_cols)
        elif detection_method_for_metrics == 'zscore':
            outlier_info = analyze_outliers_zscore(current_df, current_numeric_cols)
        elif detection_method_for_metrics == 'isolation_forest':
            outlier_info = analyze_outliers_isolation_forest(current_df, current_numeric_cols)
        elif detection_method_for_metrics == 'lof':
            outlier_info = analyze_outliers_lof(current_df, current_numeric_cols)
        else:
            outlier_info = analyze_outliers_iqr(current_df, current_numeric_cols)
        
        logger.debug(f"🔍 [OUTLIER STEP] Analysis complete: {outlier_info['total_outliers']} total outliers")
        logger.debug(f"🔍 [OUTLIER STEP] Columns with outliers: {[col for col, info in outlier_info['outliers_by_column'].items() if info['count'] > 0]}")
    except Exception as e:
        logger.error(f"❌ [OUTLIER STEP] Error in analyze with {detection_method_for_metrics}: {e}", exc_info=True)
        st.error(f"❌ Aykırı değer analizi sırasında hata oluştu: {str(e)}")
        return
    
    # Summary metrics (will be updated when method changes) - in purple cards
    columns_with_outliers = [col for col, info in outlier_info['outliers_by_column'].items() if info['count'] > 0]
    
    # Calculate total cells for display
    total_cells = len(current_df) * len(current_numeric_cols) if current_numeric_cols else len(current_df)
    total_rows = len(current_df)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Toplam Aykırı Değer</div>
            <div style='font-size: 2em; font-weight: bold;'>{outlier_info['total_outliers']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Aykırı Değer Yüzdesi</div>
            <div style='font-size: 2em; font-weight: bold;'>{outlier_info['total_outlier_percentage']:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Aykırı Değer İçeren Sütun</div>
            <div style='font-size: 2em; font-weight: bold;'>{len(columns_with_outliers)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            <div style='font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;'>Toplam Satır Sayısı</div>
            <div style='font-size: 2em; font-weight: bold;'>{total_rows:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Box plot visualization - Only for IQR method
    st.markdown("#### 📦 Kutu Grafiği")
    if detection_method_for_metrics == 'iqr':
        # Show box plots only for columns with outliers
        if columns_with_outliers:
            selected_col_for_plot = st.selectbox(
                "Görselleştirmek istediğiniz sütunu seçin",
                options=columns_with_outliers,
                key="outlier_box_plot_select"
            )
            if selected_col_for_plot:
                box_plot = create_box_plot(current_df, selected_col_for_plot, library='plotly', title=f'{selected_col_for_plot} - Aykırı Değer Analizi')
                if box_plot:
                    st.plotly_chart(box_plot, width='stretch', key=f"outlier_box_plot_{selected_col_for_plot}")
                else:
                    st.warning(f"⚠️ {selected_col_for_plot} sütunu için kutu grafiği oluşturulamadı.")
        else:
            st.info("ℹ️ Aykırı değer içeren sütun bulunamadığı için kutu grafiği gösterilemiyor.")
    elif detection_method_for_metrics == 'zscore':
        # Histogram for Z-Score method - only for columns with outliers
        st.markdown("#### 📊 Histogram (Z-Score için)")
        if columns_with_outliers:
            selected_col_for_hist = st.selectbox(
                "Görselleştirmek istediğiniz sütunu seçin",
                options=columns_with_outliers,
                key="outlier_histogram_select"
            )
            if selected_col_for_hist:
                histogram = create_histogram(
                    current_df, 
                    selected_col_for_hist, 
                    library='plotly', 
                    title=f'{selected_col_for_hist} - Z-Score Dağılımı'
                )
                if histogram:
                    st.plotly_chart(histogram, width='stretch', key=f"outlier_histogram_{selected_col_for_hist}")
                else:
                    st.warning(f"⚠️ {selected_col_for_hist} sütunu için histogram oluşturulamadı.")
        else:
            st.info("ℹ️ Aykırı değer içeren sütun bulunamadığı için histogram gösterilemiyor.")
    
    elif detection_method_for_metrics in ['isolation_forest', 'lof']:
        # PCA-based 2D scatter plot for Isolation Forest and LOF
        method_name = 'Isolation Forest' if detection_method_for_metrics == 'isolation_forest' else 'LOF'
        st.markdown(f"#### 📊 2D Scatter Plot (PCA) - {method_name} için")
        
        if len(current_numeric_cols) >= 2:
            try:
                from sklearn.decomposition import PCA
                from sklearn.preprocessing import StandardScaler
                
                # Prepare data: use all numeric columns
                numeric_data = current_df[current_numeric_cols].dropna()
                
                if len(numeric_data) > 0:
                    # Standardize the data
                    scaler = StandardScaler()
                    scaled_data = scaler.fit_transform(numeric_data)
                    
                    # Apply PCA to 2 dimensions
                    pca = PCA(n_components=2, random_state=42)
                    pca_data = pca.fit_transform(scaled_data)
                    
                    # Create DataFrame for visualization
                    pca_df = pd.DataFrame(
                        pca_data, 
                        columns=['PC1', 'PC2'],
                        index=numeric_data.index
                    )
                    
                    # Get outlier indices from analysis
                    outlier_indices = list(outlier_info.get('outlier_rows', set()))
                    
                    # Add outlier label column
                    pca_df['is_outlier'] = pca_df.index.isin(outlier_indices)
                    pca_df['is_outlier'] = pca_df['is_outlier'].map({True: 'Aykırı Değer', False: 'Normal'})
                    
                    # Create scatter plot with color coding
                    import plotly.express as px
                    fig = px.scatter(
                        pca_df,
                        x='PC1',
                        y='PC2',
                        color='is_outlier',
                        title=f'{method_name} - PCA 2D Görselleştirme (Tüm Sayısal Sütunlar)',
                        labels={
                            'PC1': f'PC1 ({pca.explained_variance_ratio_[0]:.1%} varyans)',
                            'PC2': f'PC2 ({pca.explained_variance_ratio_[1]:.1%} varyans)',
                            'is_outlier': 'Durum'
                        },
                        color_discrete_map={
                            'Aykırı Değer': '#FF4444',
                            'Normal': '#4444FF'
                        }
                    )
                    fig.update_layout(
                        height=600,
                        template='plotly_dark',
                        showlegend=True
                    )
                    st.plotly_chart(fig, width='stretch', key=f"outlier_pca_scatter_{detection_method_for_metrics}")
                    
                    # Show PCA info
                    st.caption(f"ℹ️ PCA, {len(current_numeric_cols)} sayısal sütunu 2 boyuta indirgedi. "
                              f"Toplam varyansın {pca.explained_variance_ratio_.sum():.1%}'i korundu.")
                else:
                    st.warning("⚠️ Sayısal veri bulunamadı (tüm değerler NaN).")
            except Exception as e:
                logger.error(f"❌ PCA scatter plot oluşturulurken hata: {e}", exc_info=True)
                st.error(f"❌ PCA görselleştirmesi oluşturulamadı: {str(e)}")
        elif len(current_numeric_cols) == 1:
            st.info("ℹ️ En az 2 sayısal sütun gereklidir. PCA görselleştirmesi için yeterli sütun yok.")
        else:
            st.info("ℹ️ Sayısal sütun bulunamadığı için PCA görselleştirmesi gösterilemiyor.")
    
    st.markdown("---")
    
    # Detection Method Selection (for table display)
    # Create columns: title and info card on same row
    col_title, col_info = st.columns([2, 3])
    
    with col_title:
        st.markdown("#### 🔍 Aykırı Değer Tespit Yöntemi")
        detection_method_for_table = st.radio(
            "Tespit yöntemini seçin (tablo güncellenecek)",
            options=['iqr', 'zscore', 'isolation_forest', 'lof'],
            key="outlier_detection_method_for_table",
            horizontal=True,
            help="Farklı yöntemler farklı aykırı değer sonuçları verebilir. Tabloyu güncellemek için bir yöntem seçin.",
            label_visibility="visible"
        )
    
    with col_info:
        # Method info cards
        method_info = {
            'iqr': {
                'name': 'IQR (Interquartile Range)',
                'short_desc': 'Çeyrekler arası aralık yöntemi',
                'description': '<strong>Nasıl Çalışır:</strong> Q1 ve Q3 çeyreklerini hesaplar. IQR = Q3 - Q1. Alt sınır: Q1 - 1.5×IQR, Üst sınır: Q3 + 1.5×IQR<br><br><strong>✓ Avantajları:</strong> Basit, hızlı, normal dağılım varsayımı yok<br><strong>✗ Dezavantajları:</strong> Tek değişkenli, çok değişkenli ilişkileri yakalamaz<br><strong>📌 Kullanım:</strong> Normal dağılıma yakın veriler için ideal'
            },
            'zscore': {
                'name': 'Z-Score',
                'short_desc': 'Standart sapma tabanlı yöntem',
                'description': '<strong>Nasıl Çalışır:</strong> Ortalama ve standart sapma hesaplanır. Z-skoru 3\'ten büyük (veya -3\'ten küçük) değerler aykırı kabul edilir<br><br><strong>✓ Avantajları:</strong> Hızlı, normal dağılımlar için güvenilir<br><strong>✗ Dezavantajları:</strong> Normal dağılım varsayımı, aykırı değerlerden etkilenebilir<br><strong>📌 Kullanım:</strong> Normal dağılımlı veriler için uygun'
            },
            'isolation_forest': {
                'name': 'Isolation Forest',
                'short_desc': 'Makine öğrenmesi tabanlı',
                'description': '<strong>Nasıl Çalışır:</strong> Rastgele özellikler ve bölme noktalarıyla ağaçlar oluşturur. Aykırı değerler daha kısa yollarda izole edilir<br><br><strong>✓ Avantajları:</strong> Çok değişkenli, normal dağılım varsayımı yok, büyük veri setlerinde etkili<br><strong>✗ Dezavantajları:</strong> Daha yavaş, parametre ayarı gerekir<br><strong>📌 Kullanım:</strong> Çok boyutlu ve karmaşık veriler için ideal'
            },
            'lof': {
                'name': 'LOF (Local Outlier Factor)',
                'short_desc': 'Yerel yoğunluk tabanlı',
                'description': '<strong>Nasıl Çalışır:</strong> Her noktanın yerel yoğunluğunu komşularıyla karşılaştırır. Düşük yoğunluklu noktalar aykırı kabul edilir<br><br><strong>✓ Avantajları:</strong> Yerel desenleri yakalar, küme yapılarını korur<br><strong>✗ Dezavantajları:</strong> Hesaplama maliyeti yüksek, parametre ayarı gerekir<br><strong>📌 Kullanım:</strong> Küme yapılı veriler için uygun'
            }
        }
        
        selected_method_info = method_info.get(detection_method_for_table, method_info['iqr'])
        
        # Info card (compact, horizontal style) - align with title
        card_id = f"method_info_card_{detection_method_for_table}"
        st.markdown(f"""
        <div id="{card_id}" style="width: 100%; height: 200px; perspective: 1000px; margin-top: -10px; margin-bottom: 10px;">
            <div class="method-info-card-inner" style="position: relative; width: 100%; height: 100%; text-align: center; transition: transform 0.6s; transform-style: preserve-3d;">
                <div class="method-info-card-front" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 10px; display: flex; align-items: center; justify-content: center; padding: 15px 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                    <div style="text-align: center; width: 100%;">
                        <div style="font-size: 1.3em; font-weight: bold; margin-bottom: 8px;">📊 {selected_method_info['name']}</div>
                        <div style="font-size: 1em; opacity: 0.9;">{selected_method_info['short_desc']}</div>
                    </div>
                </div>
                <div class="method-info-card-back" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 10px; display: flex; align-items: center; justify-content: center; padding: 15px 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); background: linear-gradient(135deg, #764ba2 0%, #667eea 100%); color: white; transform: rotateY(180deg); font-size: 0.85em; line-height: 1.5; text-align: center; overflow-y: auto;">
                    <div style="width: 100%;">
                        <div style="font-weight: bold; margin-bottom: 8px; font-size: 1.1em;">{selected_method_info['name']}</div>
                        <div style="padding: 0 5px; font-size: 0.9em; line-height: 1.5;">{selected_method_info['description']}</div>
                    </div>
                </div>
            </div>
        </div>
        <style>
            #{card_id}:hover .method-info-card-inner {{
                transform: rotateY(180deg);
            }}
        </style>
        """, unsafe_allow_html=True)
    
    # Analyze outliers using selected method
    try:
        if detection_method_for_table == 'iqr':
            outlier_info_table = analyze_outliers_iqr(current_df, current_numeric_cols)
        elif detection_method_for_table == 'zscore':
            outlier_info_table = analyze_outliers_zscore(current_df, current_numeric_cols)
        elif detection_method_for_table == 'isolation_forest':
            outlier_info_table = analyze_outliers_isolation_forest(current_df, current_numeric_cols)
        elif detection_method_for_table == 'lof':
            outlier_info_table = analyze_outliers_lof(current_df, current_numeric_cols)
        else:
            outlier_info_table = analyze_outliers_iqr(current_df, current_numeric_cols)
    except Exception as e:
        logger.error(f"❌ [OUTLIER TABLE] Error analyzing with {detection_method_for_table}: {e}", exc_info=True)
        st.error(f"❌ {detection_method_for_table} yöntemi ile analiz sırasında hata oluştu: {str(e)}")
        outlier_info_table = outlier_info  # Fallback to default
    
    st.markdown("---")
    
    # Column-based detail table (method-specific)
    st.markdown("#### 📋 Sütun Bazlı Detay")
    outlier_detail_data = []
    
    # Get columns with outliers for the selected method
    columns_with_outliers_table = [col for col, info in outlier_info_table['outliers_by_column'].items() if info['count'] > 0]
    
    if columns_with_outliers_table:
        # Method-specific table columns
        if detection_method_for_table == 'iqr':
            # IQR: Show lower/upper bounds
            for col, info in outlier_info_table['outliers_by_column'].items():
                outlier_detail_data.append({
                    'Sütun': col,
                    'Aykırı Değer Sayısı': info['count'],
                    'Aykırı Değer Yüzdesi': f"{info['percentage']:.2f}%",
                    'Alt Sınır': f"{info.get('lower_bound', 'N/A'):.2f}" if 'lower_bound' in info and info.get('lower_bound') is not None else 'N/A',
                    'Üst Sınır': f"{info.get('upper_bound', 'N/A'):.2f}" if 'upper_bound' in info and info.get('upper_bound') is not None else 'N/A'
                })
        elif detection_method_for_table == 'zscore':
            # Z-Score: Show threshold and outlier row count
            threshold = outlier_info_table.get('threshold', 3.0)
            for col, info in outlier_info_table['outliers_by_column'].items():
                outlier_detail_data.append({
                    'Sütun': col,
                    'Aykırı Değer Sayısı': info['count'],
                    'Aykırı Değer Yüzdesi': f"{info['percentage']:.2f}%",
                    'Threshold': f"{threshold:.2f}",
                    'Aykırı Satır Sayısı': len(info.get('outlier_indices', []))
                })
        elif detection_method_for_table == 'isolation_forest':
            # Isolation Forest: Show contamination parameter
            contamination = outlier_info_table.get('contamination', 0.1)
            for col, info in outlier_info_table['outliers_by_column'].items():
                outlier_detail_data.append({
                    'Sütun': col,
                    'Aykırı Değer Sayısı': info['count'],
                    'Aykırı Değer Yüzdesi': f"{info['percentage']:.2f}%",
                    'Contamination': f"{contamination:.2f}",
                    'Aykırı Satır Sayısı': len(info.get('outlier_indices', []))
                })
        elif detection_method_for_table == 'lof':
            # LOF: Show contamination and n_neighbors
            contamination = outlier_info_table.get('contamination', 0.1)
            n_neighbors = outlier_info_table.get('n_neighbors', 20)
            for col, info in outlier_info_table['outliers_by_column'].items():
                outlier_detail_data.append({
                    'Sütun': col,
                    'Aykırı Değer Sayısı': info['count'],
                    'Aykırı Değer Yüzdesi': f"{info['percentage']:.2f}%",
                    'Contamination': f"{contamination:.2f}",
                    'N Neighbors': n_neighbors,
                    'Aykırı Satır Sayısı': len(info.get('outlier_indices', []))
                })
        
        if outlier_detail_data:
            outlier_df = pd.DataFrame(outlier_detail_data)
            outlier_df = outlier_df.sort_values('Aykırı Değer Yüzdesi', ascending=False)
            st.dataframe(outlier_df, width='stretch', hide_index=True)
        else:
            st.success("✅ Veri setinde aykırı değer bulunmuyor!")
    else:
        st.success("✅ Veri setinde aykırı değer bulunmuyor!")
    
    # Show message below table if no outliers
    if not columns_with_outliers_table:
        st.info("ℹ️ Seçilen yöntem ({}) ile tespit edilen aykırı değer bulunmuyor.".format(
            detection_method_for_table.upper() if detection_method_for_table != 'isolation_forest' else 'Isolation Forest'
        ))
    
    st.markdown("---")
    
    # LLM suggestions section (similar to missing values)
    # Use selected method for LLM suggestions
    columns_with_outliers_for_llm = [col for col, info in outlier_info_table['outliers_by_column'].items() if info['count'] > 0]
    
    if llm_enabled:
        step_key = 'outlier'
        suggestions_key = f'step_{current_step}_{step_key}_{detection_method_for_table}'
        index_key = f'preprocessing_suggestion_index_{step_key}_{detection_method_for_table}'
        
        # Initialize suggestion index for this step and method
        if index_key not in st.session_state:
            st.session_state[index_key] = 0
        
        # Clear suggestions if no columns with outliers for selected method
        if not columns_with_outliers_for_llm:
            if suggestions_key in st.session_state.preprocessing_suggestions:
                del st.session_state.preprocessing_suggestions[suggestions_key]
                st.session_state[index_key] = 0
        
        with st.expander("🤖 LLM Önerileri", expanded=True):
            # Only show button if there are columns with outliers for selected method
            if not columns_with_outliers_for_llm:
                st.info(f"ℹ️ Seçilen yöntem ({detection_method_for_table.upper() if detection_method_for_table != 'isolation_forest' else 'Isolation Forest'}) ile aykırı değer içeren sütun bulunmadığı için LLM önerisi alınamaz.")
            elif suggestions_key not in st.session_state.preprocessing_suggestions:
                if st.button("💡 LLM Önerilerini Al", key=f"get_suggestions_{step_key}_{detection_method_for_table}"):
                    # Yeni öneriler alındığında uygulanmış öneri ID'lerini temizle (bu step için)
                    # Not: Tüm applied_suggestion_ids'i temizlemiyoruz, sadece bu step için olanları
                    
                    with st.spinner("🤖 LLM önerileri oluşturuluyor..."):
                        # Get outlier columns info for prompt using SELECTED METHOD
                        # Use current_df and current_numeric_cols
                        if detection_method_for_table == 'iqr':
                            outlier_info_step = analyze_outliers_iqr(current_df, current_numeric_cols)
                        elif detection_method_for_table == 'zscore':
                            outlier_info_step = analyze_outliers_zscore(current_df, current_numeric_cols)
                        elif detection_method_for_table == 'isolation_forest':
                            outlier_info_step = analyze_outliers_isolation_forest(current_df, current_numeric_cols)
                        elif detection_method_for_table == 'lof':
                            outlier_info_step = analyze_outliers_lof(current_df, current_numeric_cols)
                        else:
                            outlier_info_step = analyze_outliers_iqr(current_df, current_numeric_cols)
                        
                        columns_with_outliers_step = [col for col, info in outlier_info_step['outliers_by_column'].items() if info['count'] > 0]
                        
                        # Update data_summary with outlier columns info (EXACTLY like missing values step)
                        # Recalculate data_summary from current_df
                        current_data_summary = get_data_summary(current_df)
                        data_summary_with_outliers = current_data_summary.copy()
                        if 'outliers' not in data_summary_with_outliers:
                            data_summary_with_outliers['outliers'] = {}
                        data_summary_with_outliers['outliers']['columns_with_outliers'] = columns_with_outliers_step
                        data_summary_with_outliers['outliers']['outliers_by_column'] = {
                            col: info for col, info in outlier_info_step['outliers_by_column'].items() 
                            if info['count'] > 0
                        }
                        
                        # CRITICAL: Only send columns WITH outliers to LLM (not all numeric columns)
                        # Use empty categorical_cols since outliers are only for numeric columns
                        if step_key == 'outlier':
                            suggestions_result = suggest_outlier_steps(
                                data_summary=data_summary_with_outliers,
                                numeric_columns=columns_with_outliers_step,  # ONLY columns with outliers (not all numeric cols)
                                categorical_columns=[],  # No categorical columns for outlier step
                                analysis_level=analysis_level,
                                detection_method=detection_method_for_table  # Pass selected detection method
                            )
                        else:
                            suggestions_result = {"suggestions": []}
                        
                        if suggestions_result.get('error'):
                            st.error(f"❌ LLM önerisi alınamadı: {suggestions_result.get('error')}")
                        else:
                            suggestions = suggestions_result.get('suggestions', [])
                            # Filter suggestions for this step type, selected method, and only columns with outliers
                            filtered_suggestions = [
                                s for s in suggestions 
                                if s.get('preprocessing_type') == step_key 
                                and all(col in columns_with_outliers_step for col in s.get('columns', []))
                                and s.get('method', '').startswith(f"{detection_method_for_table}_")  # Filter by selected method
                            ]
                            
                            # Otomatik öncelik hesaplaması (LLM'in verdiği önceliği override et) - EXACTLY like missing values
                            if step_key == 'outlier':
                                outliers_by_column = outlier_info_step.get('outliers_by_column', {})
                                for suggestion in filtered_suggestions:
                                    columns = suggestion.get('columns', [])
                                    if columns:
                                        # Her sütun için aykırı değer yüzdesini kontrol et
                                        max_outlier_pct = 0
                                        for col in columns:
                                            if col in outliers_by_column:
                                                max_outlier_pct = max(max_outlier_pct, outliers_by_column[col]['percentage'])
                                        
                                        # Önceliği otomatik belirle (LLM'in verdiği önceliği override et)
                                        if max_outlier_pct > 20:
                                            suggestion['priority'] = 'yüksek'
                                        elif max_outlier_pct >= 5:
                                            suggestion['priority'] = 'orta'
                                        else:
                                            suggestion['priority'] = 'düşük'
                            
                            st.session_state.preprocessing_suggestions[suggestions_key] = filtered_suggestions
                            st.session_state[index_key] = 0  # Reset index
                            if filtered_suggestions:
                                st.success(f"✅ {len(filtered_suggestions)} öneri alındı")
                            st.rerun()
            else:
                # Refresh button
                if st.button("🔄 Yeni Öneriler Al", key=f"refresh_suggestions_{step_key}"):
                    del st.session_state.preprocessing_suggestions[suggestions_key]
                    st.session_state[index_key] = 0
                    st.rerun()
            
            # Display suggestions in carousel format (similar to missing values)
            if suggestions_key in st.session_state.preprocessing_suggestions:
                suggestions = st.session_state.preprocessing_suggestions[suggestions_key]
                if suggestions:
                    current_index = st.session_state[index_key]
                    
                    st.markdown(f"<div style='text-align: center; margin: 10px 0;'><strong>{len(suggestions)} öneri sunuldu</strong> | <em>Öneri {current_index + 1}/{len(suggestions)}</em></div>", unsafe_allow_html=True)
                    
                    # Navigation buttons and current suggestion
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        if st.button("◀️ Önceki", key=f"prev_suggestion_{step_key}_{detection_method_for_table}", disabled=(current_index == 0), width='stretch'):
                            st.session_state[index_key] = max(0, current_index - 1)
                            st.rerun()
                    
                    with col2:
                        # Current suggestion - kart tasarımı
                        suggestion = suggestions[current_index]
                        method = suggestion.get('method', 'Bilinmeyen')
                        columns = suggestion.get('columns', [])
                        reason = suggestion.get('reason', '')
                        priority = suggestion.get('priority', 'orta')
                        analysis_level_sugg = suggestion.get('analysis_level', 'Temel')
                        
                        # HTML tag'lerini temizle
                        import html as html_module
                        import re
                        if reason:
                            try:
                                reason = html_module.unescape(reason)
                            except:
                                pass
                            reason = re.sub(r'<[^>]+>', '', reason, flags=re.DOTALL | re.IGNORECASE)
                            reason = ' '.join(reason.split()).strip()
                        
                        # Priority ve level renkleri
                        priority_colors = {'yüksek': '#f44336', 'orta': '#ff9800', 'düşük': '#4caf50'}
                        level_colors = {'Temel': '#4CAF50', 'Orta': '#FF9800', 'Gelişmiş': '#F44336'}
                        priority_color = priority_colors.get(priority, '#ff9800')
                        level_color = level_colors.get(analysis_level_sugg, '#4CAF50')
                        
                        # Güvenli HTML
                        method_safe = html_module.escape(str(method))
                        reason_safe = html_module.escape(reason) if reason else 'Açıklama bulunamadı.'
                        priority_safe = html_module.escape(priority)
                        level_safe = html_module.escape(analysis_level_sugg)
                        columns_display = ', '.join(columns) if columns else 'Tüm sütunlar'
                        columns_safe = html_module.escape(columns_display)
                        
                        # Kart tasarımı
                        if columns:
                            card_html = f"""
                        <div style='
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 25px;
                            border-radius: 15px;
                            margin: 10px 0;
                            color: white;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            min-height: 180px;
                            border-left: 5px solid #f0f0f0;
                        '>
                            <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;'>
                                <h3 style='color: white; margin: 0; margin-right: 10px; font-size: 1.3em;'>
                                    🎯 {method_safe}
                                </h3>
                                <div style='display: flex; gap: 10px;'>
                                    <span style='
                                        background: {priority_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                    '>
                                        Öncelik: {priority_safe}
                                    </span>
                                    <span style='
                                        background: {level_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                        text-transform: uppercase;
                                    '>
                                        {level_safe}
                                    </span>
                                </div>
                            </div>
                            <div style='
                                background: rgba(255, 255, 255, 0.15);
                                padding: 10px 15px;
                                border-radius: 8px;
                                margin-bottom: 15px;
                                display: inline-block;
                            '>
                                <span style='color: #f0f0f0; font-size: 0.95em;'>
                                    <strong>📍 Sütunlar:</strong> {columns_safe}
                                </span>
                            </div>
                            <p style='
                                color: white; 
                                margin: 15px 0 0 0; 
                                line-height: 1.7; 
                                font-size: 1em;
                                padding: 10px;
                                background: rgba(255, 255, 255, 0.1);
                                border-radius: 8px;
                            '>
                                {reason_safe}
                            </p>
                        </div>
                        """
                        else:
                            card_html = f"""
                        <div style='
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 25px;
                            border-radius: 15px;
                            margin: 10px 0;
                            color: white;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            min-height: 150px;
                            border-left: 5px solid #f0f0f0;
                        '>
                            <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;'>
                                <h3 style='color: white; margin: 0; font-size: 1.4em; font-weight: bold;'>
                                    🎯 {method_safe}
                                </h3>
                                <div style='display: flex; gap: 10px;'>
                                    <span style='
                                        background: {priority_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                    '>
                                        Öncelik: {priority_safe}
                                    </span>
                                    <span style='
                                        background: {level_color};
                                        color: white;
                                        padding: 5px 12px;
                                        border-radius: 20px;
                                        font-size: 0.75em;
                                        font-weight: bold;
                                        text-transform: uppercase;
                                    '>
                                        {level_safe}
                                    </span>
                                </div>
                            </div>
                            <p style='
                                color: white; 
                                margin: 0; 
                                line-height: 1.8; 
                                font-size: 1.05em;
                                padding: 15px;
                                background: rgba(255, 255, 255, 0.15);
                                border-radius: 8px;
                                font-weight: 500;
                            '>
                                {reason_safe}
                            </p>
                        </div>
                        """
                        
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Uygula butonu - Check if method+column combination already applied
                        method = suggestion.get('method', '')
                        columns = suggestion.get('columns', [])
                        
                        # Check if this method+column combination is already applied
                        is_applied = False
                        is_manual_operation = False
                        button_text = "✅ Zaten Uygulandı"
                        
                        if step_key == 'outlier' and columns:
                            # Get all processed columns from step history (step 2 = outlier)
                            step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
                            processed_columns = set()
                            for hist in step_history:
                                hist_columns = hist.get('columns', [])
                                if isinstance(hist_columns, list):
                                    processed_columns.update(hist_columns)
                            
                            # Check if any of the suggested columns are already processed
                            already_processed_cols = [col for col in columns if col in processed_columns]
                            
                            if already_processed_cols:
                                # Check if it was applied via LLM suggestion or manually
                                is_llm_applied = False
                                for col in already_processed_cols:
                                    for history_item in step_history:
                                        if (history_item.get('type') == step_key and
                                            history_item.get('method') == method and
                                            col in history_item.get('columns', [])):
                                            is_llm_applied = True
                                            break
                                    if is_llm_applied:
                                        break
                                
                                is_applied = True
                                if not is_llm_applied:
                                    # Manual operation
                                    is_manual_operation = True
                                    button_text = f"ℹ️ Bu sütun üzerinde Manuel olarak işlem yapıldı: {', '.join(already_processed_cols)}"
                                else:
                                    # LLM suggestion was applied
                                    button_text = "✅ Zaten Uygulandı"
                            else:
                                # Also check if this specific method+column combination is already applied
                                for col in columns:
                                    for history_item in st.session_state.preprocessing_history:
                                        if (history_item.get('step') == current_step and 
                                            history_item.get('type') == step_key and
                                            history_item.get('method') == method and
                                            col in history_item.get('columns', [])):
                                            is_applied = True
                                            button_text = "✅ Zaten Uygulandı"
                                            break
                                    if is_applied:
                                        break
                        
                        # Also check by suggestion_id for backward compatibility
                        if not is_applied:
                            suggestion_id = f"{step_key}_{method}_{'_'.join(columns) if columns else 'all'}"
                            is_applied = suggestion_id in st.session_state.applied_suggestion_ids
                            if is_applied:
                                button_text = "✅ Zaten Uygulandı"
                        
                        if is_applied:
                            st.button(button_text, key=f"apply_suggestion_{step_key}_{detection_method_for_table}_{current_index}", width='stretch', disabled=True)
                        else:
                            if st.button("✅ Uygula", key=f"apply_suggestion_{step_key}_{detection_method_for_table}_{current_index}", width='stretch', type="primary"):
                                # Validate method for outlier step
                                if step_key == 'outlier':
                                    valid_methods = ['iqr_remove', 'iqr_cap', 'zscore_remove', 'zscore_cap', 'isolation_forest_remove', 'lof_remove']
                                    if method not in valid_methods:
                                        st.error(f"❌ Bilinmeyen yöntem: '{method}'. Lütfen geçerli bir yöntem seçin: {', '.join(valid_methods)}")
                                        logger.warning(f"Unknown method for outlier: {method}")
                                    else:
                                        apply_preprocessing_suggestion(current_df, suggestion, step_key)
                                else:
                                    apply_preprocessing_suggestion(current_df, suggestion, step_key)
                    
                    with col3:
                        if st.button("Sonraki ▶️", key=f"next_suggestion_{step_key}_{detection_method_for_table}", disabled=(current_index == len(suggestions) - 1), width='stretch'):
                            st.session_state[index_key] = min(len(suggestions) - 1, current_index + 1)
                            st.rerun()
                    
                    # Dots indicator
                    dots_html = "<div style='text-align: center; margin-top: 15px;'>"
                    for i in range(len(suggestions)):
                        if i == current_index:
                            dots_html += "🔵 "
                        else:
                            dots_html += "⚪ "
                    dots_html += "</div>"
                    st.markdown(dots_html, unsafe_allow_html=True)
                else:
                    st.info("ℹ️ Henüz öneri bulunmuyor.")
    
    st.markdown("---")
    
    # Manual operations section
    st.markdown("### 🔧 Manuel İşlemler")
    
    # Create a styled container for manual operations
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    '>
    """, unsafe_allow_html=True)
    
    # Sütun Seçimi
    st.markdown("#### 📌 Sütun Seçimi")
    
    # Get columns with outliers (numeric only)
    # Get detection method from table selection (use same method for column list)
    detection_method_for_columns = st.session_state.get('outlier_detection_method_for_table', 'iqr')
    
    # Analyze outliers using selected method for column list
    try:
        if detection_method_for_columns == 'iqr':
            outlier_info_for_columns = analyze_outliers_iqr(current_df, current_numeric_cols)
        elif detection_method_for_columns == 'zscore':
            outlier_info_for_columns = analyze_outliers_zscore(current_df, current_numeric_cols)
        elif detection_method_for_columns == 'isolation_forest':
            outlier_info_for_columns = analyze_outliers_isolation_forest(current_df, current_numeric_cols)
        elif detection_method_for_columns == 'lof':
            outlier_info_for_columns = analyze_outliers_lof(current_df, current_numeric_cols)
        else:
            outlier_info_for_columns = analyze_outliers_iqr(current_df, current_numeric_cols)
    except Exception as e:
        logger.error(f"❌ [OUTLIER COLUMNS] Error analyzing with {detection_method_for_columns}: {e}", exc_info=True)
        outlier_info_for_columns = outlier_info  # Fallback to default
    
    columns_with_outliers_list = [col for col, info in outlier_info_for_columns['outliers_by_column'].items() if info['count'] > 0]
    
    # Get already processed columns from step history (step 2 = outlier)
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
    processed_columns = set()
    for hist in step_history:
        hist_columns = hist.get('columns', [])
        if isinstance(hist_columns, list):
            processed_columns.update(hist_columns)
    
    # Filter out already processed columns from selection options
    available_columns = [col for col in columns_with_outliers_list if col not in processed_columns]
    
    if available_columns:
        selected_columns = st.multiselect(
            "Aykırı değerleri işlemek istediğiniz sütunları seçin",
            options=available_columns,
            help=f"Aykırı değer içeren {len(available_columns)} sütun gösteriliyor (Daha önce işlenen {len(processed_columns)} sütun gizlendi)",
            label_visibility="collapsed"
        )
        
        # Show info message about selected columns
        if selected_columns:
            st.info(f"✅ {len(selected_columns)} sayısal sütun seçildi")
        else:
            st.info("ℹ️ Lütfen aykırı değerleri işlemek istediğiniz sütunları seçin")
    else:
        if columns_with_outliers_list:
            st.success(f"✅ Tüm aykırı değer içeren sütunlar işlendi! ({len(processed_columns)} sütun)")
        else:
            st.success("✅ Veri setinde aykırı değer bulunmuyor!")
        selected_columns = []
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Yöntem Seçimi (sadece action - remove/cap)
    st.markdown("#### ⚙️ Yöntem Seçimi")
    
    all_columns_processed = len(columns_with_outliers_list) > 0 and len(available_columns) == 0
    
    if selected_columns:
        # Get detection method from table selection
        detection_method = st.session_state.get('outlier_detection_method_for_table', 'iqr')
        
        # Action selection (remove or cap) - only action selection here
        action = st.selectbox(
            "İşlem Tipi",
            options=['remove', 'cap'] if detection_method in ['iqr', 'zscore'] else ['remove'],
            key="outlier_action",
            help="Aykırı değerleri kaldır (remove) veya sınırla (cap)",
            label_visibility="collapsed"
        )
        
        # Action info card (only one card now)
        action_info = {
            'remove': {
                'name': 'Kaldır (Remove)',
                'description': 'Aykırı değerleri içeren satırları veri setinden tamamen kaldırır.<br><br><strong>✓ Avantajları:</strong> Veri setini temizler, model performansını artırabilir.<br><strong>✗ Dezavantajları:</strong> Veri kaybına neden olur, örneklem boyutu küçülür.<br><strong>📌 Kullanım:</strong> Çok fazla aykırı değer varsa ve veri kaybı kabul edilebilirse kullanılır.'
            },
            'cap': {
                'name': 'Sınırla (Cap)',
                'description': 'Aykırı değerleri belirlenen sınırlara (alt/üst) çeker, değerleri korur.<br><br><strong>✓ Avantajları:</strong> Veri kaybı olmaz, örneklem boyutu korunur.<br><strong>✗ Dezavantajları:</strong> Aykırı değerler hala mevcut, sadece sınırlanmış durumda.<br><strong>📌 Kullanım:</strong> Veri kaybından kaçınmak istendiğinde kullanılır.'
            }
        }
        
        action_info_text = action_info.get(action, {'name': action, 'description': 'İşlem bilgisi bulunamadı'})
        
        # Show only action info card (wide and short - horizontal layout, centered)
        card_id = f"action_card_{action}"
        col_left, col_center, col_right = st.columns([1, 3, 1])
        with col_center:
            st.markdown(f"""
            <div id="{card_id}" style="width: 100%; height: 180px; perspective: 1000px; margin: 10px 0;">
                <div class="action-card-inner" style="position: relative; width: 100%; height: 100%; text-align: center; transition: transform 0.6s; transform-style: preserve-3d;">
                    <div class="action-card-front" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 10px; display: flex; align-items: center; justify-content: center; padding: 15px 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                        <div style="text-align: center; width: 100%;">
                            <div style="font-size: 1.5em; font-weight: bold; margin-bottom: 5px;">📊 Bilgi Kartı</div>
                            <div style="font-size: 1.4em;">{action_info_text['name']}</div>
                        </div>
                    </div>
                    <div class="action-card-back" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 10px; display: flex; align-items: center; justify-content: center; padding: 15px 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); background: linear-gradient(135deg, #764ba2 0%, #667eea 100%); color: white; transform: rotateY(180deg); font-size: 0.9em; line-height: 1.5; text-align: center; overflow-y: auto;">
                        <div style="width: 100%;">
                            <div style="font-weight: bold; margin-bottom: 8px; font-size: 1.1em;">{action_info_text['name']}</div>
                            <div style="padding: 0 10px; font-size: 0.9em; line-height: 1.5;">{action_info_text['description']}</div>
                        </div>
                    </div>
                </div>
            </div>
            <style>
                #{card_id}:hover .action-card-inner {{
                    transform: rotateY(180deg);
                }}
            </style>
            """, unsafe_allow_html=True)
        
        # Store method as "detection_method_action"
        method = f"{detection_method}_{action}"
    else:
        method = None
        if all_columns_processed:
            st.info("ℹ️ Bütün aykırı değer içeren sütunlar işlenmiştir. Sonraki adıma geçebilirsiniz.")
        else:
            st.info("ℹ️ Önce sütun seçin")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Action buttons - Uygula butonu tüm satırı kaplar
    # Uygula butonu sadece yöntem seçildiğinde gösterilir (adım 1 mantığı)
    if selected_columns and method:
        if st.button("✅ Uygula", key="apply_outlier", type="primary", use_container_width=True):
                try:
                    df_processed = current_df.copy()
                    
                    # Parse method
                    method_parts = method.split('_')
                    if len(method_parts) >= 2:
                        detection_method = '_'.join(method_parts[:-1])
                        action = method_parts[-1]
                        
                        df_processed = apply_outlier_method_wrapper(df_processed, selected_columns, detection_method, action)
                        
                        # Save to session state
                        st.session_state.preprocessed_data = df_processed
                        
                        # Add to history
                        st.session_state.preprocessing_history.append({
                            'step': current_step,
                            'step_key': 'outlier',
                            'type': 'outlier',
                            'method': method,
                            'columns': selected_columns,
                            'timestamp': datetime.now().isoformat(),
                            'before_data': current_df.copy()
                        })
                        
                        st.success(f"✅ İşlem başarıyla uygulandı! {len(selected_columns)} sütun işlendi: {', '.join(selected_columns)}")
                        st.rerun()
                    else:
                        st.error("❌ Geçersiz yöntem formatı.")
                except Exception as e:
                    st.error(f"❌ Hata oluştu: {str(e)}")
                    logger.error(f"Error applying outlier method: {e}", exc_info=True)
        elif not selected_columns:
            st.warning("⚠️ Lütfen en az bir sütun seçin")
        elif not method:
            st.warning("⚠️ Lütfen bir yöntem seçin")
    
    # Show applied operations for this step with undo functionality - ALWAYS SHOW
    st.markdown("### 📋 Uygulanan İşlemler")
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
    if step_history:
        for i, operation in enumerate(step_history):
            col1, col2 = st.columns([4, 1])
            with col1:
                method_op = operation.get('method', 'Bilinmeyen')
                columns_op = operation.get('columns', [])
                
                # Parse method for display
                if columns_op:
                    method_parts = method_op.split('_')
                    if len(method_parts) >= 2:
                        detection_display = '_'.join(method_parts[:-1]).upper()
                        action_display = method_parts[-1].upper()
                        display_text = f"{', '.join(columns_op)} sütunları - {detection_display} ({action_display}) ile işlendi"
                    else:
                        display_text = f"{', '.join(columns_op)} sütunları - {method_op} ile işlendi"
                else:
                    display_text = f"Tüm sütunlar - {method_op} ile işlendi"
                
                # Create a styled card for each operation
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 5px 0;
                    color: white;
                '>
                    <span style='font-size: 1.2em; margin-right: 10px;'>✅</span>
                    {display_text}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("↶ Geri Al", key=f"undo_outlier_{i}", width='stretch'):
                    # Remove from history
                    operation_to_remove = step_history[i]
                    remove_method = operation_to_remove.get('method', '')
                    remove_columns = operation_to_remove.get('columns', [])
                    
                    # Remove from preprocessing_history
                    st.session_state.preprocessing_history.remove(operation_to_remove)
                    
                    # Rebuild the dataframe by reapplying ALL operations in order (all steps)
                    # Suppress INFO logs during rebuild
                    original_log_level = logger.level
                    logger.setLevel(logging.WARNING)
                    try:
                        df_rebuilt = st.session_state.original_data.copy()
                        
                        # Apply all operations in correct order: feature_engineering -> missing_values -> outlier -> encoding
                        for op in st.session_state.preprocessing_history:
                            op_type = op.get('type', '')
                            
                            if op_type == 'feature_engineering':
                                op_method = op.get('method', '')
                                if op_method == 'remove_duplicates':
                                    df_rebuilt = remove_duplicate_rows(df_rebuilt, keep=op.get('keep', 'first'))
                                elif op_method == 'drop_column':
                                    df_rebuilt = drop_columns(df_rebuilt, op.get('columns', []))
                                elif op_method == 'create_numeric_feature':
                                    df_rebuilt = create_numeric_feature(
                                        df_rebuilt,
                                        op.get('operation', 'add'),
                                        op.get('columns', []),
                                        op.get('new_column_name', '')
                                    )
                                elif op_method == 'create_datetime_feature':
                                    df_rebuilt = create_datetime_feature(
                                        df_rebuilt,
                                        op.get('columns', [])[0] if op.get('columns') else '',
                                        op.get('feature_type', 'year'),
                                        op.get('new_column_name', '')
                                    )
                                elif op_method == 'create_categorical_combination':
                                    df_rebuilt = create_categorical_combination(
                                        df_rebuilt,
                                        op.get('columns', []),
                                        op.get('new_column_name', ''),
                                        op.get('separator', '_')
                                    )
                            elif op_type == 'missing_values':
                                op_method_dict = op.get('method_dict')
                                if op_method_dict:
                                    # Handle dict method (numeric and categorical separately)
                                    if op_method_dict.get('numeric') and op_method_dict.get('numeric_cols'):
                                        df_rebuilt = apply_missing_values_method(
                                            df_rebuilt, 
                                            op_method_dict['numeric_cols'], 
                                            op_method_dict['numeric']
                                        )
                                    if op_method_dict.get('categorical') and op_method_dict.get('categorical_cols'):
                                        df_rebuilt = apply_missing_values_method(
                                            df_rebuilt, 
                                            op_method_dict['categorical_cols'], 
                                            op_method_dict['categorical']
                                        )
                                else:
                                    # Handle string method
                                    df_rebuilt = apply_missing_values_method(
                                        df_rebuilt, 
                                        op.get('columns', []), 
                                        op.get('method', '')
                                    )
                            elif op_type == 'outlier':
                                outlier_method = op.get('method', '')
                                method_parts = outlier_method.split('_')
                                if len(method_parts) >= 2:
                                    detection_method = '_'.join(method_parts[:-1])
                                    action = method_parts[-1]
                                    df_rebuilt = apply_outlier_method_wrapper(
                                        df_rebuilt,
                                        op.get('columns', []),
                                        detection_method,
                                        action
                                    )
                            elif op_type == 'encoding':
                                df_rebuilt = apply_encoding_method(
                                    df_rebuilt,
                                    op.get('columns', []),
                                    op.get('method', '')
                                )
                    finally:
                        # Restore original log level
                        logger.setLevel(original_log_level)
                    
                    # Update preprocessed data
                    st.session_state.preprocessed_data = df_rebuilt
                    
                    # Remove from applied_suggestion_ids if it was from LLM
                    if operation_to_remove.get('from_llm'):
                        suggestion_id = f"outlier_{remove_method}_{'_'.join(remove_columns) if remove_columns else 'all'}"
                        if suggestion_id in st.session_state.applied_suggestion_ids:
                            st.session_state.applied_suggestion_ids.remove(suggestion_id)
                    
                    st.success("✅ İşlem geri alındı!")
                    st.rerun()
    else:
        st.info("ℹ️ Henüz bu adımda işlem uygulanmadı.")
    
    # Add spacing before navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Action buttons - right aligned at bottom
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([3, 1, 1, 1])
    with col_nav2:
        if current_step > 1:
            if st.button("← Geri", key="prev_step_outlier", width='stretch'):
                st.session_state.preprocessing_step -= 1
                st.rerun()
    with col_nav3:
        # Atla butonu - son adımda (Summary) gösterilmez
        if current_step < len(steps):
            if st.button("Atla", key="skip_step_outlier", width='stretch'):
                st.session_state.preprocessing_step += 1
                st.rerun()
    with col_nav4:
        has_operation = check_step_has_operation(current_step)
        if st.button("İleri →", key="next_step_manual_outlier", disabled=not has_operation, width='stretch'):
            st.session_state.preprocessing_step += 1
            st.rerun()


# Render step content based on current step
if current_step == 1:
    render_feature_engineering_step(df)
elif current_step == 2:
    render_missing_values_step(df)
elif current_step == 3:
    render_outlier_step(df)
elif current_step == 4:
    render_encoding_step(df)
elif current_step == 5:
    render_scaling_step(df)
elif current_step == 6:
    st.info("Summary step - Implementation in progress...")
    
    # Show applied operations for this step - ALWAYS SHOW
    st.markdown("### 📋 Uygulanan İşlemler")
    step_history = [h for h in st.session_state.preprocessing_history if h.get('step') == current_step]
    if step_history:
        for idx, hist in enumerate(step_history):
            method_op = hist.get('method', '')
            columns_op = hist.get('columns', [])
            st.info(f"✅ {method_op} işlemi uygulandı")
    else:
        st.info("ℹ️ Henüz bu adımda işlem uygulanmadı.")
    
    # Add spacing before navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)

    # Action buttons - right aligned at bottom
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col2:
        if current_step > 1:
            if st.button("← Geri", key="prev_step_summary", width='stretch'):
                st.session_state.preprocessing_step -= 1
                st.rerun()
    with col3:
        # Atla butonu - son adımda (Summary) gösterilmez
        if current_step < len(steps):
            if st.button("Atla", key="skip_step_summary", width='stretch'):
                st.session_state.preprocessing_step += 1
                st.rerun()
    with col4:
        has_operation = check_step_has_operation(current_step)
        if st.button("İleri →", key="next_step_summary", disabled=not has_operation, width='stretch'):
            st.session_state.preprocessing_step += 1
            st.rerun()

# Navigation buttons are now in each step (Geri, Atla, İleri)

