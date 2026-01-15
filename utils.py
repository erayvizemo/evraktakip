import streamlit as st

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
