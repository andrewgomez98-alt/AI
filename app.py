import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

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

    /* Input Field */
    .stTextInput > div > div > input {
        background-color: #1E1E1E !important;
        color: #00FBFF !important;
        border: 1px solid #00FBFF33 !important;
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
    st.error("Missing GEMINI_API_KEY in Secrets.")
    st.stop()

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. SESSION MANAGEMENT ---
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
if "messages" not in st.session_state:
    st.session_state.messages = []

    # LOAD MEMORY FROM CLOUD ON STARTUP
    try:
        memory_df = conn.read(worksheet="Agent_Memory", ttl=0)
        if not memory_df.empty:
            # Filter for current session if you want to resume, 
            # or keep empty for a fresh start while saving to the same sheet.
            # Here, we filter for the existing session if it matches.
            session_mem = memory_df[memory_df['Session_ID'] == st.session_state.session_id]
            for _, row in session_mem.iterrows():
                st.session_state.messages.append({"role": row['Role'], "content": row['Content']})
    except:
        pass

def save_message_to_cloud(role, content):
    """Saves a single message as a new row to prevent character limit errors."""
    if conn is None: return
    try:
        new_entry = pd.DataFrame([{
            "Session_ID": st.session_state.session_id,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Role": role,
            "Content": content
        }])

        # Pull existing, append new, and update
        try:
            history = conn.read(worksheet="Agent_Memory", ttl=0)
            updated_history = pd.concat([history, new_entry], ignore_index=True)
        except:
            updated_history = new_entry

        conn.update(worksheet="Agent_Memory", data=updated_history)
    except Exception as e:
        st.sidebar.warning(f"Cloud Sync Lag: {str(e)}")

# --- 4. NEURAL ENGINE (Gemini 1.5 Flash) ---
def get_gemini_response(user_text, system_instruction, temp):
    # Using the current stable 1.5 Flash endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

    headers = {'Content-Type': 'application/json'}

    contents = []
    # Add history for context
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    # Add current instruction and query
    contents.append({
        "role": "user", 
        "parts": [{"text": f"SYSTEM INSTRUCTION: {system_instruction}\n\nUSER: {user_text}"}]
    })

    payload = {
        "contents": contents,
        "generationConfig": {"temperature": temp, "maxOutputTokens": 2048}
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"NEURAL ERROR {response.status_code}: {response.text}"

# --- 5. UI LAYOUT ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>💠 NEURAL LINK</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8B949E;'>v3.0 Atomic Memory Protocol</p>", unsafe_allow_html=True)
    st.divider()

    sys_prompt = st.text_area("System Persona", "You are a creative strategist focused on high-growth content and efficient production.")
    temp = st.slider("Neural Temperature", 0.0, 1.0, 0.7)

    st.divider()
    if st.button("🗑️ PURGE SESSION"):
        st.session_state.messages = []
        st.session_state.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        st.rerun()

st.title("💠 Agent Neural Link")
st.markdown(f"""
    <div class='portal-card'>
        <b>Active Session:</b> {st.session_state.session_id}<br>
        <b>Memory Protocol:</b> Atomic Row Storage (Character Limit Fix Active)
    </div>
    """, unsafe_allow_html=True)

# Display Chat History
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# User Interaction
user_query = st.chat_input("Send a command to the neural net...")

if user_query:
    # 1. Display User Message
    with st.chat_message("user"):
        st.markdown(user_query)

    # 2. Save User Message to Cloud immediately
    st.session_state.messages.append({"role": "user", "content": user_query})
    save_message_to_cloud("user", user_query)

    # 3. Get and Display AI Response
    with st.chat_message("assistant"):
        with st.spinner("Processing through Neural Layers..."):
            reply = get_gemini_response(user_query, sys_prompt, temp)
            st.markdown(reply)

            if "NEURAL ERROR" not in reply:
                st.session_state.messages.append({"role": "assistant", "content": reply})
                # 4. Save AI Response to Cloud immediately
                save_message_to_cloud("assistant", reply)
