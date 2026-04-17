import streamlit as st
import google.generativeai as genai

# --- 1. DESIGN & THEMING (CYAN & OBSIDIAN) ---
st.set_page_config(page_title="Neural Link", page_icon="💠", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #050505; color: #E0E0E0; }
        [data-testid="stSidebar"] { background-color: #0E1117; border-right: 1px solid #00FBFF33; }
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
# Ensure you add 'GEMINI_API_KEY' to your Streamlit Secrets!
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Missing API Key. Please add 'GEMINI_API_KEY' to Streamlit Secrets.")

# --- 3. UI LAYOUT ---
st.title("💠 AGENT NEURAL LINK")
st.markdown("<div class='portal-card'>Neural connection established. Configure parameters in the sidebar.</div>", unsafe_allow_html=True)

st.sidebar.header("⚙️ Agent Config")
sys_prompt = st.sidebar.text_area("System Instruction", "You are a creative strategist.")
temp = st.sidebar.slider("Creativity", 0.0, 1.0, 0.7)

user_query = st.chat_input("Enter command...")

if user_query:
    with st.chat_message("user"):
        st.markdown(user_query)
    with st.chat_message("assistant"):
        full_p = f"Instruction: {sys_prompt}\n\nUser: {user_query}"
        response = model.generate_content(full_p, generation_config={"temperature": temp})
        st.markdown(f"<span style='color:#00FBFF;'>●</span> {response.text}", unsafe_allow_html=True)
