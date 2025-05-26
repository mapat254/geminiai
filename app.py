import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import json
import markdown

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
    .image-gallery {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 20px;
    }
    .image-card {
        flex: 1;
        min-width: 200px;
        max-width: 300px;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
    }
    .image-card img {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

def search_bing_images(query, num_images=5):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        search_url = f'https://www.bing.com/images/search?q={query}&form=HDRSC2'
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        images = []
        for img in soup.find_all('a', class_='iusc'):
            try:
                m = json.loads(img['m'])
                image_url = m['murl']
                images.append({
                    'url': image_url,
                    'title': m.get('t', 'Image')
                })
                if len(images) >= num_images:
                    break
            except:
                continue
        
        return images
    except Exception as e:
        st.error(f"Error searching images: {str(e)}")
        return []

# App title
st.markdown('<div class="main-title">AI Content Generator</div>', unsafe_allow_html=True)

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'model' not in st.session_state:
    st.session_state.model = 'gemini-1.5-flash'
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None
if 'images' not in st.session_state:
    st.session_state.images = []

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
                with st.spinner("Generating content..."):
                    # Initialize the model
                    model = genai.GenerativeModel(
                        model_name=st.session_state.model
                    )
                    
                    # Generate content
                    response = model.generate_content(user_input)
                    st.session_state.generated_content = response.text
                    
                    # Search for relevant images
                    st.session_state.images = search_bing_images(user_input)
                
                # Display result
                st.markdown("### Generated Content")
                st.markdown(st.session_state.generated_content)
                
                # Display images after the first paragraph
                if st.session_state.images:
                    st.markdown("### Related Images")
                    st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
                    for image in st.session_state.images:
                        st.markdown(f"""
                            <div class="image-card">
                                <img src="{image['url']}" alt="{image['title']}">
                                <p>{image['title']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
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
                    with st.spinner("Processing file..."):
                        # Initialize the model
                        model = genai.GenerativeModel(
                            model_name=st.session_state.model
                        )
                        
                        # Generate content
                        response = model.generate_content(content)
                        st.session_state.generated_content = response.text
                        
                        # Search for relevant images
                        st.session_state.images = search_bing_images(content[:100])  # Use first 100 chars for image search
                    
                    # Display result
                    st.markdown("### Generated Content")
                    st.markdown(st.session_state.generated_content)
                    
                    # Display images after the first paragraph
                    if st.session_state.images:
                        st.markdown("### Related Images")
                        st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
                        for image in st.session_state.images:
                            st.markdown(f"""
                                <div class="image-card">
                                    <img src="{image['url']}" alt="{image['title']}">
                                    <p>{image['title']}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)
