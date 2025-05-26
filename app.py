import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# App configuration
st.set_page_config(
    page_title="AI Content Generator",
    page_icon="✨",
    layout="wide"
)

# Custom styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: #1E40AF;
    }
    .card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .success-text {
        color: #047857;
        font-weight: 600;
    }
    .error-text {
        color: #DC2626;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# App title
st.markdown('<div class="main-title">AI Content Generator</div>', unsafe_allow_html=True)

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'model' not in st.session_state:
    st.session_state.model = 'gemini-1.5-flash'

# Sidebar configuration
with st.sidebar:
    st.markdown("### Configuration")
    
    # API Key input
    api_key = st.text_input(
        "Enter your Gemini API key:",
        type="password",
        value=st.session_state.api_key
    )
    
    # Model selection
    model = st.selectbox(
        "Select Model:",
        ["gemini-1.5-flash", "gemini-1.5-pro"],
        index=0
    )
    
    if st.button("Save Configuration"):
        if api_key:
            st.session_state.api_key = api_key
            st.session_state.model = model
            genai.configure(api_key=api_key)
            st.success("Configuration saved successfully!")
        else:
            st.error("Please enter an API key.")

# Main content area
st.markdown("### Generate Content")

st.markdown('<div class="card">', unsafe_allow_html=True)

# Input method selection
input_method = st.radio(
    "Choose input method:",
    ["Enter text manually", "Upload a file"],
    horizontal=True
)

if input_method == "Enter text manually":
    user_input = st.text_area(
        "Enter your text:",
        height=150,
        placeholder="Enter the text you want to process..."
    )
    
    if st.button("Generate"):
        if not st.session_state.api_key:
            st.error("Please configure your API key in the sidebar first.")
        elif not user_input:
            st.error("Please enter some text to process.")
        else:
            try:
                # Initialize the model
                model = genai.GenerativeModel(
                    model_name=st.session_state.model
                )
                
                # Generate content
                response = model.generate_content(user_input)
                
                # Display result
                st.markdown("### Result")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

else:  # File upload
    uploaded_file = st.file_uploader("Upload a text file:", type=["txt"])
    
    if uploaded_file is not None:
        content = uploaded_file.read().decode("utf-8")
        if st.button("Process File"):
            if not st.session_state.api_key:
                st.error("Please configure your API key in the sidebar first.")
            else:
                try:
                    # Initialize the model
                    model = genai.GenerativeModel(
                        model_name=st.session_state.model
                    )
                    
                    # Generate content
                    response = model.generate_content(content)
                    
                    # Display result
                    st.markdown("### Result")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)
