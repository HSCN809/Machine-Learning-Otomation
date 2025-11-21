"""Streamlit page for data upload and validation."""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.modules.data_upload.data_loader import load_data
from backend.modules.data_upload.data_validator import (
    validate_file_format,
    validate_file_size,
    validate_dataframe,
    get_validation_report,
    get_data_summary
)
from backend.modules.data_upload.data_analyzer import (
    get_numeric_statistics,
    get_categorical_statistics,
    get_categorical_value_distribution,
    get_column_cardinality_info,
    get_data_types_summary
)
from backend.modules.utils.file_handler import save_uploaded_file, get_file_size_mb, cleanup_temp_files
from backend.modules.config.settings import MAX_FILE_SIZE_MB, SUPPORTED_FORMATS

# Page configuration
st.set_page_config(
    page_title="Veri Yükleme",
    page_icon="📊",
    layout="wide"
)

# Sadece sol üstteki sayfa navigasyon dropdown'unu gizle (app/data upload)
st.markdown("""
<style>
    /* Sol üstteki sayfa navigasyon dropdown'unu gizle */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Update session state for current page
st.session_state.page = 'Veri Yükleme'

st.title("📊 Veri Yükleme")
st.markdown("---")

# Sidebar navigation (same as main page)
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
        st.info("ℹ️ Veri yüklenmedi")
    
    st.markdown("---")
    st.markdown("### 🧭 Navigasyon")
    
    if st.button("🏠 Ana Sayfa", width='stretch'):
        st.switch_page("app.py")
    
    if st.button("📊 Veri Yükleme", width='stretch', type="primary"):
        pass  # Already on this page
    
    if st.button("🔍 EDA", width='stretch'):
        st.switch_page("pages/eda.py")
    
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
    Veri Yükleme modülü, CSV ve Excel dosyalarınızı yükleyip detaylı doğrulama yapar. Eksik değerler, sabit sütunlar ve veri kalitesi sorunlarını tespit ederek kullanıcıya rehberlik sunar.
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("💡 Sol menüden sayfalar arasında geçiş yapabilirsiniz")

# Initialize session state
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None
if 'validation_report' not in st.session_state:
    st.session_state.validation_report = None
if 'data_summary' not in st.session_state:
    st.session_state.data_summary = None

# Hazır veri setleri için yardımcı fonksiyonlar
def get_sample_datasets_dir():
    """Veri setleri klasörünün yolunu döndür"""
    project_root = Path(__file__).resolve().parent.parent.parent
    return project_root / 'backend' / 'modules' / 'data_upload' / 'sample_datasets'

def get_available_sample_datasets():
    """Klasördeki tüm CSV dosyalarını listele"""
    datasets_dir = get_sample_datasets_dir()
    if not datasets_dir.exists():
        return []
    
    csv_files = list(datasets_dir.glob('*.csv'))
    return sorted(csv_files, key=lambda x: x.stem.lower())

def load_sample_dataset(dataset_name):
    """Hazır veri setlerini yerel dosyalardan yükle"""
    datasets_dir = get_sample_datasets_dir()
    
    try:
        # Iris veri seti sklearn'den yükleniyor (özel durum - IRIS.csv varsa onu kullan)
        if dataset_name.lower() == 'iris':
            # Önce CSV dosyasını kontrol et
            iris_csv = datasets_dir / 'IRIS.csv'
            if iris_csv.exists():
                return pd.read_csv(iris_csv)
            # Yoksa sklearn'den yükle
            from sklearn.datasets import load_iris
            iris = load_iris()
            df = pd.DataFrame(iris.data, columns=iris.feature_names)
            df['species'] = pd.Categorical.from_codes(iris.target, iris.target_names)
            return df
        
        # Diğer veri setleri için klasördeki CSV dosyalarını tara
        if not datasets_dir.exists():
            raise FileNotFoundError(f"Veri setleri klasörü bulunamadı: {datasets_dir}")
        
        # Klasördeki tüm CSV dosyalarını listele
        csv_files = list(datasets_dir.glob('*.csv'))
        
        if not csv_files:
            raise FileNotFoundError(f"Klasörde CSV dosyası bulunamadı: {datasets_dir}")
        
        # Dataset adını normalize et (küçük harf, tire/alt çizgi kaldır)
        normalized_name = dataset_name.lower().replace('-', '').replace('_', '')
        
        # Dosya adlarını kontrol et ve eşleşeni bul
        for csv_file in csv_files:
            file_name_normalized = csv_file.stem.lower().replace('-', '').replace('_', '')
            if normalized_name in file_name_normalized or file_name_normalized in normalized_name:
                return pd.read_csv(csv_file)
        
        # Eşleşme bulunamazsa hata ver
        available_files = [f.name for f in csv_files]
        raise FileNotFoundError(
            f"'{dataset_name}' veri seti bulunamadı. "
            f"Mevcut dosyalar: {', '.join(available_files)}"
        )
        
    except FileNotFoundError as e:
        st.error(f"Veri seti dosyası bulunamadı: {str(e)}")
        st.info("💡 Veri setleri henüz indirilmemiş. Lütfen veri setlerini manuel olarak indirin.")
        return None
    except Exception as e:
        st.error(f"Veri seti yüklenirken hata oluştu: {str(e)}")
        return None

def get_dataset_emoji(dataset_name):
    """Veri seti adına göre emoji döndür"""
    name_lower = dataset_name.lower()
    emoji_map = {
        'titanic': '🚢',
        'iris': '🌸',
        'diamonds': '💎',
        'tips': '🍽️',
        'penguins': '🐧',
        'flights': '✈️',
        'planets': '🪐',
    }
    for key, emoji in emoji_map.items():
        if key in name_lower:
            return emoji
    return '📊'  # Varsayılan emoji

# Hazır Veri Setleri Bölümü
st.header("📚 Hazır Veri Setleri")
st.markdown("Hızlı test için hazır veri setlerinden birini seçebilirsiniz:")

# Klasördeki CSV dosyalarını otomatik algıla
available_datasets = get_available_sample_datasets()

if not available_datasets:
    st.warning("⚠️ `backend/modules/data_upload/sample_datasets/` klasöründe CSV dosyası bulunamadı.")
    st.info("💡 CSV dosyalarını bu klasöre ekleyerek hazır veri setlerini kullanabilirsiniz.")
else:
    # Butonları dinamik olarak oluştur (her satırda 5 buton)
    cols_per_row = 5
    for i in range(0, len(available_datasets), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, csv_file in enumerate(available_datasets[i:i+cols_per_row]):
            with cols[j]:
                dataset_name = csv_file.stem
                emoji = get_dataset_emoji(dataset_name)
                button_label = f"{emoji} {dataset_name}"
                
                if st.button(button_label, width='stretch', key=f"dataset_{i+j}"):
                    df = load_sample_dataset(dataset_name)
                    if df is not None:
                        with st.spinner("🤖 LLM ile öneriler oluşturuluyor..."):
                            try:
                                validation_report = get_validation_report(df)
                                data_summary = get_data_summary(df)
                                st.session_state.uploaded_data = df
                                st.session_state.validation_report = validation_report
                                st.session_state.data_summary = data_summary
                                st.success(f"✅ {dataset_name} veri seti yüklendi!")
                                st.rerun()
                            except Exception as e:
                                error_msg = str(e)
                                st.error(f"❌ LLM önerisi oluşturulamadı: {error_msg}")
                                st.info("💡 Veri seti yüklendi ancak LLM önerileri oluşturulamadı. Lütfen .env dosyasını kontrol edin.")
                                # Veriyi yine de kaydet ama LLM olmadan
                                data_summary = get_data_summary(df)
                                st.session_state.uploaded_data = df
                                st.session_state.data_summary = data_summary

st.markdown("---")

# File upload section
st.header("📁 Dosya Yükleme")

uploaded_file = st.file_uploader(
    "Veri dosyanızı seçin",
    type=['csv', 'xlsx', 'xls'],
    help=f"Desteklenen formatlar: CSV, Excel (XLSX, XLS). Maksimum dosya boyutu: {MAX_FILE_SIZE_MB} MB"
)

if uploaded_file is not None:
    # Display file info
    file_size_mb = get_file_size_mb(uploaded_file.name) if hasattr(uploaded_file, 'name') else uploaded_file.size / (1024 * 1024)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Dosya Adı", uploaded_file.name)
    with col2:
        st.metric("Dosya Boyutu", f"{file_size_mb:.2f} MB")
    with col3:
        file_ext = Path(uploaded_file.name).suffix
        st.metric("Format", file_ext.upper())
    
    # Validate file format
    is_valid_format, format_error = validate_file_format(uploaded_file)
    if not is_valid_format:
        st.error(format_error)
        st.stop()
    
    # Validate file size
    is_valid_size, size_error = validate_file_size(uploaded_file)
    if not is_valid_size:
        st.error(size_error)
        st.stop()
    
    # Load button
    if st.button("📥 Veriyi Yükle", type="primary", width='stretch'):
        with st.spinner("Dosya yükleniyor..."):
            # Save uploaded file temporarily
            temp_file_path = save_uploaded_file(uploaded_file)
            
            if temp_file_path:
                # Determine file format
                file_ext = Path(uploaded_file.name).suffix.lower()
                if file_ext == '.csv':
                    file_format = 'csv'
                elif file_ext in ['.xlsx', '.xls']:
                    file_format = 'excel'
                else:
                    file_format = None
                
                # Load data
                df = load_data(temp_file_path, file_format)
                
                if df is not None:
                    # Validate DataFrame
                    is_valid_df, df_error = validate_dataframe(df)
                    
                    if is_valid_df:
                        # Generate validation report with LLM (always uses LLM)
                        with st.spinner("🤖 LLM ile öneriler oluşturuluyor..."):
                            try:
                                validation_report = get_validation_report(df)
                                data_summary = get_data_summary(df)
                                
                                # Store in session state
                                st.session_state.uploaded_data = df
                                st.session_state.validation_report = validation_report
                                st.session_state.data_summary = data_summary
                                
                                # Cleanup temp file
                                cleanup_temp_files(temp_file_path)
                                
                                st.success("✅ Veri başarıyla yüklendi!")
                                st.rerun()
                            except Exception as e:
                                error_msg = str(e)
                                st.error(f"❌ LLM önerisi oluşturulamadı: {error_msg}")
                                st.info("💡 Veri yüklendi ancak LLM önerileri oluşturulamadı. Lütfen .env dosyasını kontrol edin.")
                                # Veriyi yine de kaydet ama LLM olmadan
                                data_summary = get_data_summary(df)
                                st.session_state.uploaded_data = df
                                st.session_state.data_summary = data_summary
                                cleanup_temp_files(temp_file_path)
                    else:
                        st.error(f"Veri doğrulama hatası: {df_error}")
                        cleanup_temp_files(temp_file_path)
                else:
                    st.error("Veri yüklenirken bir hata oluştu.")
                    cleanup_temp_files(temp_file_path)

# Display validation report if data is loaded
if st.session_state.uploaded_data is not None:
    st.markdown("---")
    st.header("📋 Veri Doğrulama Raporu")
    
    df = st.session_state.uploaded_data
    validation_report = st.session_state.validation_report
    data_summary = st.session_state.data_summary
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Toplam Satır", f"{data_summary['shape']['rows']:,}")
    with col2:
        st.metric("Toplam Sütun", data_summary['shape']['columns'])
    with col3:
        st.metric("Toplam Sorun", validation_report['summary']['total_issues'])
    with col4:
        missing_pct = data_summary['missing_values']['missing_percentage']
        st.metric("Eksik Değer Oranı", f"{missing_pct:.1f}%")
    
    # Display issues by severity
    if validation_report['summary']['total_issues'] > 0:
        st.subheader("Tespit Edilen Sorunlar")
        
        # Helper function to display issue
        def display_issue(issue):
            """Display a single issue with LLM enhancement (always uses LLM)."""
            has_llm = 'llm_enhanced_suggestion' in issue
            
            if has_llm:
                st.markdown("#### 🤖 LLM Önerisi")
                
                # LLM önerisini metin olarak göster (JSON string ise parse et)
                suggestion_text = issue['llm_enhanced_suggestion']
                try:
                    import json
                    # Eğer JSON string ise parse et
                    if suggestion_text.strip().startswith('{'):
                        suggestion_json = json.loads(suggestion_text)
                        if isinstance(suggestion_json, dict) and 'enhanced_suggestion' in suggestion_json:
                            suggestion_text = suggestion_json['enhanced_suggestion']
                        elif isinstance(suggestion_json, str):
                            suggestion_text = suggestion_json
                except:
                    # JSON değilse olduğu gibi göster
                    pass
                
                st.info(suggestion_text)
                
                # Priority only (impact analysis removed - now included in suggestion)
                priority = issue.get('llm_priority', 'orta')
                
                # Check if priority is default or empty
                if not priority or priority == 'orta' or priority.strip() == '':
                    # Try to get from enhanced_suggestion if it's JSON
                    suggestion = issue.get('llm_enhanced_suggestion', '')
                    try:
                        import json
                        if suggestion and suggestion.strip().startswith('{'):
                            suggestion_json = json.loads(suggestion)
                            if isinstance(suggestion_json, dict):
                                if 'priority' in suggestion_json and suggestion_json['priority']:
                                    priority = suggestion_json['priority']
                    except:
                        pass
                
                # Validate priority
                if priority not in ['yüksek', 'orta', 'düşük']:
                    priority = 'orta'
                
                priority_emoji = {'yüksek': '🔴', 'orta': '🟡', 'düşük': '🟢'}.get(priority, '🟡')
                st.markdown(f"**{priority_emoji} Öncelik:** {priority.upper()}")
            else:
                # LLM önerisi yoksa (LLM başarısız oldu)
                st.warning("⚠️ LLM önerisi oluşturulamadı. Lütfen tekrar deneyin.")
            
            # Sütun/Kapsam bilgisi
            if issue.get('column'):
                st.write(f"**📍 Etkilenen Sütun:** {issue['column']}")
            else:
                st.write(f"**📍 Kapsam:** Tüm Veri Seti (Genel Sorun)")
        
        # Critical issues
        if validation_report['issues_by_severity']['kritik']:
            st.error("🔴 **Kritik Sorunlar**")
            for issue in validation_report['issues_by_severity']['kritik']:
                with st.expander(f"⚠️ {issue['description']}", expanded=True):
                    display_issue(issue)
        
        # Warning issues
        if validation_report['issues_by_severity']['uyarı']:
            st.warning("🟡 **Uyarılar**")
            for issue in validation_report['issues_by_severity']['uyarı']:
                with st.expander(f"⚠️ {issue['description']}"):
                    display_issue(issue)
        
        # Info issues
        if validation_report['issues_by_severity']['bilgi']:
            st.info("🔵 **Bilgilendirmeler**")
            for issue in validation_report['issues_by_severity']['bilgi']:
                with st.expander(f"ℹ️ {issue['description']}"):
                    display_issue(issue)
        
        st.info("💡 **Not:** Bu sorunlar sadece bilgilendirme amaçlıdır. Düzeltme işlemleri 'Veri Ön İşleme' modülünde yapılabilir.")
    else:
        st.success("✅ Veri kalitesi iyi görünüyor! Tespit edilen sorun yok.")
    
    st.markdown("---")
    st.header("📊 Veri Önizleme")
    
    # Data preview
    st.subheader("İlk 10 Satır")
    st.dataframe(df.head(10), width='stretch')
    
    # Data types (from backend)
    st.subheader("Veri Tipleri")
    dtype_df = get_data_types_summary(df)
    st.dataframe(dtype_df, width='stretch')
    
    # Basic statistics for numeric columns (from backend)
    numeric_stats = get_numeric_statistics(df)
    if not numeric_stats.empty:
        st.subheader("Sayısal Sütunlar - Temel İstatistikler")
        st.dataframe(numeric_stats, width='stretch')
    
    # Basic statistics for categorical columns (from backend)
    categorical_stats = get_categorical_statistics(df)
    if not categorical_stats.empty:
        st.subheader("Kategorik Sütunlar - Temel İstatistikler")
        st.dataframe(categorical_stats, width='stretch')
        
        # Value distributions for each categorical column
        st.subheader("Kategorik Sütunlar - Değer Dağılımları")
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
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
    
    # Clear data button
    st.markdown("---")
    if st.button("🗑️ Veriyi Temizle", width='stretch'):
        st.session_state.uploaded_data = None
        st.session_state.validation_report = None
        st.session_state.data_summary = None
        st.rerun()

else:
    st.info("👆 Lütfen yukarıdan bir veri dosyası yükleyin.")
    st.markdown("""
    ### Desteklenen Formatlar:
    - **CSV** (.csv)
    - **Excel** (.xlsx, .xls)
    
    ### Dosya Gereksinimleri:
    - Maksimum dosya boyutu: **100 MB**
    - Minimum 1 sütun ve 1 satır içermelidir
    - Yapısal (tabular) veri formatında olmalıdır
    """)

