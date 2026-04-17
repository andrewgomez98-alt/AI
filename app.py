import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. DESIGN & HIGH-END THEMING (CYAN & OBSIDIAN) ---
st.set_page_config(page_title="Neural Link v2.0", page_icon="💠", layout="wide")

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

# --- 2. CONNECTIONS (AI & SHEETS) ---
# Fixing the 401 error by isolating the AI key from the GSheets credentials
if "GEMINI_API_KEY" in st.secrets:
    # transport='rest' ensures the AI engine doesn't accidentally use your GSheets login cookies
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"], transport='rest')
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Missing GEMINI_API_KEY in Secrets.")
    st.stop()

# Initialize GSheets Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. SESSION & MEMORY INITIALIZATION ---
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. COMPACT CLOUD ENGINE (Writes one row per session) ---
def save_to_cloud():
    try:
        # 1. Compress the conversation into a single JSON Blob (saves space)
        compact_json = json.dumps(st.session_state.messages)
        
        # 2. Create the data row
        new_row = pd.DataFrame([{
            "Session_ID": st.session_state.session_id,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Chat_Blob": compact_json
        }])
        
        # 3. Pull existing logs and merge (overwriting the old version of this session)
        try:
            full_history = conn.read(worksheet="Agent_Memory", ttl=0)
            # Remove the previous version of this specific session if it exists
            clean_history = full_history[full_history['Session_ID'] != st.session_state.session_id]
            updated_history = pd.concat([clean_history, new_row], ignore_index=True)
        except:
            updated_history = new_row
            
        # 4. Push back to Google Sheets
        conn.update(worksheet="Agent_Memory", data=updated_history)
    except Exception as e:
        st.sidebar.warning(f"Cloud Sync Delay: {str(e)}")

# --- 5. UI LAYOUT ---
st.title("💠 AGENT NEURAL LINK")
st.markdown("<div class='portal-card'><b>Neural Status:</b> Active <br><b>Cloud Sync:</b> Agent_Memory.gsheet established.</div>", unsafe_allow_html=True)

# SIDEBAR CONTROLS
st.sidebar.header("⚙️ Neural Parameters")
sys_prompt = st.sidebar.text_area("System Persona", "You are a creative strategist for RelAXE Studio.")
temp = st.sidebar.slider("Creativity (Temperature)", 0.0, 1.0, 0.7)

st.sidebar.divider()
if st.sidebar.button("🗑️ Wipe Neural History"):
    st.session_state.messages = []
    st.session_state.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    st.success("Memory purged.")
    st.rerun()

# Display current chat from browser memory
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. INTERACTION LOGIC ---
user_input = st.chat_input("Input command...")

if user_input:
    # 1. Show user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 2. Generate AI response with history context
    with st.chat_message("assistant"):
        with st.spinner("Processing through Neural Net..."):
            # Format history for the Gemini API
            api_history = [
                {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} 
                for m in st.session_state.messages[:-1]
            ]
            
            chat_session = model.start_chat(history=api_history)
            
            # Combine current turn with system instructions
            full_query = f"INSTRUCTION: {sys_prompt}\n\nUSER: {user_input}"
            response = chat_session.send_message(full_query, generation_config={"temperature": temp})
            
            st.markdown(f"<span style='color:#00FBFF;'>●</span> {response.text}", unsafe_allow_html=True)
            
            # 3. Save to browser memory
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # 4. Save to Google Sheets (Compact Blob Mode)
            save_to_cloud()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption(f"Session Trace: {st.session_state.session_id}")
