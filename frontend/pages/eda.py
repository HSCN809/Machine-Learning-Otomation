"""Streamlit page for Exploratory Data Analysis (EDA)."""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import logging

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.modules.eda.eda_visualizer import (
    create_histogram,
    create_box_plot,
    create_correlation_matrix,
    create_missing_heatmap,
    create_scatter_plot,
    create_grouped_bar_chart,
    create_violin_plot,
    create_line_chart,
    create_area_chart,
    create_pie_chart,
    create_kde_plot,
    create_pair_plot,
    create_strip_plot,
    create_swarm_plot,
    create_ridge_plot
)
from backend.modules.eda.eda_analyzer import (
    calculate_correlations,
    detect_outliers,
    analyze_distributions
)
from backend.modules.eda.eda_llm_enhancer import suggest_visualizations
from backend.modules.data_upload.data_validator import get_data_summary

# Logger setup
logger = logging.getLogger(__name__)


def apply_visualization_suggestion(df: pd.DataFrame, suggestion: dict, library: str = 'plotly'):
    """
    LLM önerisine göre görselleştirmeyi oluştur ve session state'e kaydet.
    Görselleştirme tab'larda gösterilecek.
    
    Args:
        df: DataFrame
        suggestion: LLM önerisi dictionary
        library: Görselleştirme kütüphanesi
    """
    viz_type = suggestion.get('visualization_type', '').lower()
    column = suggestion.get('column', '')
    
    # Görselleştirme tipine göre mapping
    viz_type_normalized = viz_type.replace('_', ' ').strip()
    
    # Session state'te uygulanan görselleştirmeleri sakla
    if 'applied_visualizations' not in st.session_state:
        st.session_state.applied_visualizations = []
    
    # Uygulanan önerileri takip et (duplicate önleme)
    if 'applied_suggestion_ids' not in st.session_state:
        st.session_state.applied_suggestion_ids = []
    
    # Unique ID oluştur (viz_type + column kombinasyonu)
    suggestion_id = f"{viz_type_normalized}_{column or 'general'}"
    
    # Eğer bu öneri daha önce uygulandıysa, tekrar uygulama
    if suggestion_id in st.session_state.applied_suggestion_ids:
        st.warning(f"⚠️ Bu öneri zaten uygulandı: {viz_type_normalized} - {column or 'Genel'}")
        return
    
    try:
        visualization = None
        viz_info = None
        
        # Histogram
        if 'histogram' in viz_type_normalized:
            logger.debug(f"🔍 DEBUG Histogram: column={column}, column_in_df={column in df.columns if column else False}")
            if column and column in df.columns:
                try:
                    visualization = create_histogram(df, column, library=library)
                    if visualization:
                        logger.debug(f"✅ Histogram oluşturuldu: column={column}")
                        viz_info = {
                            'type': 'Histogram',
                            'column': column,
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ Histogram None döndü: column={column}")
                except Exception as e:
                    logger.debug(f"❌ Histogram hatası: {str(e)}")
            else:
                logger.debug(f"❌ Histogram: Column yok veya DataFrame'de yok")
        
        # Box Plot
        elif 'box plot' in viz_type_normalized:
            logger.debug(f"🔍 DEBUG Box Plot: column={column}, column_in_df={column in df.columns if column else False}")
            if column and column in df.columns:
                try:
                    visualization = create_box_plot(df, column, library=library)
                    if visualization:
                        logger.debug(f"✅ Box Plot oluşturuldu: column={column}")
                        viz_info = {
                            'type': 'Box Plot',
                            'column': column,
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ Box Plot None döndü: column={column}")
                except Exception as e:
                    logger.debug(f"❌ Box Plot hatası: {str(e)}")
            else:
                logger.debug(f"❌ Box Plot: Column yok veya DataFrame'de yok")
        
        # Scatter Plot
        elif 'scatter plot' in viz_type_normalized:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            logger.debug(f"🔍 DEBUG Scatter Plot: column={column}, numeric_cols={len(numeric_cols)}, cols={numeric_cols[:5]}")
            if len(numeric_cols) >= 2:
                x_col = column if (column and column in numeric_cols) else numeric_cols[0]
                y_col = None
                if column and column in numeric_cols:
                    other_cols = [c for c in numeric_cols if c != column]
                    if other_cols:
                        y_col = other_cols[0]
                else:
                    y_col = numeric_cols[1] if len(numeric_cols) > 1 else None
                
                logger.debug(f"🔍 Scatter Plot: x_col={x_col}, y_col={y_col}")
                if x_col and y_col:
                    try:
                        visualization = create_scatter_plot(df, x_col, y_col, library=library)
                        if visualization:
                            logger.debug(f"✅ Scatter Plot oluşturuldu: x={x_col}, y={y_col}")
                            viz_info = {
                                'type': 'Scatter Plot',
                                'columns': [x_col, y_col],
                                'visualization': visualization,
                                'library': library,
                                'suggestion': suggestion
                            }
                        else:
                            logger.debug(f"❌ Scatter Plot None döndü: x={x_col}, y={y_col}")
                    except Exception as e:
                        logger.debug(f"❌ Scatter Plot hatası: {str(e)}")
                        st.error(f"Scatter plot hatası: {str(e)}")
                else:
                    logger.debug(f"❌ Scatter Plot: x_col veya y_col None - x_col={x_col}, y_col={y_col}")
            else:
                logger.debug(f"❌ Scatter Plot: Yeterli numeric sütun yok (en az 2 gerekli, {len(numeric_cols)} var)")
        
        # Correlation Matrix / Correlation Heatmap
        elif 'correlation' in viz_type_normalized or 'heatmap' in viz_type_normalized:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            logger.debug(f"🔍 DEBUG Correlation/Heatmap: numeric_cols={len(numeric_cols)}, is_missing={'missing' in viz_type_normalized}")
            if len(numeric_cols) >= 2:
                if 'missing' in viz_type_normalized or 'eksik' in viz_type_normalized.lower():
                    try:
                        visualization = create_missing_heatmap(df, library=library)
                        if visualization:
                            logger.debug(f"✅ Missing Values Heatmap oluşturuldu")
                            viz_info = {
                                'type': 'Missing Values Heatmap',
                                'visualization': visualization,
                                'library': library,
                                'suggestion': suggestion
                            }
                        else:
                            logger.debug(f"❌ Missing Values Heatmap None döndü")
                    except Exception as e:
                        logger.debug(f"❌ Missing Values Heatmap hatası: {str(e)}")
                else:
                    try:
                        visualization = create_correlation_matrix(df, library=library)
                        if visualization:
                            logger.debug(f"✅ Correlation Matrix oluşturuldu")
                            viz_info = {
                                'type': 'Correlation Matrix',
                                'visualization': visualization,
                                'library': library,
                                'suggestion': suggestion
                            }
                        else:
                            logger.debug(f"❌ Correlation Matrix None döndü")
                    except Exception as e:
                        logger.debug(f"❌ Correlation Matrix hatası: {str(e)}")
            else:
                logger.debug(f"❌ Correlation/Heatmap: Yeterli numeric sütun yok (en az 2 gerekli, {len(numeric_cols)} var)")
        
        # Grouped Bar Chart
        elif 'grouped bar chart' in viz_type_normalized or 'grouped bar' in viz_type_normalized:
            # Kategorik sütunları bul
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            # Numeric sütunları da kontrol et (binary veya low cardinality)
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            low_cardinality_numeric = [c for c in numeric_cols if df[c].nunique() <= 10]
            
            logger.debug(f"🔍 DEBUG Grouped Bar Chart: column={column}, cat_cols={len(categorical_cols)}, low_card_numeric={len(low_cardinality_numeric)}")
            
            # Category column bul
            category_col = None
            if column and column in df.columns:
                category_col = column
            elif categorical_cols:
                category_col = categorical_cols[0]
            elif low_cardinality_numeric:
                category_col = low_cardinality_numeric[0]
            
            logger.debug(f"🔍 Grouped Bar Chart: category_col={category_col}")
            
            if category_col:
                # İkinci sütun bul (value_column)
                value_column = None
                if category_col in categorical_cols:
                    # Diğer kategorik sütunları dene
                    other_cat_cols = [c for c in categorical_cols if c != category_col]
                    if other_cat_cols:
                        value_column = other_cat_cols[0]
                    elif low_cardinality_numeric:
                        value_column = low_cardinality_numeric[0]
                elif category_col in low_cardinality_numeric:
                    # Eğer column numeric ise, kategorik sütun bul
                    if categorical_cols:
                        value_column = categorical_cols[0]
                    elif len(low_cardinality_numeric) > 1:
                        other_numeric = [c for c in low_cardinality_numeric if c != category_col]
                        if other_numeric:
                            value_column = other_numeric[0]
                
                logger.debug(f"🔍 Grouped Bar Chart: value_column={value_column}")
                
                try:
                    visualization = create_grouped_bar_chart(
                        df, 
                        category_column=category_col,
                        value_column=value_column,
                        library=library
                    )
                    if visualization:
                        logger.debug(f"✅ Grouped Bar Chart oluşturuldu: category={category_col}, value={value_column}")
                        viz_info = {
                            'type': 'Grouped Bar Chart',
                            'column': category_col,
                            'value_column': value_column,
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ Grouped Bar Chart None döndü: category={category_col}, value={value_column}")
                except Exception as e:
                    logger.debug(f"❌ Grouped Bar Chart hatası: {str(e)}")
                    st.error(f"Grouped bar chart hatası: {str(e)}")
            else:
                logger.debug(f"❌ Grouped Bar Chart: category_col bulunamadı")
        
        # Bar Chart (histogram olarak uygula)
        elif 'bar chart' in viz_type_normalized and 'grouped' not in viz_type_normalized:
            logger.debug(f"🔍 DEBUG Bar Chart: column={column}, column_in_df={column in df.columns if column else False}")
            if column and column in df.columns:
                try:
                    visualization = create_histogram(df, column, library=library)
                    if visualization:
                        logger.debug(f"✅ Bar Chart oluşturuldu: column={column}")
                        viz_info = {
                            'type': 'Bar Chart',
                            'column': column,
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ Bar Chart None döndü: column={column}")
                except Exception as e:
                    logger.debug(f"❌ Bar Chart hatası: {str(e)}")
            else:
                logger.debug(f"❌ Bar Chart: Column yok veya DataFrame'de yok")
        
        # Count Plot (histogram olarak uygula)
        elif 'count plot' in viz_type_normalized:
            logger.debug(f"🔍 DEBUG Count Plot: column={column}, column_in_df={column in df.columns if column else False}")
            if column and column in df.columns:
                try:
                    visualization = create_histogram(df, column, library=library)
                    if visualization:
                        logger.debug(f"✅ Count Plot oluşturuldu: column={column}")
                        viz_info = {
                            'type': 'Count Plot',
                            'column': column,
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ Count Plot None döndü: column={column}")
                except Exception as e:
                    logger.debug(f"❌ Count Plot hatası: {str(e)}")
            else:
                logger.debug(f"❌ Count Plot: Column yok veya DataFrame'de yok")
        
        # Violin Plot
        elif 'violin plot' in viz_type_normalized or 'violin' in viz_type_normalized:
            logger.debug(f"🔍 DEBUG Violin Plot: column={column}, column_in_df={column in df.columns if column else False}")
            if column and column in df.columns:
                try:
                    visualization = create_violin_plot(df, column, library=library)
                    if visualization:
                        logger.debug(f"✅ Violin Plot oluşturuldu: column={column}")
                        viz_info = {
                            'type': 'Violin Plot',
                            'column': column,
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ Violin Plot None döndü: column={column}")
                except Exception as e:
                    logger.debug(f"❌ Violin Plot hatası: {str(e)}")
            else:
                logger.debug(f"❌ Violin Plot: Column yok veya DataFrame'de yok")
        
        # Line Chart
        elif 'line chart' in viz_type_normalized or 'line plot' in viz_type_normalized:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            logger.debug(f"🔍 DEBUG Line Chart: column={column}, numeric_cols={len(numeric_cols)}")
            if column and column in df.columns:
                y_col = None
                if column in numeric_cols and len(numeric_cols) >= 2:
                    other_cols = [c for c in numeric_cols if c != column]
                    if other_cols:
                        y_col = other_cols[0]
                logger.debug(f"🔍 Line Chart: y_col={y_col}")
                try:
                    visualization = create_line_chart(df, column, y_col, library=library)
                    if visualization:
                        logger.debug(f"✅ Line Chart oluşturuldu: column={column}, y_col={y_col}")
                        viz_info = {
                            'type': 'Line Chart',
                            'column': column,
                            'y_column': y_col,
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ Line Chart None döndü: column={column}, y_col={y_col}")
                except Exception as e:
                    logger.debug(f"❌ Line Chart hatası: {str(e)}")
            else:
                logger.debug(f"❌ Line Chart: Column yok veya DataFrame'de yok")
        
        # Area Chart
        elif 'area chart' in viz_type_normalized or 'area plot' in viz_type_normalized:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            logger.debug(f"🔍 DEBUG Area Chart: column={column}, numeric_cols={len(numeric_cols)}")
            if column and column in df.columns:
                y_col = None
                if column in numeric_cols and len(numeric_cols) >= 2:
                    other_cols = [c for c in numeric_cols if c != column]
                    if other_cols:
                        y_col = other_cols[0]
                logger.debug(f"🔍 Area Chart: y_col={y_col}")
                try:
                    visualization = create_area_chart(df, column, y_col, library=library)
                    if visualization:
                        logger.debug(f"✅ Area Chart oluşturuldu: column={column}, y_col={y_col}")
                        viz_info = {
                            'type': 'Area Chart',
                            'column': column,
                            'y_column': y_col,
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ Area Chart None döndü: column={column}, y_col={y_col}")
                except Exception as e:
                    logger.debug(f"❌ Area Chart hatası: {str(e)}")
            else:
                logger.debug(f"❌ Area Chart: Column yok veya DataFrame'de yok")
        
        # Pie Chart
        elif 'pie chart' in viz_type_normalized or 'pie' in viz_type_normalized:
            logger.debug(f"🔍 DEBUG Pie Chart: column={column}, column_in_df={column in df.columns if column else False}")
            if column and column in df.columns:
                try:
                    visualization = create_pie_chart(df, column, library=library)
                    if visualization:
                        logger.debug(f"✅ Pie Chart oluşturuldu: column={column}")
                        viz_info = {
                            'type': 'Pie Chart',
                            'column': column,
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ Pie Chart None döndü: column={column}")
                except Exception as e:
                    logger.debug(f"❌ Pie Chart hatası: {str(e)}")
            else:
                logger.debug(f"❌ Pie Chart: Column yok veya DataFrame'de yok")
        
        # KDE Plot / Density Plot
        elif 'kde plot' in viz_type_normalized or 'density plot' in viz_type_normalized or 'kde' in viz_type_normalized:
            logger.debug(f"🔍 DEBUG KDE Plot: column={column}, column_in_df={column in df.columns if column else False}")
            if column and column in df.columns:
                try:
                    visualization = create_kde_plot(df, column, library=library)
                    if visualization:
                        logger.debug(f"✅ KDE Plot oluşturuldu: column={column}")
                        viz_info = {
                            'type': 'KDE Plot',
                            'column': column,
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ KDE Plot None döndü: column={column}")
                except Exception as e:
                    logger.debug(f"❌ KDE Plot hatası: {str(e)}")
            else:
                logger.debug(f"❌ KDE Plot: Column yok veya DataFrame'de yok")
        
        # Pair Plot
        elif 'pair plot' in viz_type_normalized or 'pairplot' in viz_type_normalized:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            logger.debug(f"🔍 DEBUG Pair Plot: numeric_cols={len(numeric_cols)}, cols={numeric_cols[:5]}")
            if len(numeric_cols) >= 2:
                try:
                    visualization = create_pair_plot(df, columns=numeric_cols[:5], library=library)
                    if visualization:
                        logger.debug(f"✅ Pair Plot oluşturuldu: columns={numeric_cols[:5]}")
                        viz_info = {
                            'type': 'Pair Plot',
                            'columns': numeric_cols[:5],
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ Pair Plot None döndü: columns={numeric_cols[:5]}")
                except Exception as e:
                    logger.debug(f"❌ Pair Plot hatası: {str(e)}")
            else:
                logger.debug(f"❌ Pair Plot: Yeterli numeric sütun yok (en az 2 gerekli, {len(numeric_cols)} var)")
        
        # Strip Plot
        elif 'strip plot' in viz_type_normalized or 'stripplot' in viz_type_normalized:
            logger.debug(f"🔍 DEBUG Strip Plot: column={column}, column_in_df={column in df.columns if column else False}")
            if column and column in df.columns:
                categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                y_col = None
                if column in categorical_cols:
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    if numeric_cols:
                        y_col = numeric_cols[0]
                logger.debug(f"🔍 Strip Plot: y_col={y_col}")
                try:
                    visualization = create_strip_plot(df, column, y_col, library=library)
                    if visualization:
                        logger.debug(f"✅ Strip Plot oluşturuldu: column={column}, y_col={y_col}")
                        viz_info = {
                            'type': 'Strip Plot',
                            'column': column,
                            'y_column': y_col,
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ Strip Plot None döndü: column={column}, y_col={y_col}")
                except Exception as e:
                    logger.debug(f"❌ Strip Plot hatası: {str(e)}")
            else:
                logger.debug(f"❌ Strip Plot: Column yok veya DataFrame'de yok")
        
        # Swarm Plot
        elif 'swarm plot' in viz_type_normalized or 'swarmplot' in viz_type_normalized:
            logger.debug(f"🔍 DEBUG Swarm Plot: column={column}, column_in_df={column in df.columns if column else False}")
            if column and column in df.columns:
                categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                y_col = None
                if column in categorical_cols:
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    if numeric_cols:
                        y_col = numeric_cols[0]
                logger.debug(f"🔍 Swarm Plot: y_col={y_col}")
                try:
                    visualization = create_swarm_plot(df, column, y_col, library=library)
                    if visualization:
                        logger.debug(f"✅ Swarm Plot oluşturuldu: column={column}, y_col={y_col}")
                        viz_info = {
                            'type': 'Swarm Plot',
                            'column': column,
                            'y_column': y_col,
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ Swarm Plot None döndü: column={column}, y_col={y_col}")
                except Exception as e:
                    logger.debug(f"❌ Swarm Plot hatası: {str(e)}")
            else:
                logger.debug(f"❌ Swarm Plot: Column yok veya DataFrame'de yok")
        
        # Ridge Plot
        elif 'ridge plot' in viz_type_normalized or 'ridge' in viz_type_normalized:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            logger.debug(f"🔍 DEBUG Ridge Plot: column={column}, numeric_cols={len(numeric_cols)}, categorical_cols={len(categorical_cols)}")
            if column and column in df.columns:
                value_col = column if column in numeric_cols else (numeric_cols[0] if numeric_cols else None)
                cat_col = column if column in categorical_cols else (categorical_cols[0] if categorical_cols else None)
                logger.debug(f"🔍 Ridge Plot: value_col={value_col}, cat_col={cat_col}")
                if value_col:
                    try:
                        visualization = create_ridge_plot(df, value_col, cat_col, library=library)
                        if visualization:
                            logger.debug(f"✅ Ridge Plot oluşturuldu: value_col={value_col}, cat_col={cat_col}")
                            viz_info = {
                                'type': 'Ridge Plot',
                                'value_column': value_col,
                                'category_column': cat_col,
                                'visualization': visualization,
                                'library': library,
                                'suggestion': suggestion
                            }
                        else:
                            logger.debug(f"❌ Ridge Plot None döndü: value_col={value_col}, cat_col={cat_col}")
                    except Exception as e:
                        logger.debug(f"❌ Ridge Plot hatası: {str(e)}")
                else:
                    logger.debug(f"❌ Ridge Plot: value_col bulunamadı")
            else:
                logger.debug(f"❌ Ridge Plot: Column yok veya DataFrame'de yok")
        
        # Diğer görselleştirmeler için genel yaklaşım
        else:
            logger.debug(f"🔍 DEBUG Diğer (Fallback): viz_type={viz_type_normalized}, column={column}")
            if column and column in df.columns:
                try:
                    visualization = create_histogram(df, column, library=library)
                    if visualization:
                        logger.debug(f"✅ Fallback Histogram oluşturuldu: column={column}")
                        viz_info = {
                            'type': viz_type_normalized.title(),
                            'column': column,
                            'visualization': visualization,
                            'library': library,
                            'suggestion': suggestion
                        }
                    else:
                        logger.debug(f"❌ Fallback Histogram None döndü: column={column}")
                except Exception as e:
                    logger.debug(f"❌ Fallback Histogram hatası: {str(e)}")
            else:
                logger.debug(f"❌ Fallback: Column yok veya DataFrame'de yok")
        
        # Session state'e kaydet
        if viz_info:
            # Duplicate önleme: ID'yi kaydet
            st.session_state.applied_suggestion_ids.append(suggestion_id)
            st.session_state.applied_visualizations.append(viz_info)
            st.success(f"✅ {viz_info['type']} oluşturuldu! Tab'larda görüntülenebilir.")
            st.rerun()
        else:
            # Debug bilgisi
            debug_info = f"Viz type: {viz_type_normalized}, Column: {column or 'None'}"
            if 'scatter' in viz_type_normalized:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                debug_info += f", Numeric cols: {len(numeric_cols)}"
            elif 'grouped bar' in viz_type_normalized:
                categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                debug_info += f", Categorical cols: {len(categorical_cols)}"
            st.warning(f"⚠️ Görselleştirme oluşturulamadı: {viz_type_normalized}")
            logger.debug(debug_info)
    
    except Exception as e:
        st.error(f"❌ Hata: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


# Page configuration
st.set_page_config(
    page_title="Keşifsel Veri Analizi (EDA)",
    page_icon="🔍",
    layout="wide"
)

# Hide default page navigation
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Update session state for current page
st.session_state.page = 'EDA'

st.title("🔍 Keşifsel Veri Analizi (EDA)")
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
    
    if st.button("🔍 EDA", width='stretch', type="primary"):
        pass  # Already on this page
    
    if st.button("🔧 Veri Ön İşleme", width='stretch'):
        st.switch_page("pages/data_preprocessing.py")
    
    st.markdown("---")
    st.markdown("### ⚙️ Ayarlar")
    
    # Visualization library selection
    viz_library = st.selectbox(
        "📚 Görselleştirme Kütüphanesi",
        options=['plotly', 'matplotlib', 'seaborn', 'streamlit'],
        index=0,
        help="Görselleştirmeler için kullanılacak kütüphane"
    )
    
    # LLM suggestions toggle
    llm_enabled = st.toggle(
        "🤖 LLM Önerileri",
        value=True,
        help="LLM ile görselleştirme önerileri"
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
    EDA modülü, yüklenen verilerinizi görselleştirip analiz etmenizi sağlar. Histogram, box plot, korelasyon matrisi ve daha fazlası.
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
df = st.session_state.get('uploaded_data')

if df is None or df.empty:
    st.error("❌ Veri bulunamadı veya boş!")
    st.stop()

# Store settings in session state
st.session_state.eda_viz_library = viz_library
st.session_state.eda_llm_enabled = llm_enabled

# Main content area
st.success(f"✅ {len(df):,} satır × {len(df.columns)} sütun veri analiz ediliyor")

# Get column types
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

# Get data summary for LLM
data_summary = get_data_summary(df)

# Determine analysis level based on dataset characteristics
def determine_analysis_level(df, numeric_cols, categorical_cols, data_summary):
    """
    Veri setinin özelliklerine göre analiz seviyesini belirle.
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    num_numeric = len(numeric_cols)
    num_categorical = len(categorical_cols)
    missing_pct = data_summary.get('missing_values', {}).get('missing_percentage', 0)
    
    # Gelişmiş: Çok fazla veri, çok fazla sütun, karmaşık yapı
    if total_rows > 10000 or total_cols > 20 or (num_numeric > 10 and num_categorical > 5):
        return 'Gelişmiş'
    # Orta: Orta seviye karmaşıklık
    elif total_rows > 1000 or total_cols > 10 or missing_pct > 10:
        return 'Orta'
    # Temel: Küçük ve basit veri setleri
    else:
        return 'Temel'

# Auto-determine analysis level (değişkenler tanımlandıktan sonra)
analysis_level = determine_analysis_level(df, numeric_cols, categorical_cols, data_summary)

# LLM Visualization Suggestions (if enabled)
if llm_enabled:
    with st.expander("🤖 LLM Görselleştirme Önerileri", expanded=False):
        # Veri hash'i oluştur (veri değiştiğinde önerileri sıfırlamak için)
        import hashlib
        data_hash = hashlib.md5(str(df.shape).encode() + str(df.columns.tolist()).encode()).hexdigest()
        
        # Initialize suggestions in session state
        if 'eda_suggestions' not in st.session_state:
            st.session_state.eda_suggestions = []
        if 'eda_suggestion_index' not in st.session_state:
            st.session_state.eda_suggestion_index = 0
        if 'eda_data_hash' not in st.session_state:
            st.session_state.eda_data_hash = None
        
        # Veri değiştiyse önerileri sıfırla
        if st.session_state.eda_data_hash != data_hash:
            st.session_state.eda_suggestions = []
            st.session_state.eda_suggestion_index = 0
            st.session_state.eda_data_hash = data_hash
        
        # Button to get suggestions
        if st.button("💡 Önerileri Al", key="get_viz_suggestions"):
            # Yeni öneriler alındığında uygulanmış öneri ID'lerini temizle (grafik üretme hakkını yenile)
            if 'applied_suggestion_ids' in st.session_state:
                st.session_state.applied_suggestion_ids = []
            
            with st.spinner("🤖 LLM önerileri oluşturuluyor..."):
                suggestions_result = suggest_visualizations(
                    data_summary,
                    numeric_cols,
                    categorical_cols,
                    analysis_level
                )
                
                if suggestions_result.get('error'):
                    st.error(f"❌ LLM önerisi alınamadı: {suggestions_result.get('error')}")
                    st.session_state.eda_suggestions = []
                else:
                    suggestions = suggestions_result.get('suggestions', [])
                    if suggestions:
                        # Her öneriye analiz seviyesi ekle (eğer LLM'den gelmediyse)
                        for suggestion in suggestions:
                            if 'analysis_level' not in suggestion or not suggestion.get('analysis_level'):
                                # LLM'den gelmediyse, görselleştirme tipine göre otomatik belirle
                                viz_type = suggestion.get('visualization_type', '').lower()
                                if any(x in viz_type for x in ['histogram', 'bar chart', 'pie chart', 'count plot']):
                                    suggestion['analysis_level'] = 'Temel'
                                elif any(x in viz_type for x in ['box plot', 'scatter plot', 'line plot', 'distribution']):
                                    suggestion['analysis_level'] = 'Orta'
                                elif any(x in viz_type for x in ['correlation', 'heatmap', 'pair plot', 'violin plot', 'density']):
                                    suggestion['analysis_level'] = 'Gelişmiş'
                                else:
                                    suggestion['analysis_level'] = analysis_level  # Fallback
                        
                        # En az 8 öneri garantisi
                        if len(suggestions) < 8:
                            st.warning(f"⚠️ Sadece {len(suggestions)} öneri alındı. En az 8 öneri gereklidir. Lütfen tekrar deneyin.")
                        
                        st.session_state.eda_suggestions = suggestions
                        st.session_state.eda_suggestion_index = 0
                        st.session_state.eda_data_hash = data_hash  # Veri hash'ini kaydet
                        st.success(f"✅ {len(suggestions)} öneri alındı (Analiz Seviyesi: {analysis_level})")
                        st.rerun()
                    else:
                        st.info("ℹ️ Öneri bulunamadı.")
                        st.session_state.eda_suggestions = []
        
        # Display suggestions in carousel format
        if st.session_state.eda_suggestions:
            suggestions = st.session_state.eda_suggestions
            current_index = st.session_state.eda_suggestion_index
            
            st.markdown(f"<div style='text-align: center; margin: 10px 0;'><strong>{len(suggestions)} öneri sunuldu</strong> | <em>Öneri {current_index + 1}/{len(suggestions)}</em></div>", unsafe_allow_html=True)
            
            # Navigation buttons and current suggestion
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                if st.button("◀️ Önceki", key="prev_suggestion", disabled=(current_index == 0), width='stretch'):
                    st.session_state.eda_suggestion_index = max(0, current_index - 1)
                    st.rerun()
            
            with col2:
                # Current suggestion - kart tasarımı
                suggestion = suggestions[current_index]
                viz_type = suggestion.get('visualization_type', 'Bilinmeyen')
                column = suggestion.get('column', 'Genel')
                reason = suggestion.get('reason', '')
                
                # HTML tag'lerini temizle
                if reason:
                    import html as html_module
                    import re
                    try:
                        reason = html_module.unescape(reason)
                    except:
                        pass
                    reason = re.sub(r'<[^>]+>', '', reason, flags=re.DOTALL | re.IGNORECASE)
                    reason = ' '.join(reason.split()).strip()
                
                # Viz type ve column'u temizle
                # LLM'den gelen ismi normalize et (sadece İngilizce gösterilecek)
                viz_type_raw = str(viz_type).strip()
                viz_type_clean = viz_type_raw.replace('_', ' ').title()
                
                column_clean = str(column) if column and column != 'Genel' and column else ''
                
                # Analiz seviyesi badge'i
                analysis_level_badge = suggestion.get('analysis_level', 'Temel')
                level_colors = {
                    'Temel': '#4CAF50',  # Yeşil
                    'Orta': '#FF9800',   # Turuncu
                    'Gelişmiş': '#F44336'  # Kırmızı
                }
                level_color = level_colors.get(analysis_level_badge, '#4CAF50')
                
                # Reason'ı güvenli hale getir
                import html as html_module
                reason_safe = html_module.escape(reason) if reason else 'Açıklama bulunamadı.'
                viz_type_safe = html_module.escape(viz_type_clean)
                analysis_level_safe = html_module.escape(analysis_level_badge)
                
                # Sütun adına göre farklı kart tasarımları
                if column_clean:
                    # Sütun adı olan öneriler için kart tasarımı
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
                                📊 {viz_type_safe}
                            </h3>
                            <span style='
                                background: {level_color};
                                color: white;
                                padding: 5px 12px;
                                border-radius: 20px;
                                font-size: 0.75em;
                                font-weight: bold;
                                text-transform: uppercase;
                            '>
                                {analysis_level_safe}
                            </span>
                        </div>
                        <div style='
                            background: rgba(255, 255, 255, 0.15);
                            padding: 10px 15px;
                            border-radius: 8px;
                            margin-bottom: 15px;
                            display: inline-block;
                        '>
                            <span style='color: #f0f0f0; font-size: 0.95em;'>
                                <strong>📍 Sütun:</strong> {html_module.escape(column_clean)}
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
                    # Sütun adı olmayan öneriler için aynı renk kart tasarımı
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
                                📊 {viz_type_safe}
                            </h3>
                            <span style='
                                background: {level_color};
                                color: white;
                                padding: 5px 12px;
                                border-radius: 20px;
                                font-size: 0.75em;
                                font-weight: bold;
                                text-transform: uppercase;
                            '>
                                {analysis_level_safe}
                            </span>
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
                
                # Uygula butonu (duplicate önleme)
                apply_button_key = f"apply_suggestion_{current_index}"
                
                # Öneri ID'sini oluştur (duplicate kontrolü için)
                viz_type_raw = str(suggestion.get('visualization_type', '')).lower().replace('_', ' ').strip()
                column_raw = suggestion.get('column', '')
                suggestion_id = f"{viz_type_raw}_{column_raw or 'general'}"
                
                # Eğer bu öneri zaten uygulandıysa, butonu devre dışı bırak
                is_applied = 'applied_suggestion_ids' in st.session_state and suggestion_id in st.session_state.applied_suggestion_ids
                
                if is_applied:
                    st.button("✅ Zaten Uygulandı", key=apply_button_key, width='stretch', disabled=True)
                else:
                    if st.button("✅ Uygula", key=apply_button_key, width='stretch', type="primary"):
                        # Görselleştirmeyi oluştur
                        apply_visualization_suggestion(df, suggestion, viz_library)
            
            with col3:
                if st.button("Sonraki ▶️", key="next_suggestion", disabled=(current_index == len(suggestions) - 1), width='stretch'):
                    st.session_state.eda_suggestion_index = min(len(suggestions) - 1, current_index + 1)
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

# Create tabs for different analysis sections
tab1, tab2, tab3, tab4 = st.tabs(["📊 Temel Görselleştirmeler", "📈 Sayısal Analizler", "📋 Kategorik Analizler", "🔗 İlişki Analizleri"])

# Session state'te görüntüleme modunu kontrol et
if 'show_manual_viz_tab1' not in st.session_state:
    st.session_state.show_manual_viz_tab1 = False
if 'show_manual_viz_tab2' not in st.session_state:
    st.session_state.show_manual_viz_tab2 = False
if 'show_manual_viz_tab3' not in st.session_state:
    st.session_state.show_manual_viz_tab3 = False
if 'show_manual_viz_tab4' not in st.session_state:
    st.session_state.show_manual_viz_tab4 = False

with tab1:
    st.subheader("Temel Görselleştirmeler")
    
    # LLM görselleştirmeleri var mı kontrol et
    has_llm_viz = 'applied_visualizations' in st.session_state and st.session_state.applied_visualizations
    has_relevant_llm = False
    if has_llm_viz:
        for viz_info in st.session_state.applied_visualizations:
            if viz_info.get('type') in ['Missing Values Heatmap', 'Correlation Matrix']:
                has_relevant_llm = True
                break
    
    # Toggle butonu (LLM görselleştirmesi varsa göster)
    if has_relevant_llm:
        col_toggle1, _ = st.columns([1, 4])
        with col_toggle1:
            if st.button("🔄 Manuel Grafik Oluşturma", key="toggle_manual_tab1", width='stretch'):
                st.session_state.show_manual_viz_tab1 = not st.session_state.show_manual_viz_tab1
                st.rerun()
    
    # LLM görselleştirmeleri göster (manuel mod kapalıysa)
    if not st.session_state.show_manual_viz_tab1 and has_relevant_llm:
        applied_viz = st.session_state.applied_visualizations
        for idx, viz_info in enumerate(applied_viz):
            viz_type = viz_info.get('type', '')
            
            if viz_type in ['Missing Values Heatmap', 'Correlation Matrix']:
                st.markdown(f"### 🤖 LLM Önerisi: {viz_type}")
                visualization = viz_info.get('visualization')
                library = viz_info.get('library', viz_library)
                
                if visualization:
                    if library == 'plotly':
                        st.plotly_chart(visualization, width='stretch', key=f"applied_viz_{idx}_{viz_type}")
                    elif library in ['matplotlib', 'seaborn']:
                        st.pyplot(visualization)
                    elif library == 'streamlit':
                        if hasattr(visualization, 'plot'):
                            st.plotly_chart(visualization, width='stretch', key=f"applied_viz_{idx}_{viz_type}")
                        else:
                            st.dataframe(visualization)
                st.markdown("---")
    
    # Manuel görselleştirmeler (LLM modu kapalıysa veya LLM görselleştirmesi yoksa)
    if st.session_state.show_manual_viz_tab1 or not has_relevant_llm:
        # Missing values heatmap
        st.markdown("### 🔍 Eksik Değerler Haritası")
        missing_viz = create_missing_heatmap(df, library=viz_library)
        if missing_viz:
            if viz_library == 'plotly':
                st.plotly_chart(missing_viz, width='stretch', key="missing_heatmap_default")
            elif viz_library in ['matplotlib', 'seaborn']:
                st.pyplot(missing_viz)
            elif viz_library == 'streamlit':
                st.dataframe(missing_viz)
        else:
            st.info("Eksik değer bulunamadı veya görselleştirme oluşturulamadı.")
        
        # Correlation matrix
        if len(numeric_cols) >= 2:
            st.markdown("### 🔗 Korelasyon Matrisi")
            corr_viz = create_correlation_matrix(df, library=viz_library)
            if corr_viz:
                if viz_library == 'plotly':
                    st.plotly_chart(corr_viz, width='stretch', key="correlation_matrix_default")
                elif viz_library in ['matplotlib', 'seaborn']:
                    st.pyplot(corr_viz)
                elif viz_library == 'streamlit':
                    st.dataframe(corr_viz)
            else:
                st.info("Korelasyon matrisi oluşturulamadı.")

with tab2:
    st.subheader("Sayısal Sütun Analizleri")
    
    # LLM görselleştirmeleri var mı kontrol et
    has_llm_viz = 'applied_visualizations' in st.session_state and st.session_state.applied_visualizations
    has_relevant_llm = False
    if has_llm_viz:
        for viz_info in st.session_state.applied_visualizations:
            if viz_info.get('type') in ['Histogram', 'Box Plot', 'Bar Chart', 'Count Plot']:
                has_relevant_llm = True
                break
    
    # Toggle butonu (LLM görselleştirmesi varsa göster)
    if has_relevant_llm:
        col_toggle2, _ = st.columns([1, 4])
        with col_toggle2:
            if st.button("🔄 Manuel Grafik Oluşturma", key="toggle_manual_tab2", width='stretch'):
                st.session_state.show_manual_viz_tab2 = not st.session_state.show_manual_viz_tab2
                st.rerun()
    
    # LLM görselleştirmeleri göster (manuel mod kapalıysa)
    if not st.session_state.show_manual_viz_tab2 and has_relevant_llm:
        applied_viz = st.session_state.applied_visualizations
        for idx, viz_info in enumerate(applied_viz):
            viz_type = viz_info.get('type', '')
            
            if viz_type in ['Histogram', 'Box Plot', 'Bar Chart', 'Count Plot']:
                column = viz_info.get('column', '')
                st.markdown(f"### 🤖 LLM Önerisi: {viz_type} - {column}")
                visualization = viz_info.get('visualization')
                library = viz_info.get('library', viz_library)
                
                if visualization:
                    if library == 'plotly':
                        st.plotly_chart(visualization, width='stretch', key=f"applied_viz_{idx}_{viz_type}_{column}")
                    elif library in ['matplotlib', 'seaborn']:
                        st.pyplot(visualization)
                    elif library == 'streamlit':
                        if hasattr(visualization, 'plot'):
                            st.plotly_chart(visualization, width='stretch', key=f"applied_viz_{idx}_{viz_type}_{column}")
                        else:
                            st.dataframe(visualization)
                st.markdown("---")
    
    # Manuel görselleştirmeler (LLM modu kapalıysa veya LLM görselleştirmesi yoksa)
    if st.session_state.show_manual_viz_tab2 or not has_relevant_llm:
        if len(numeric_cols) == 0:
            st.info("ℹ️ Sayısal sütun bulunamadı.")
        else:
            selected_numeric_col = st.selectbox(
                "📊 Analiz Edilecek Sayısal Sütun Seçin",
                options=numeric_cols,
                key="numeric_col_selector"
            )
            
            if selected_numeric_col:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📊 Histogram")
                    hist_viz = create_histogram(df, selected_numeric_col, library=viz_library)
                    if hist_viz:
                        if viz_library == 'plotly':
                            st.plotly_chart(hist_viz, width='stretch', key=f"histogram_{selected_numeric_col}")
                        elif viz_library in ['matplotlib', 'seaborn']:
                            st.pyplot(hist_viz)
                        elif viz_library == 'streamlit':
                            st.bar_chart(hist_viz.value_counts())
                
                with col2:
                    st.markdown("#### 📦 Box Plot")
                    box_viz = create_box_plot(df, selected_numeric_col, library=viz_library)
                    if box_viz:
                        if viz_library == 'plotly':
                            st.plotly_chart(box_viz, width='stretch', key=f"boxplot_{selected_numeric_col}")
                        elif viz_library in ['matplotlib', 'seaborn']:
                            st.pyplot(box_viz)
                        elif viz_library == 'streamlit':
                            st.line_chart(box_viz)
                
                
                # Distribution analysis
                st.markdown("#### 📈 Dağılım Analizi")
                dist_analysis = analyze_distributions(df, selected_numeric_col)
                if dist_analysis:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Ortalama", f"{dist_analysis.get('mean', 0):.2f}")
                    with col2:
                        st.metric("Medyan", f"{dist_analysis.get('median', 0):.2f}")
                    with col3:
                        st.metric("Standart Sapma", f"{dist_analysis.get('std', 0):.2f}")
                    with col4:
                        st.metric("Çarpıklık", f"{dist_analysis.get('skewness', 0):.2f}")
                    
                    # Normality test
                    is_normal = dist_analysis.get('is_normal', False)
                    if is_normal:
                        st.success(f"✅ Normal dağılım (p-value: {dist_analysis.get('normality_p_value', 0):.4f})")
                    else:
                        st.warning(f"⚠️ Normal dağılım değil (p-value: {dist_analysis.get('normality_p_value', 0):.4f})")
                
                # Outlier detection
                st.markdown("#### 🎯 Outlier Tespiti")
                outlier_analysis = detect_outliers(df, selected_numeric_col, method='iqr')
                if outlier_analysis:
                    st.metric("Outlier Sayısı", f"{outlier_analysis.get('outlier_count', 0)}")
                    st.metric("Outlier Yüzdesi", f"%{outlier_analysis.get('outlier_percentage', 0):.2f}")
                    if outlier_analysis.get('outlier_count', 0) > 0:
                        st.warning(f"⚠️ {outlier_analysis.get('outlier_count', 0)} adet outlier tespit edildi.")

with tab3:
    st.subheader("Kategorik Sütun Analizleri")
    
    if len(categorical_cols) == 0:
        st.info("ℹ️ Kategorik sütun bulunamadı.")
    else:
        selected_cat_col = st.selectbox(
            "📋 Analiz Edilecek Kategorik Sütun Seçin",
            options=categorical_cols,
            key="categorical_col_selector"
        )
        
        if selected_cat_col:
            # Value counts
            st.markdown("#### 📊 Değer Dağılımı")
            value_counts = df[selected_cat_col].value_counts()
            
            if viz_library == 'plotly':
                try:
                    import plotly.express as px
                    fig = px.bar(
                        x=value_counts.index,
                        y=value_counts.values,
                        title=f'{selected_cat_col} Değer Dağılımı',
                        labels={'x': selected_cat_col, 'y': 'Sayı'}
                    )
                    fig.update_layout(height=400, template='plotly_white')
                    st.plotly_chart(fig, width='stretch', key=f"categorical_bar_{selected_cat_col}")
                except:
                    st.bar_chart(value_counts)
            elif viz_library == 'streamlit':
                st.bar_chart(value_counts)
            else:
                # For matplotlib and seaborn
                try:
                    import matplotlib.pyplot as plt
                    if viz_library == 'seaborn':
                        import seaborn as sns
                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.countplot(data=df, x=selected_cat_col, ax=ax)
                        ax.set_title(f'{selected_cat_col} Değer Dağılımı', fontsize=14, fontweight='bold')
                        plt.xticks(rotation=45, ha='right')
                        plt.tight_layout()
                        st.pyplot(fig)
                    else:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        value_counts.plot(kind='bar', ax=ax)
                        ax.set_title(f'{selected_cat_col} Değer Dağılımı', fontsize=14, fontweight='bold')
                        ax.set_xlabel(selected_cat_col, fontsize=12)
                        ax.set_ylabel('Sayı', fontsize=12)
                        plt.xticks(rotation=45, ha='right')
                        plt.tight_layout()
                        st.pyplot(fig)
                except:
                    st.bar_chart(value_counts)
            
            # Statistics
            st.markdown("#### 📈 İstatistikler")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Benzersiz Değer", df[selected_cat_col].nunique())
            with col2:
                st.metric("Toplam Değer", len(df[selected_cat_col]))
            with col3:
                missing_count = df[selected_cat_col].isnull().sum()
                st.metric("Eksik Değer", f"{missing_count} (%{(missing_count/len(df)*100):.1f})")
            
            # Top values
            st.markdown("#### 🔝 En Sık Görülen Değerler")
            st.dataframe(
                pd.DataFrame({
                    'Değer': value_counts.head(10).index,
                    'Sayı': value_counts.head(10).values,
                    'Yüzde (%)': (value_counts.head(10).values / len(df) * 100).round(2)
                }),
                width='stretch'
            )

with tab4:
    st.subheader("İlişki Analizleri")
    
    # LLM görselleştirmeleri var mı kontrol et
    has_llm_viz = 'applied_visualizations' in st.session_state and st.session_state.applied_visualizations
    has_relevant_llm = False
    if has_llm_viz:
        for viz_info in st.session_state.applied_visualizations:
            if viz_info.get('type') == 'Scatter Plot':
                has_relevant_llm = True
                break
    
    # Toggle butonu (LLM görselleştirmesi varsa göster)
    if has_relevant_llm:
        col_toggle4, _ = st.columns([1, 4])
        with col_toggle4:
            if st.button("🔄 Manuel Grafik Oluşturma", key="toggle_manual_tab4", width='stretch'):
                st.session_state.show_manual_viz_tab4 = not st.session_state.show_manual_viz_tab4
                st.rerun()
    
    # LLM görselleştirmeleri göster (manuel mod kapalıysa)
    if not st.session_state.show_manual_viz_tab4 and has_relevant_llm:
        applied_viz = st.session_state.applied_visualizations
        for idx, viz_info in enumerate(applied_viz):
            viz_type = viz_info.get('type', '')
            
            if viz_type == 'Scatter Plot':
                columns = viz_info.get('columns', [])
                st.markdown(f"### 🤖 LLM Önerisi: {viz_type} - {columns[0]} vs {columns[1] if len(columns) > 1 else ''}")
                visualization = viz_info.get('visualization')
                library = viz_info.get('library', viz_library)
                
                if visualization:
                    if library == 'plotly':
                        st.plotly_chart(visualization, width='stretch', key=f"applied_viz_{idx}_{viz_type}_{'_'.join(columns)}")
                    elif library in ['matplotlib', 'seaborn']:
                        st.pyplot(visualization)
                    elif library == 'streamlit':
                        if hasattr(visualization, 'plot'):
                            st.plotly_chart(visualization, width='stretch', key=f"applied_viz_{idx}_{viz_type}_{'_'.join(columns)}")
                        else:
                            st.dataframe(visualization)
                st.markdown("---")
    
    # Manuel görselleştirmeler (LLM modu kapalıysa veya LLM görselleştirmesi yoksa)
    if st.session_state.show_manual_viz_tab4 or not has_relevant_llm:
        if len(numeric_cols) < 2:
            st.info("ℹ️ İlişki analizi için en az 2 sayısal sütun gereklidir.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                x_col = st.selectbox("X Ekseni Sütunu", options=numeric_cols, key="scatter_x")
            
            with col2:
                y_col = st.selectbox("Y Ekseni Sütunu", options=numeric_cols, key="scatter_y")
            
            if x_col and y_col and x_col != y_col:
                # Scatter plot
                st.markdown("### 📊 Scatter Plot")
                color_col = None
                if len(categorical_cols) > 0:
                    use_color = st.checkbox("Kategorik sütun ile renklendir", key="use_color_scatter")
                    if use_color:
                        color_col = st.selectbox("Renk Sütunu", options=categorical_cols, key="scatter_color")
                
                scatter_viz = create_scatter_plot(df, x_col, y_col, library=viz_library, color_column=color_col)
                if scatter_viz:
                    if viz_library == 'plotly':
                        st.plotly_chart(scatter_viz, width='stretch', key=f"scatter_{x_col}_{y_col}")
                    elif viz_library in ['matplotlib', 'seaborn']:
                        st.pyplot(scatter_viz)
                
                # Correlation
                st.markdown("### 🔗 Korelasyon")
                corr_value = df[x_col].corr(df[y_col])
                st.metric("Pearson Korelasyon", f"{corr_value:.4f}")
                
                if abs(corr_value) > 0.7:
                    st.success("✅ Güçlü korelasyon")
                elif abs(corr_value) > 0.3:
                    st.info("ℹ️ Orta korelasyon")
                else:
                    st.warning("⚠️ Zayıf korelasyon")

