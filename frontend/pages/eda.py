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
# from backend.modules.eda.eda_llm_enhancer import suggest_visualizations  # REMOVED (temporarily disabled)
from backend.modules.data_upload.data_validator import get_data_summary
from backend.modules.data_upload.data_analyzer import (
    get_numeric_statistics,
    get_categorical_statistics,
    get_categorical_value_distribution,
    get_column_cardinality_info,
    get_data_types_summary
)
import io

# Logger setup
logger = logging.getLogger(__name__)


def export_visualization(visualization, viz_type: str, library: str = 'plotly', format: str = 'png'):
    """
    Export visualization to file format.
    
    Args:
        visualization: Visualization object
        viz_type: Type of visualization
        library: Library used ('plotly', 'matplotlib', 'seaborn')
        format: Export format ('png', 'pdf', 'html')
        
    Returns:
        Bytes data for download
    """
    try:
        if library == 'plotly':
            if format == 'png':
                return visualization.to_image(format='png')
            elif format == 'pdf':
                return visualization.to_image(format='pdf')
            elif format == 'html':
                return visualization.to_html().encode('utf-8')
        elif library in ['matplotlib', 'seaborn']:
            import matplotlib.pyplot as plt
            buf = io.BytesIO()
            if format == 'png':
                visualization.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            elif format == 'pdf':
                visualization.savefig(buf, format='pdf', bbox_inches='tight')
            buf.seek(0)
            return buf.read()
    except Exception as e:
        logger.error(f"Export error: {e}")
        return None


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
            logger.debug(f"🔍 DEBUG Correlation/Heatmap: numeric_cols={len(numeric_cols)}")
            if len(numeric_cols) >= 2:
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
    
    /* Streamlit'in sayfa navigasyon butonlarını gizle */
    button[data-testid="baseButton-secondary"] {
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
    
    if st.button("🤖 Model Seçimi", width='stretch'):
        st.switch_page("pages/model_selection.py")
    
    st.markdown("---")
    st.markdown("### ⚙️ Ayarlar")
    
    # Visualization library selection
    viz_library = st.selectbox(
        "📚 Görselleştirme Kütüphanesi",
        options=['plotly', 'matplotlib', 'seaborn', 'streamlit'],
        index=0,
        help="Görselleştirmeler için kullanılacak kütüphane"
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
    
    # Orta: Çok fazla veri, çok fazla sütun, karmaşık yapı
    if total_rows > 10000 or total_cols > 20 or (num_numeric > 10 and num_categorical > 5):
        return 'Orta'
    # Orta: Orta seviye karmaşıklık
    elif total_rows > 1000 or total_cols > 10 or missing_pct > 10:
        return 'Orta'
    # Temel: Küçük ve basit veri setleri
    else:
        return 'Temel'

# Auto-determine analysis level (değişkenler tanımlandıktan sonra)
analysis_level = determine_analysis_level(df, numeric_cols, categorical_cols, data_summary)

# LLM Visualization Suggestions - REMOVED (temporarily disabled)

# Create tabs for different analysis sections
tab0, tab1, tab2, tab3, tab4 = st.tabs(["📊 Özet Dashboard", "📊 Temel Görselleştirmeler", "📈 Sayısal Analizler", "📋 Kategorik Analizler", "🔗 İlişki Analizleri"])

# Session state'te görüntüleme modunu kontrol et
if 'show_manual_viz_tab1' not in st.session_state:
    st.session_state.show_manual_viz_tab1 = False
if 'show_manual_viz_tab2' not in st.session_state:
    st.session_state.show_manual_viz_tab2 = False
if 'show_manual_viz_tab3' not in st.session_state:
    st.session_state.show_manual_viz_tab3 = False
if 'show_manual_viz_tab4' not in st.session_state:
    st.session_state.show_manual_viz_tab4 = False

# Özet Dashboard Tab
with tab0:
    st.subheader("📊 Veri Özeti Dashboard")
    
    # Temel istatistikler
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Toplam Satır", f"{len(df):,}")
    with col2:
        st.metric("📋 Toplam Sütun", len(df.columns))
    with col3:
        st.metric("🔢 Sayısal Sütun", len(numeric_cols))
    with col4:
        st.metric("📝 Kategorik Sütun", len(categorical_cols))
    
    st.markdown("---")
    
    # Data preview section (moved from data_upload.py)
    # First 10 rows
    st.markdown("#### İlk 10 Satır")
    st.dataframe(df.head(10), width='stretch')
    
    st.markdown("---")
    
    # Data types
    st.markdown("#### Veri Tipleri")
    dtype_df = get_data_types_summary(df)
    st.dataframe(dtype_df, width='stretch')
    
    st.markdown("---")
    
    # Basic statistics for numeric columns
    numeric_stats = get_numeric_statistics(df)
    if not numeric_stats.empty:
        st.markdown("#### Sayısal Sütunlar - Temel İstatistikler")
        st.dataframe(numeric_stats, width='stretch')
        st.markdown("---")
    
    # Basic statistics for categorical columns
    categorical_stats = get_categorical_statistics(df)
    if not categorical_stats.empty:
        st.markdown("#### Kategorik Sütunlar - Temel İstatistikler")
        st.dataframe(categorical_stats, width='stretch')
        st.markdown("---")
        
        # Value distributions for each categorical column
        st.markdown("#### Kategorik Sütunlar - Değer Dağılımları")
        categorical_cols_list = df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols_list:
            with st.expander(f"📊 {col} - Değer Dağılımı"):
                # Get value distribution from backend
                value_dist = get_categorical_value_distribution(df, col, top_n=10)
                if not value_dist.empty:
                    st.dataframe(value_dist, width='stretch')
                    
                    # Get cardinality info from backend
                    cardinality_info = get_column_cardinality_info(df, col)
                    if cardinality_info['warning']:
                        if cardinality_info['is_potential_id']:
                            st.error(cardinality_info['warning'])
                        else:
                            st.warning(cardinality_info['warning'])
                    
                    st.caption(f"Toplam benzersiz değer: {cardinality_info['unique_count']} / {cardinality_info['total_count']} ({cardinality_info['cardinality_ratio']*100:.1f}%)")

with tab1:
    st.subheader("Temel Görselleştirmeler")
    
    # LLM görselleştirmeleri - REMOVED (temporarily disabled)
    
    # Manuel görselleştirmeler
    if True:  # Always show manual visualizations
        applied_viz = st.session_state.applied_visualizations.copy() if 'applied_visualizations' in st.session_state else []
        for idx, viz_info in enumerate(applied_viz):
            viz_type = viz_info.get('type', '')
            
            if viz_type == 'Correlation Matrix':
                visualization = viz_info.get('visualization')
                library = viz_info.get('library', viz_library)
                
                if visualization:
                    # Görselleştirme başlığı ve silme butonu
                    col_title, col_delete = st.columns([4, 1])
                    with col_title:
                        st.markdown(f"### 🤖 LLM Önerisi: {viz_type}")
                    with col_delete:
                        if st.button("🗑️ Sil", key=f"delete_viz_tab1_{idx}", help="Bu görselleştirmeyi sil"):
                            # Görselleştirmeyi listeden çıkar
                            if 'applied_visualizations' in st.session_state:
                                st.session_state.applied_visualizations.pop(idx)
                                # Applied suggestion IDs'den de çıkar
                                suggestion_id = f"{viz_type.lower().replace(' ', '_')}_{viz_info.get('column', 'general')}"
                                if 'applied_suggestion_ids' in st.session_state and suggestion_id in st.session_state.applied_suggestion_ids:
                                    st.session_state.applied_suggestion_ids.remove(suggestion_id)
                            st.rerun()
                    
                    if library == 'plotly':
                        st.plotly_chart(visualization, config={'displayModeBar': True}, key=f"applied_viz_{idx}_{viz_type}")
                    elif library in ['matplotlib', 'seaborn']:
                        st.pyplot(visualization)
                    elif library == 'streamlit':
                        if hasattr(visualization, 'plot'):
                            st.plotly_chart(visualization, config={'displayModeBar': True}, key=f"applied_viz_{idx}_{viz_type}")
                        else:
                            st.dataframe(visualization)
                    
                    # LLM Yorumu Al butonu - REMOVED (temporarily disabled)
                    if False:  # LLM disabled
                        interpretation_key = f"interpret_{idx}_{viz_type}"
                        if st.button("🤖 LLM Yorumu Al", key=interpretation_key):
                            from backend.modules.eda.eda_llm_enhancer import interpret_analysis
                            with st.spinner("LLM yorumu oluşturuluyor..."):
                                column_name = viz_info.get('column', 'Genel')
                                interpretation_result = interpret_analysis(
                                    viz_type,
                                    column_name,
                                    data_summary
                                )
                                
                                if interpretation_result.get('error'):
                                    st.error(f"❌ Yorum alınamadı: {interpretation_result.get('error')}")
                                else:
                                    interpretation = interpretation_result.get('interpretation', '')
                                    key_findings = interpretation_result.get('key_findings', [])
                                    recommendations = interpretation_result.get('recommendations', [])
                                    
                                    if interpretation:
                                        st.markdown("#### 📝 LLM Yorumu")
                                        st.info(interpretation)
                                    
                                    if key_findings:
                                        st.markdown("#### 🔍 Önemli Bulgular")
                                        for finding in key_findings:
                                            st.markdown(f"- {finding}")
                                    
                                    if recommendations:
                                        st.markdown("#### 💡 Öneriler")
                                        for rec in recommendations:
                                            st.markdown(f"- {rec}")
                    
                    st.markdown("---")
    
    # Manuel görselleştirmeler
    if True:  # Always show manual visualizations
        # Missing values heatmap - eksik değer kontrolü
        st.markdown("### 🔍 Eksik Değerler Haritası")
        missing_count = df.isnull().sum().sum()
        
        if missing_count == 0:
            # Eksik değer yoksa Türkçe mesaj göster
            st.success("✅ Veri setinizde eksik değer bulunmamaktadır. Tüm veriler tam ve analize hazırdır.")
        else:
            # Eksik değer varsa Plotly heatmap göster
            missing_viz = create_missing_heatmap(df, library='plotly')
            if missing_viz is not None:
                st.plotly_chart(missing_viz, config={'displayModeBar': True}, key="missing_heatmap_default")
            else:
                st.warning("⚠️ Eksik değerler haritası oluşturulamadı.")
        
        st.markdown("---")
        
        # Correlation matrix
        if len(numeric_cols) >= 2:
            st.markdown("### 🔗 Korelasyon Matrisi")
            corr_viz = create_correlation_matrix(df, library=viz_library)
            if corr_viz:
                if viz_library == 'plotly':
                    st.plotly_chart(corr_viz, config={'displayModeBar': True}, key="correlation_matrix_default")
                elif viz_library in ['matplotlib', 'seaborn']:
                    st.pyplot(corr_viz)
                elif viz_library == 'streamlit':
                    st.dataframe(corr_viz)
            else:
                st.info("Korelasyon matrisi oluşturulamadı.")

with tab2:
    st.subheader("Sayısal Sütun Analizleri")
    
    # LLM görselleştirmeleri - REMOVED (temporarily disabled)
    
    # Manuel görselleştirmeler
    if True:  # Always show manual visualizations
        applied_viz = st.session_state.applied_visualizations.copy() if 'applied_visualizations' in st.session_state else []
        for idx, viz_info in enumerate(applied_viz):
            viz_type = viz_info.get('type', '')
            
            if viz_type in ['Histogram', 'Box Plot', 'Bar Chart', 'Count Plot']:
                column = viz_info.get('column', '')
                # Görselleştirme başlığı ve silme butonu
                col_title, col_delete = st.columns([4, 1])
                with col_title:
                    st.markdown(f"### 🤖 LLM Önerisi: {viz_type} - {column}")
                with col_delete:
                    if st.button("🗑️ Sil", key=f"delete_viz_tab2_{idx}", help="Bu görselleştirmeyi sil"):
                        if 'applied_visualizations' in st.session_state:
                            st.session_state.applied_visualizations.pop(idx)
                            suggestion_id = f"{viz_type.lower().replace(' ', '_')}_{column or 'general'}"
                            if 'applied_suggestion_ids' in st.session_state and suggestion_id in st.session_state.applied_suggestion_ids:
                                st.session_state.applied_suggestion_ids.remove(suggestion_id)
                        st.rerun()
                
                visualization = viz_info.get('visualization')
                library = viz_info.get('library', viz_library)
                
                if visualization:
                    if library == 'plotly':
                        st.plotly_chart(visualization, config={'displayModeBar': True}, key=f"applied_viz_{idx}_{viz_type}_{column}")
                    elif library in ['matplotlib', 'seaborn']:
                        st.pyplot(visualization)
                    elif library == 'streamlit':
                        if hasattr(visualization, 'plot'):
                            st.plotly_chart(visualization, config={'displayModeBar': True}, key=f"applied_viz_{idx}_{viz_type}_{column}")
                        else:
                            st.dataframe(visualization)
                st.markdown("---")
    
    # Manuel görselleştirmeler (LLM modu kapalıysa veya LLM görselleştirmesi yoksa)
    if True:  # Always show manual visualizations
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
                            st.plotly_chart(hist_viz, config={'displayModeBar': True}, key=f"histogram_{selected_numeric_col}")
                        elif viz_library in ['matplotlib', 'seaborn']:
                            st.pyplot(hist_viz)
                        elif viz_library == 'streamlit':
                            st.bar_chart(hist_viz.value_counts())
                
                with col2:
                    st.markdown("#### 📦 Box Plot")
                    box_viz = create_box_plot(df, selected_numeric_col, library=viz_library)
                    if box_viz:
                        if viz_library == 'plotly':
                            st.plotly_chart(box_viz, config={'displayModeBar': True}, key=f"boxplot_{selected_numeric_col}")
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
                    st.plotly_chart(fig, config={'displayModeBar': True}, key=f"categorical_bar_{selected_cat_col}")
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
    
    # LLM görselleştirmeleri - REMOVED (temporarily disabled)
    
    # Manuel görselleştirmeler
    if True:  # Always show manual visualizations
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
                        st.plotly_chart(scatter_viz, config={'displayModeBar': True}, key=f"scatter_{x_col}_{y_col}")
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

