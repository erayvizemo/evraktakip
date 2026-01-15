import streamlit as st
import pandas as pd
import pdfplumber
import docx
import io
import re

# -----------------------------------------------------------------------------
# 1. UTILS & STYLING (Restored from src/utils.py)
# -----------------------------------------------------------------------------
def inject_custom_css():
    st.markdown("""
    <style>
    /* Global Theme */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #262730;
    }
    
    /* Cards/Containers */
    .css-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #374151;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    
    /* Summary Metrics */
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #60a5fa;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #9ca3af;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background-color: #10b981;
    }
    
    /* Alerts */
    .upsell-box {
        background-color: #37330c; 
        border: 1px solid #ca8a04;
        color: #fef08a;
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
    }
    
    .upsell-title {
        font-weight: bold;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    </style>
    """, unsafe_allow_html=True)

def card_start():
    st.markdown('<div class="css-card">', unsafe_allow_html=True)

def card_end():
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DOCUMENT LOADER (Restored from src/doc_loader.py)
# -----------------------------------------------------------------------------
def extract_text_from_pdf(file_bytes):
    """
    Extracts text from a PDF file (bytes).
    """
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_docx(file_bytes):
    """
    Extracts text from a DOCX file (bytes).
    """
    doc = docx.Document(io.BytesIO(file_bytes))
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def load_document(uploaded_file):
    """
    Router to load document based on type.
    """
    if uploaded_file.name.lower().endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file.getvalue())
    elif uploaded_file.name.lower().endswith(".docx"):
        return extract_text_from_docx(uploaded_file.getvalue())
    else:
        return "Unsupported file format."

# -----------------------------------------------------------------------------
# 3. ANALYZER (Restored from src/analyzer.py)
# -----------------------------------------------------------------------------
class RuleExtractor:
    def __init__(self, text):
        self.text = text

    def extract_critical_rules(self):
        """
        Extracts top 3 critical rules: Passport Validity, Photos, Biometrics.
        """
        rules = []
        
        # Passport Validity
        passport_match = re.search(r"(pasaport|travel document).*?(en az|geçerli).*?(\d+\s*ay|\d+\s*yıl)", self.text, re.IGNORECASE)
        if passport_match:
            rules.append(f"⚠️ Pasaport Geçerliliği: {passport_match.group(0)}")
        else:
            rules.append("⚠️ Pasaport Geçerliliği: En az 6 ay önerilir (Dokümanda bulunamadı)")

        # Photos
        photo_match = re.search(r"(biyometrik|fotoğraf).*?(\d\.\d\s*x\s*\d\.\d|\d\s*x\s*\d)", self.text, re.IGNORECASE)
        if photo_match:
            rules.append(f"📸 Fotoğraf: {photo_match.group(0)}")
        
        # Biometrics hint (simple check)
        if "parmak izi" in self.text.lower() or "biyometri" in self.text.lower():
            rules.append("Fingerprint: Son 59 ayda verilmemişse şahsen başvuru gerekir.")

        # Cap at 3
        while len(rules) < 3:
            rules.append("Ek kural bulunamadı.")
            
        return rules[:3]

    def extract_fees(self):
        """
        Extracts visa fees.
        """
        # Look for currency amounts near keywords
        fees = []
        matches = re.findall(r"(vize|harç|ücret).*?(\d{2,3})\s*(€|EUR|TL|USD|\$)", self.text, re.IGNORECASE)
        for m in matches:
            fees.append(f"{m[1]} {m[2]}")
        
        return list(set(fees)) if fees else ["Belirtilmemiş"]

    def extract_insurance_limit(self):
        """
        Extracts insurance coverage requirement.
        """
        match = re.search(r"(sigorta|teminat).*?(\d{2,3}[\.,]?\d{0,3})\s*(€|EUR|Euro)", self.text, re.IGNORECASE)
        if match:
            return f"{match.group(2)} {match.group(3)}"
        return "30.000 € (Standart)"

    def analyze_checklist_items(self):
        """
        Attempts to list potential checklist items by looking for bullet points or numbered lists.
        """
        items = []
        # Simple heuristic: lines starting with -, *, 1., or specific keywords
        lines = self.text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) < 5 or "sayfa" in line.lower(): 
                continue # Skip short rubbish
            
            # Pattern for list items
            if re.match(r"^(\d+\.|-|\*|•)\s+", line):
                clean_line = re.sub(r"^(\d+\.|-|\*|•)\s+", "", line)
                items.append(clean_line)
            # Fallback for document names
            elif any(x in line.lower() for x in ["belge", "form", "dilekçe", "bordro", "banka", "rezervasyon", "sigorta"]):
                items.append(line)
                
        return items if items else ["Otomatik liste çıkarılamadı. Lütfen metni kontrol edin."]

    def get_upsell_opportunities(self):
        """
        Returns flags for upsell.
        """
        upsells = {
            "insurance": False,
            "flight_hotel": False,
            "vip": False
        }
        
        lower_text = self.text.lower()
        
        if "sigorta" in lower_text or "teminat" in lower_text:
            upsells["insurance"] = True
            
        if any(x in lower_text for x in ["uçak", "otel", "konaklama", "rezervasyon", "bilet"]):
            upsells["flight_hotel"] = True
            
        if "vip" in lower_text or "eksper" in lower_text:
            upsells["vip"] = True
            
        return upsells

# -----------------------------------------------------------------------------
# 4. MAIN APP LOGIC (Restored from app.py)
# -----------------------------------------------------------------------------

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
