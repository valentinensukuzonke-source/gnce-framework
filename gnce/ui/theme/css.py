import streamlit as st

def apply_gnce_theme():
    st.markdown("""
<style>

/* ------------------------------------
   GLOBAL DARK THEME
------------------------------------- */

body, .block-container {
    background-color: #0f172a !important;
    color: #e2e8f0 !important;
    font-family: "Inter", sans-serif;
}

[data-testid="stAppViewContainer"] { background-color: #0f172a !important; }

/* Hide Streamlit default header */
header { visibility: hidden; height: 0px !important; }

/* ------------------------------------
   GN Header
------------------------------------- */

.gn-header-title {
    font-size: 2.2rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}

.gn-header-subtitle {
    font-size: 1rem;
    opacity: 0.8;
    margin-bottom: 0.8rem;
}

/* Logo card */
.gn-logo-card {
    width: 160px;
    height: 100px;
    border-radius: 20px;
    background: radial-gradient(circle at 0% 0%, #e3f6ff, #0f172a);
    box-shadow: 0 10px 25px rgba(0,0,0,0.35);
    display: flex;
    justify-content: center;
    align-items: center;
}

.gn-logo-mark {
    width: 120px;
    animation: gn-spin 18s linear infinite;
}

@keyframes gn-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* ------------------------------------
   GN Badges
------------------------------------- */
.gn-badge {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: rgba(0, 179, 201, 0.1);
    color: #00b3c9;
    border: 1px solid rgba(0, 179, 201, 0.3);
    margin-right: 0.25rem;
}

/* ------------------------------------
   SEVERITY TAGS
------------------------------------- */

div[data-baseweb="tag"] {
    display: inline-flex;
    padding: 0;
    background-color: transparent !important;
}

span[data-testid="tag-text"] {
    display: inline-block;
    border-radius: 999px;
    padding: 2px 8px;
    font-weight: 600;
    background-color: #3a3f47 !important;
    color: white !important;
}

/* Colors */
span[title*="ALLOW"]     { background-color: #21c162 !important; }
span[title*="DENY"]      { background-color: #d9364f !important; }
span[title*="ESCALATE"]  { background-color: #ff7a24 !important; }
span[title*="WARNING"]   { background-color: #e7c000 !important; color:black!important; }
span[title*="ADVISORY"]  { background-color: #1e88e5 !important; }
span[title*="ERROR"]     { background-color: #9c27b0 !important; }
span[title*="LOW"]       { background-color: #00916E !important; }
span[title*="MEDIUM"]    { background-color: #ffb300 !important; color:black!important;}
span[title*="HIGH"]      { background-color: #C62828 !important; }
span[title*="CRITICAL"]  { background-color: #8b008b !important; }

/* ------------------------------------
   Card Styling
------------------------------------- */
.gn-card {
    background:#020617;
    border:1px solid #1e293b;
    padding:1rem;
    border-radius:12px;
    margin-bottom:1rem;
}

</style>
""", unsafe_allow_html=True)
