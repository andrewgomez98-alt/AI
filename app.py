import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import base64 # Needed for encoding images for Gemini API
import mimetypes # To infer mime type from file extension if needed, though st.file_uploader often provides it

# --- 1. HIGH-END MOUNTAIN-CYBER AESTHETIC ---
st.set_page_config(page_title="Neural Link v3.0", page_icon="💠", layout="wide")

st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161B22 !important;
        border-right: 1px solid #00FBFF33;
    }

    /* Chat Messages */
    [data-testid="stChatMessage"] {
        background-color: #161B22;
        border-radius: 15px;
        border: 1px solid #30363D;
        margin-bottom: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    /* User message specific styling */
    [data-testid="stChatMessage"].st-emotion-cache-1c7y2k2 { /* This class might vary slightly based on Streamlit version */
        background-color: #202B37;
    }

    /* Input Field */
    .stTextInput > div > div > input {
        background-color: #1E1E1E !important;
        color: #00FBFF !important;
        border: 1px solid #00FBFF33 !important;
    }

    /* File Uploader styling */
    .stFileUploader > div > div { /* Target the inner container of the uploader */
        background-color: #1E1E1E !important;
        border: 1px solid #00FBFF33 !important;
        border-radius: 8px !important;
        color: #00FBFF !important;
        padding: 5px; /* Adjust padding for better look */
    }
    .stFileUploader > div > div > button { /* Target the browse button */
        background-color: transparent !important;
        color: #00FBFF !important;
        border: 1px solid #00FBFF !important;
        border-radius: 8px !important;
        transition: 0.3s;
    }
    .stFileUploader > div > div > button:hover {
        background-color: #00FBFF !important;
        color: #000 !important;
        box-shadow: 0 0 10px #00FBFF;
    }
    .stFileUploader > div > div > div > span { /* Text like "No file uploaded" */
        color: #00FBFF !important;
    }
    .stFileUploader > div > div > div > p { /* File name after upload */
        color: #E0E0E0 !important;
    }

    /* Custom KPI Cards for Session Info */
    .portal-card {
        background: rgba(22, 27, 34, 0.8);
        border-left: 5px solid #00FBFF;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }

    /* Buttons */
    .stButton>button {
        background-color: transparent !important;
        color: #00FBFF !important;
        border: 1px solid #00FBFF !important;
        border-radius: 8px !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #00FBFF !important;
        color: #000 !important;
        box-shadow: 0 0 15px #00FBFF;
    }

    /* Headers */
    h1, h2, h3 {
        color: #00FBFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION & DATABASE ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Missing GEMINI_API_KEY in Secrets. Please add it to your Streamlit secrets.")
    st.stop()

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. SESSION MANAGEMENT ---
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
if "messages" not in st.session_state:
    st.session_state.messages = []
# NEW: Initialize a place to store uploaded attachments for the current turn
if "current_attachments" not in st.session_state:
    st.session_state.current_attachments = []

    # LOAD MEMORY FROM CLOUD ON STARTUP
    try:
        memory_df = conn.read(worksheet="Agent_Memory", ttl=0)
        if not memory_df.empty:
            # Filter for current session if you want to resume,
            # or keep empty for a fresh start while saving to the same sheet.
            # NOTE: Attachments are NOT loaded from GSheets, only text.
            session_mem = memory_df[memory_df['Session_ID'] == st.session_state.session_id]
            for _, row in session_mem.iterrows():
                # If you stored image placeholders, you might
