import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. DESIGN & THEMING ---
st.set_page_config(page_title="Neural Link v2", page_icon="💠", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #050505; color: #E0E0E0; }
        [data-testid="stSidebar"] { background-color: #0E1117; border-right: 1px solid #00FBFF33; }
        [data-testid="stChatMessage"] { background-color: #111; border-radius: 10px; border: 1px solid #333; margin-bottom: 10px; }
        .stTextInput > div > div > input { background-color: #1E1E1E !important; color: #00FBFF !important; }
        .stButton > button { background-color: transparent; color: #00FBFF; border: 2px solid #00FBFF; width: 100%; }
        .stButton > button:hover { background-color: #00FBFF; color: #000; box-shadow: 0 0 15px #00FBFF; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNECTIONS (AI & SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Missing API Key.")
    st.stop()

# --- 3. SESSION & COMPACT MEMORY LOGIC ---
# Create a unique ID for this specific browser session
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. SIDEBAR CONTROLS ---
st.sidebar.header("⚙️ Neural Config")
sys_prompt = st.sidebar.text_area("System Instruction", "You are a creative strategist.")
temp = st.sidebar.slider("Creativity", 0.0, 1.0, 0.7)

# --- 5. CLOUD SYNC FUNCTION (The Compact Writer) ---
def save_to_cloud():
    # Convert the entire message list into one single string of "code" (JSON)
    compact_json = json.dumps(st.session_state.messages)
    
    new_row = pd.DataFrame([{
        "Session_ID": st.session_state.session_id,
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Chat_Blob": compact_json
    }])
    
    # We pull the current history, remove the old version of THIS session, and add the updated one
    try:
        existing_history = conn.read(worksheet="Agent_Memory", ttl=0)
        # Keep all sessions EXCEPT this current one
        clean_history = existing_history[existing_history['Session_ID'] != st.session_state.session_id]
        updated_history = pd.concat([clean_history, new_row], ignore_index=True)
    except:
        updated_history = new_row
        
    conn.update(worksheet="Agent_Memory", data=updated_history)

if st.sidebar.button("🗑️ Wipe Session & Cloud"):
    st.session_state.messages = []
    st.session_state.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    st.rerun()

# --- 6. CHAT INTERFACE ---
st.title("💠 AGENT NEURAL LINK")
st.caption(f"Connected to Cloud Database | Session: {st.session_state.session_id}")

# Display history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Interaction
query = st.chat_input("Input command...")

if query:
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            # Format history for Gemini
            hist = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} 
                    for m in st.session_state.messages[:-1]]
            
            chat = model.start_chat(history=hist)
            full_q = f"INSTRUCTION: {sys_prompt}\n\nUSER: {query}"
            response = chat.send_message(full_q, generation_config={"temperature": temp})
            
            st.markdown(f"<span style='color:#00FBFF;'>●</span> {response.text}", unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # AUTOMATIC COMPACT SAVE
            save_to_cloud()
