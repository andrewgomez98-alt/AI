import streamlit as st
import google.generativeai as genai

# --- 1. DESIGN & THEMING (CYAN & OBSIDIAN) ---
st.set_page_config(page_title="Neural Link", page_icon="💠", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #050505; color: #E0E0E0; }
        [data-testid="stSidebar"] { background-color: #0E1117; border-right: 1px solid #00FBFF33; }
        
        /* Message Bubbles */
        [data-testid="stChatMessage"] {
            background-color: #111;
            border-radius: 10px;
            margin-bottom: 10px;
            border: 1px solid #333;
        }
        
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            background-color: #1E1E1E !important; color: #00FBFF !important; border: 1px solid #333 !important;
        }
        .stButton > button {
            background-color: transparent; color: #00FBFF; border: 2px solid #00FBFF;
            border-radius: 5px; width: 100%; transition: 0.3s;
        }
        .stButton > button:hover { background-color: #00FBFF; color: #000; box-shadow: 0 0 15px #00FBFF; }
        .portal-card { background-color: #111; padding: 25px; border-radius: 15px; border-left: 5px solid #00FBFF; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AI AUTHENTICATION ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Missing API Key in Secrets.")
    st.stop()

# --- 3. MEMORY INITIALIZATION ---
# This check ensures the 'history' exists so the app doesn't crash on refresh
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. UI LAYOUT ---
st.title("💠 AGENT NEURAL LINK")

# Sidebar
st.sidebar.header("⚙️ Agent Config")
sys_prompt = st.sidebar.text_area("System Instruction", "You are a creative strategist.")
temp = st.sidebar.slider("Creativity", 0.0, 1.0, 0.7)

if st.sidebar.button("Clear Neural Memory"):
    st.session_state.messages = []
    st.rerun()

# Display Chat History from Session State
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
user_query = st.chat_input("Enter command...")

if user_query:
    # 1. Show user message
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # 2. Add to session history
    st.session_state.messages.append({"role": "user", "content": user_query})

    # 3. Generate AI response with context
    with st.chat_message("assistant"):
        with st.spinner("Accessing Neural Memory..."):
            # Format the history for the API
            history_for_api = [
                {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} 
                for m in st.session_state.messages[:-1]
            ]
            
            # Start a chat session with the saved history
            chat = model.start_chat(history=history_for_api)
            
            # Combine system prompt for the current turn
            full_query = f"INSTRUCTION: {sys_prompt}\n\nUSER: {user_query}"
            response = chat.send_message(full_query, generation_config={"temperature": temp})
            
            st.markdown(f"<span style='color:#00FBFF;'>●</span> {response.text}", unsafe_allow_html=True)
            
            # 4. Add AI response to session history
            st.session_state.messages.append({"role": "assistant", "content": response.text})
