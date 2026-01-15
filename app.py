import streamlit as st
import pandas as pd
from src.doc_loader import load_document
from src.analyzer import RuleExtractor
from src.utils import inject_custom_css, card_start, card_end

# Page Config
st.set_page_config(
    page_title="Vizemo Mevzuat Asistanı",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject CSS
inject_custom_css()

# --- Sidebar ---
with st.sidebar:
    st.title("📂 Doküman Yükle")
    st.info("Danışman Paneli v1.0")
    
    uploaded_files = st.file_uploader(
        "Vize Kural Dosyaları (PDF/Word)", 
        type=["pdf", "docx"], 
        accept_multiple_files=True
    )
    
    region_filter = st.selectbox("Bölge / Vize Tipi", ["Schengen", "Amerika", "Asya", "Diğer"])
    
    st.divider()
    st.caption("Vizemo AI Engine © 2026")

# --- Main Logic ---

if not uploaded_files:
    st.header("👋 Vizemo Mevzuat Asistanına Hoşgeldiniz")
    st.write("Analiz etmek için lütfen sol menüden güncel vize evrak listesini yükleyin.")
    st.stop()

# Layout
st.title("🛡️ Mevzuat Analiz Paneli")

# Process the LAST uploaded file for the demo (or merge logic could go here)
# For simplicity in this iteration, we visualize the first/most relevant file.
current_file = uploaded_files[0]
text_content = load_document(current_file)

if text_content == "Unsupported file format.":
    st.error("Desteklenmeyen dosya formatı.")
    st.stop()

# Analyze
analyzer = RuleExtractor(text_content)
critical_rules = analyzer.extract_critical_rules()
fees = analyzer.extract_fees()
insurance_limit = analyzer.extract_insurance_limit()
checklist = analyzer.analyze_checklist_items()
upsells = analyzer.get_upsell_opportunities()

# Create 3 Columns
col1, col2, col3 = st.columns([1, 1.5, 1])

# --- COL 1: Mevzuat Özeti ---
with col1:
    st.subheader("📌 Mevzuat Özeti")
    
    # Fees Card
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-label">Vize Ücreti</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{" / ".join(fees)}</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown(f'<div class="metric-label">Sigorta Limiti</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value" style="font-size: 1.5rem;">{insurance_limit}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Critical Rules
    st.markdown("### 🚦 Kritik Kurallar")
    for rule in critical_rules:
        st.warning(rule, icon="⚠️")

# --- COL 2: Eksik Analiz (Checklist) ---
with col2:
    st.subheader("📋 Evrak Kontrol Listesi")
    
    # Session state for checklist
    if "checked_items" not in st.session_state:
        st.session_state.checked_items = set()

    # Progress Calculation
    total_items = len(checklist)
    checked_count = len(st.session_state.checked_items)
    progress = checked_count / total_items if total_items > 0 else 0
    
    st.progress(progress, text=f"Hazırlık Oranı: %{int(progress*100)}")
    
    st.markdown('<div class="css-card" style="max-height: 600px; overflow-y: auto;">', unsafe_allow_html=True)
    for idx, item in enumerate(checklist):
        is_checked = st.checkbox(
            item, 
            key=f"check_{idx}",
            value=(idx in st.session_state.checked_items)
        )
        # Update state manually (Streamlit re-runs on interaction)
        if is_checked:
            st.session_state.checked_items.add(idx)
        elif idx in st.session_state.checked_items:
            st.session_state.checked_items.remove(idx)
    st.markdown('</div>', unsafe_allow_html=True)

# --- COL 3: Satış & Upsell ---
with col3:
    st.subheader("💰 Satış Fırsatları")
    
    if upsells["insurance"]:
        st.markdown("""
        <div class="upsell-box">
            <div class="upsell-title">🏥 Seyahat Sigortası Fırsatı</div>
            Mevzuat zorunlu kılıyor. 30.000€ teminatlı sigorta satışı yapmayı unutma!
            <br><b>Ort. Kazanç: 15€</b>
        </div>
        """, unsafe_allow_html=True)
        
    if upsells["flight_hotel"]:
        st.markdown("""
        <div class="upsell-box" style="background-color: #0c2b37; border-color: #046c4e; color: #a7f3d0;">
            <div class="upsell-title">✈️ Rezervasyon Desteği</div>
            Uçak/Otel rezervasyon kanıtı isteniyor. Geçici rezervasyon hizmeti öner.
            <br><b>Hizmet Bedeli: 200 TL</b>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 🧠 Danışman Notları")
    st.text_area("Müşteri özel notları...", height=150)
    if st.button("Dosyayı Kapat ve Kaydet"):
        st.success("Analiz kaydedildi!")

