"""Main Streamlit application entry point."""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Machine Learning Automation",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
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
st.session_state.page = 'Ana Sayfa'

# Main page
st.title("🤖 Machine Learning Automation Platform")
st.markdown("---")
st.markdown("""
### Hoş Geldiniz!

Bu platform, makine öğrenmesi modeli geliştirme sürecini otomatize eden bir araçtır.

**Özellikler:**
- 📊 Otomatik veri yükleme ve doğrulama
- 🔍 Keşifsel Veri Analizi (EDA)
- 🤖 Otomatik model eğitimi
- 📈 Model değerlendirme ve karşılaştırma
- 💬 AI Asistanı ile rehberlik

**Başlamak için:**
Sol menüden "Veri Yükleme" sayfasına gidin ve veri dosyanızı yükleyin.
""")

# Sidebar navigation with improved design
with st.sidebar:
    st.title("🤖 ML Automation")
    st.markdown("---")
    
    # Status indicator at top
    if st.session_state.get('uploaded_data') is not None:
        st.success("✅ Veri yüklü")
        df = st.session_state.get('uploaded_data')
        if df is not None:
            st.caption(f"📊 {len(df):,} satır × {len(df.columns)} sütun")
    else:
        st.info("ℹ️ Veri yüklenmedi")
    
    st.markdown("---")
    
    # Navigation menu with styled buttons
    st.markdown("### 🧭 Navigasyon")
    
    # Current page indicator
    current_page = st.session_state.get('page', 'Ana Sayfa')
    
    # Navigation buttons
    if st.button("🏠 Ana Sayfa", width='stretch', type="primary" if current_page == 'Ana Sayfa' else "secondary"):
        st.switch_page("app.py")
    
    if st.button("📊 Veri Yükleme", width='stretch', type="primary" if current_page == 'Veri Yükleme' else "secondary"):
        st.switch_page("pages/data_upload.py")
    
    if st.button("🔍 EDA", width='stretch', type="primary" if current_page == 'EDA' else "secondary"):
        st.switch_page("pages/eda.py")
    
    st.markdown("---")
    
    # About section with styled box
    st.markdown("### ℹ️ Hakkında")
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 15px; 
                border-radius: 10px; 
                margin: 10px 0;
                color: white;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
    <p style='margin: 0; font-size: 0.9em; line-height: 1.6; color: white;'>
    Makine öğrenmesi süreçlerini otomatize eden platform
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("💡 Sol menüden sayfalar arasında geçiş yapabilirsiniz")

