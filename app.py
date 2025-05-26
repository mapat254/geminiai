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
    .content-image {
        width: 100%;
        max-height: 400px;
        object-fit: cover;
        border-radius: 8px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .content-paragraph {
        margin: 20px 0;
        line-height: 1.8;
        font-size: 1.1rem;
    }
    .content-title {
        font-size: 2rem;
        font-weight: 700;
        margin: 20px 0;
        color: #1E40AF;
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

def format_content_with_images(content, images):
    # Split content into paragraphs
    paragraphs = [p for p in content.split('\n\n') if p.strip()]
    
    # Format title (first line) separately
    title = paragraphs[0].replace('#', '').strip()
    paragraphs = paragraphs[1:]
    
    # Initialize formatted content with title
    formatted_content = f'<div class="content-title">{title}</div>'
    
    # Add first image after title
    if images:
        formatted_content += f'<img src="{images[0]["url"]}" alt="{images[0]["title"]}" class="content-image">'
    
    # Interleave remaining paragraphs and images
    for i, paragraph in enumerate(paragraphs):
        # Add paragraph
        formatted_content += f'<div class="content-paragraph">{paragraph}</div>'
        
        # Add image if available (skip first image as it's already used)
        image_index = i + 1
        if image_index < len(images):
            formatted_content += f'<img src="{images[image_index]["url"]}" alt="{images[image_index]["title"]}" class="content-image">'
    
    return formatted_content

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
                
                # Format and display content with interleaved images
                formatted_content = format_content_with_images(
                    st.session_state.generated_content,
                    st.session_state.images
                )
                st.markdown(formatted_content, unsafe_allow_html=True)
                
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
                        st.session_state.images = search_bing_images(content[:100])
                    
                    # Format and display content with interleaved images
                    formatted_content = format_content_with_images(
                        st.session_state.generated_content,
                        st.session_state.images
                    )
                    st.markdown(formatted_content, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)
