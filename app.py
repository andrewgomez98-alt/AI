import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. DESIGN & HIGH-END THEMING ---
st.set_page_config(page_title="Neural Link v2.9", page_icon="💠", layout="wide")

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

# --- 2. AUTHENTICATION ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Missing GEMINI_API_KEY in Secrets.")
    st.stop()

# --- 3. DATABASE CONNECTION (v2.9 - Verbose Mode) ---
conn = None
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Test read to verify permissions
    test_read = conn.read(worksheet="Agent_Memory", ttl=0)
    st.sidebar.success("✅ Cloud Memory Linked")
except Exception as e:
    st.sidebar.error(f"❌ Sync Error: {str(e)}")
    st.sidebar.info("Check if 'Agent_Memory' tab exists and sheet is shared with Service Account email.")

# --- 4. SESSION & COMPACT MEMORY ---
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
if "messages" not in st.session_state:
    st.session_state.messages = []

def save_to_cloud():
    if conn is None: return
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
    except Exception as e:
        st.sidebar.warning(f"Save Failed: {str(e)}")

# --- 5. THE 2026 NEURAL ENGINE (v2.9) ---
def get_gemini_response(user_text, system_instruction, temp):
    # Using the latest April 2026 stable endpoint
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"
    
    session = requests.Session()
    session.headers.clear() 
    
    params = {'key': API_KEY}
    headers = {'Content-Type': 'application/json'}
    
    contents = []
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    
    full_prompt = f"INSTRUCTION: {system_instruction}\n\nUSER: {user_text}"
    contents.append({"role": "user", "parts": [{"text": full_prompt}]})
    
    payload = {"contents": contents, "generationConfig": {"temperature": temp}}
    
    response = session.post(url, params=params, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"NEURAL ERROR {response.status_code}: {response.text}"

# --- 6. UI ---
st.title("💠 AGENT NEURAL LINK")
st.markdown("<div class='portal-card'><b>Neural Engine:</b> Gemini 3 Flash (v2.9)<br><b>Cloud Sync:</b> Active Session Protocol</div>", unsafe_allow_html=True)

sys_prompt = st.sidebar.text_area("System Persona", "You are a creative strategist.")
temp = st.sidebar.slider("Creativity", 0.0, 1.0, 0.7)

if st.sidebar.button("🗑️ Wipe Session Memory"):
    st.session_state.messages = []
    st.session_state.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    st.rerun()

# Display Chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Interaction
user_query = st.chat_input("Enter command...")
if user_query:
    with st.chat_message("user"): st.markdown(user_query)
    with st.chat_message("assistant"):
        with st.spinner("Connecting to 2026 Neural Net..."):
            reply = get_gemini_response(user_query, sys_prompt, temp)
            st.markdown(f"<span style='color:#00FBFF;'>●</span> {reply}", unsafe_allow_html=True)
            if "NEURAL ERROR" not in reply:
                st.session_state.messages.append({"role": "user", "content": user_query})
                st.session_state.messages.append({"role": "assistant", "content": reply})
                save_to_cloud()
