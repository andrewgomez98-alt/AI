import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. DESIGN & HIGH-END THEMING (CYAN & OBSIDIAN) ---
st.set_page_config(page_title="Neural Link v2.2", page_icon="💠", layout="wide")

st.markdown("""
    <style>
        /* Main Obsidian Background */
        .stApp { background-color: #050505; color: #E0E0E0; }
        
        /* High-End Sidebar */
        [data-testid="stSidebar"] { 
            background-color: #0E1117; 
            border-right: 1px solid #00FBFF33; 
        }
        
        /* Chat Bubble Obsidians */
        [data-testid="stChatMessage"] {
            background-color: #111;
            border-radius: 12px;
            border: 1px solid #333;
            margin-bottom: 12px;
            padding: 15px;
        }

        /* Custom Input Portals */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            background-color: #1E1E1E !important; 
            color: #00FBFF !important; 
            border: 1px solid #333 !important;
            border-radius: 8px !important;
        }

        /* The Cyan Glow Button */
        .stButton > button {
            background-color: transparent; 
            color: #00FBFF; 
            border: 2px solid #00FBFF;
            border-radius: 8px; 
            width: 100%; 
            transition: all 0.3s ease;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stButton > button:hover {
            background-color: #00FBFF; 
            color: #000; 
            box-shadow: 0 0 20px #00FBFF;
        }

        /* Neural Card Styling */
        .portal-card {
            background-color: #111; 
            padding: 25px; 
            border-radius: 15px; 
            border-left: 5px solid #00FBFF; 
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }
    </style>
    """, unsafe_allow_html=True)

# --- 2. NEURAL STEALTH AUTHENTICATION ---
# This block isolates the AI from your GSheets credentials to prevent 401 errors
if "GEMINI_API_KEY" in st.secrets:
    # Force the environment to focus only on the AI Key
    api_key = st.secrets["GEMINI_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = api_key
    
    # Configure AI using 'rest' transport to bypass OAuth interference
    genai.configure(api_key=api_key, transport='rest')
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Missing GEMINI_API_KEY in Secrets.")
    st.stop()

# --- 3. DATABASE CONNECTION ---
# Establish connection to your Relaxe_Database
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.sidebar.error("Database initialization pending...")

# --- 4. SESSION & COMPACT MEMORY LOGIC ---
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 5. CLOUD SYNC ENGINE (Compact JSON Blobs) ---
def save_to_cloud():
    try:
        # Compress the entire chat into one string
        compact_json = json.dumps(st.session_state.messages)
        
        new_row = pd.DataFrame([{
            "Session_ID": st.session_state.session_id,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Chat_Blob": compact_json
        }])
        
        # Pull, Merge, and Update
        try:
            full_history = conn.read(worksheet="Agent_Memory", ttl=0)
            # Filter out previous versions of this session
            clean_history = full_history[full_history['Session_ID'] != st.session_state.session_id]
            updated_history = pd.concat([clean_history, new_row], ignore_index=True)
        except:
            updated_history = new_row
            
        conn.update(worksheet="Agent_Memory", data=updated_history)
    except Exception as e:
        st.sidebar.warning("Cloud Syncing...")

# --- 6. UI LAYOUT ---
st.title("💠 AGENT NEURAL LINK")
st.markdown(f"<div class='portal-card'><b>Neural Status:</b> Active<br><b>Current Session:</b> {st.session_state.session_id}</div>", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("⚙️ Neural Config")
sys_prompt = st.sidebar.text_area("System Persona", "You are a creative strategist.")
temp = st.sidebar.slider("Creativity (Temperature)", 0.0, 1.0, 0.7)

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
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.chat_message("assistant"):
        with st.spinner("Processing through Neural Net..."):
            # Prepare context for Gemini
            api_hist = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} 
                        for m in st.session_state.messages[:-1]]
            
            chat_session = model.start_chat(history=api_hist)
            full_p = f"INSTRUCTION: {sys_prompt}\n\nUSER: {user_query}"
            
            response = chat_session.send_message(full_p, generation_config={"temperature": temp})
            
            st.markdown(f"<span style='color:#00FBFF;'>●</span> {response.text}", unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # Auto-save to Google Sheets
            save_to_cloud()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption(f"Neural Link v2.2 | {st.session_state.session_id}")
