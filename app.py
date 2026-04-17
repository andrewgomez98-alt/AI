import streamlit as st
import google.generativeai as genai

# --- 1. HIGH-END DESIGN (CYAN & DARK GREY) ---
st.set_page_config(page_title="AI Agent Portal", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
        /* Main background and text */
        .stApp {
            background-color: #050505;
            color: #E0E0E0;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #0E1117;
            border-right: 1px solid #00FBFF33;
        }
        
        /* Input box styling */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            background-color: #1E1E1E !important;
            color: #00FBFF !important;
            border: 1px solid #333 !important;
        }
        
        /* Buttons - The Cyan Pop */
        .stButton > button {
            background-color: transparent;
            color: #00FBFF;
            border: 2px solid #00FBFF;
            border-radius: 5px;
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton > button:hover {
            background-color: #00FBFF;
            color: #000;
            box-shadow: 0 0 15px #00FBFF;
        }

        /* Headers */
        h1, h2, h3 {
            color: #FAFAFA;
            font-family: 'Inter', sans-serif;
            letter-spacing: -1px;
        }
        
        /* Custom Portal Card */
        .portal-card {
            background-color: #111;
            padding: 25px;
            border-radius: 15px;
            border-left: 5px solid #00FBFF;
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AI INITIALIZATION ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. THE UI ---
st.title("💠 AGENT NEURAL LINK")
st.markdown("<div class='portal-card'>Welcome to your custom AI Portal. Define your agent's parameters in the sidebar and engage.</div>", unsafe_allow_html=True)

# Sidebar for "The Prompt Portal"
st.sidebar.header("⚙️ Agent Configuration")
system_prompt = st.sidebar.text_area(
    "System Instruction (Who is this AI?)", 
    value="You are a high-level creative strategist. You provide concise, high-impact advice.",
    height=200
)

st.sidebar.divider()
temperature = st.sidebar.slider("Creativity Level", 0.0, 1.0, 0.7)

# Main Interaction Area
user_input = st.chat_input("Enter command or query...")

if user_input:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Processing through Neural Net..."):
            # We combine the system prompt with the user input for the "Portal" feel
            full_prompt = f"System Instruction: {system_prompt}\n\nUser: {user_input}"
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(temperature=temperature)
            )
            st.markdown(f"<span style='color: #00FBFF;'>●</span> {response.text}", unsafe_allow_html=True)

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("v1.0.0 | RelAXE Neural Systems")
