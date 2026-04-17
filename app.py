import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. DESIGN & HIGH-END THEMING ---
st.set_page_config(page_title="Neural Link v2.6", page_icon="💠", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #050505; color: #E0E0E0; }
        [data-testid="stSidebar"] { background-color: #0E1117; border-right: 1px solid #00FBFF33; }
        [data-testid="stChatMessage"] { background-color: #111; border-radius: 12px; border: 1px solid #333; margin-bottom: 12px; }
        .stTextInput > div > div > input { background-color: #1E1E1E !important; color: #00FBFF !important; border: 1px solid #333 !important; }
        .stButton > button { background-color: transparent; color: #00FBFF; border: 2px solid #00FBFF; border-radius: 8px; width: 100%; transition: 0.3s; }
        .stButton > button:hover { background-color: #00FBFF; color: #000; box-shadow: 0 0 20px #00FBFF; }
        .portal-card { background-color: #111; padding: 25px; border-radius: 15px; border-left: 5px solid #00FBFF; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE 2026 DIRECT ENGINE ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Missing GEMINI_API_KEY in Secrets.")
    st.stop()

# --- 3. DATABASE CONNECTION ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.sidebar.error("Cloud Sync Pending...")

# --- 4. SESSION & COMPACT MEMORY ---
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
if "messages" not in st.session_state:
    st.session_state.messages = []

def save_to_cloud():
    try:
        compact_json = json.dumps(st.session_state.messages)
        new_row = pd.DataFrame([{"Session_ID": st.session_state.session_id, "Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Chat_Blob": compact_json}])
        try:
            full_history = conn.read(worksheet="Agent_Memory", ttl=0)
            clean_history = full_history[full_history['Session_ID'] != st.session_state.session_id]
            updated_history = pd.concat([clean_history, new_row], ignore_index=True)
        except:
            updated_history = new_row
        conn.update(worksheet="Agent_Memory", data=updated_history)
    except: pass

# --- 5. THE BYPASS ENGINE ---
def get_gemini_response(user_text, system_instruction, temp):
    # UPDATED FOR APRIL 2026: Using v1 stable and Gemini 3.1 Flash
    model_name = "gemini-3.1-flash" 
    url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    
    contents = []
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    
    full_prompt = f"INSTRUCTION: {system_instruction}\n\nUSER: {user_text}"
    contents.append({"role": "user", "parts": [{"text": full_prompt}]})
    
    payload = {"contents": contents, "generationConfig": {"temperature": temp}}
    
    # We use a clean request to avoid any background cookie interference
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"CRITICAL AUTH ERROR: {response.status_code}. Google is rejecting the project key. Ensure Gemini API is ENABLED in Cloud Console."

# --- 6. UI ---
st.title("💠 AGENT NEURAL LINK")
st.markdown("<div class='portal-card'><b>Neural Engine:</b> Gemini 3.1 Flash (v2.6)<br><b>Handshake:</b> Direct URL Bypass</div>", unsafe_allow_html=True)

sys_prompt = st.sidebar.text_area("System Persona", "You are a creative strategist.")
temp = st.sidebar.slider("Creativity", 0.0, 1.0, 0.7)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

user_query = st.chat_input("Enter command...")
if user_query:
    with st.chat_message("user"): st.markdown(user_query)
    with st.chat_message("assistant"):
        with st.spinner("Bypassing Auth Gate..."):
            reply = get_gemini_response(user_query, sys_prompt, temp)
            st.markdown(f"<span style='color:#00FBFF;'>●</span> {reply}", unsafe_allow_html=True)
            if "CRITICAL AUTH" not in reply:
                st.session_state.messages.append({"role": "user", "content": user_query})
                st.session_state.messages.append({"role": "assistant", "content": reply})
                save_to_cloud()
