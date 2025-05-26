import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import json
import markdown
import random
import time

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
    .image-gallery {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 20px;
        padding: 20px 0;
    }
    .gallery-image {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 8px;
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
        z-index: 1;
    }
    .gallery-image:hover {
        transform: scale(2);
        z-index: 999;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
    }
    .gallery-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 40px 0 20px 0;
        color: #1E40AF;
    }
</style>
""", unsafe_allow_html=True)

def generate_engaging_title(model, topic):
    """Generate a professional and SEO-friendly title"""
    current_time = int(time.time())
    title_prompt = f"""
    Create one engaging and professional title about: {topic}
    Current timestamp: {current_time}

    Make it:
    - Natural and compelling
    - 50-60 characters long
    - Include the main topic naturally
    - Professional but engaging
    - Unique and original
    - Focus on value
    - Include specific benefits when relevant
    
    Return only the title itself, no additional text or formatting.
    """
    
    generation_config = genai.types.GenerationConfig(
        candidate_count=1,
        temperature=0.9,
        top_p=0.95,
        top_k=64,
    )
    
    response = model.generate_content(title_prompt, generation_config=generation_config)
    return response.text.strip().replace('"', '').replace('#', '').strip()

def search_bing_images(query, num_images=15):
    try:
        variations = [
            f"{query} {random.choice(['professional', 'expert', 'guide', 'tutorial'])}",
            f"{query} {random.choice(['best practices', 'industry leading', 'top rated'])}",
            f"{query} {random.choice(['2024 trends', 'latest developments', 'current'])}"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        all_images = []
        for variation in variations:
            search_url = f'https://www.bing.com/images/search?q={variation}&form=HDRSC2'
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for img in soup.find_all('a', class_='iusc'):
                try:
                    m = json.loads(img['m'])
                    image_url = m['murl']
                    all_images.append({
                        'url': image_url,
                        'title': m.get('t', 'Image')
                    })
                except:
                    continue
        
        random.shuffle(all_images)
        seen_urls = set()
        unique_images = []
        for img in all_images:
            if img['url'] not in seen_urls and len(unique_images) < num_images:
                seen_urls.add(img['url'])
                unique_images.append(img)
        
        return unique_images
    except Exception as e:
        st.error(f"Error searching images: {str(e)}")
        return []

def format_content_with_images(content, images, title):
    paragraphs = [p for p in content.split('\n\n') if p.strip()]
    formatted_content = f'<div class="content-title">{title}</div>'
    
    if images:
        formatted_content += f'<img src="{images[0]["url"]}" alt="{images[0]["title"]}" class="content-image">'
    
    for i, paragraph in enumerate(paragraphs):
        # Remove markdown headings and formatting
        clean_paragraph = paragraph.replace('#', '').strip()
        clean_paragraph = clean_paragraph.replace('***', '').replace('**', '').replace('*', '')
        formatted_content += f'<div class="content-paragraph">{clean_paragraph}</div>'
        
        image_index = i + 1
        if image_index < len(images) - 5:
            formatted_content += f'<img src="{images[image_index]["url"]}" alt="{images[image_index]["title"]}" class="content-image">'
    
    formatted_content += '<div class="gallery-title">Related Images</div>'
    formatted_content += '<div class="image-gallery">'
    for img in images[-6:]:
        formatted_content += f'<img src="{img["url"]}" alt="{img["title"]}" class="gallery-image" onclick="window.open(this.src)">'
    formatted_content += '</div>'
    
    return formatted_content

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'model' not in st.session_state:
    st.session_state.model = 'gemini-1.5-pro'
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None
if 'images' not in st.session_state:
    st.session_state.images = []
if 'generated_title' not in st.session_state:
    st.session_state.generated_title = None

# App title
st.markdown('<div class="main-title">Professional Content Generator</div>', unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.markdown("### Configuration")
    
    api_key = st.text_input(
        "Enter your Gemini API key:",
        type="password",
        value=st.session_state.api_key
    )
    
    model = st.selectbox(
        "Select Model:",
        ["gemini-1.5-pro", "gemini-1.5-flash"],
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
st.markdown("### Generate Professional Content")
st.markdown('<div class="card">', unsafe_allow_html=True)

input_method = st.radio(
    "Choose input method:",
    ["Enter text manually", "Upload a file"],
    horizontal=True
)

def generate_content(input_text):
    if not st.session_state.api_key:
        st.error("Please configure your API key in the sidebar first.")
        return
    elif not input_text:
        st.error("Please enter some text to process.")
        return
    
    try:
        with st.spinner("Generating professional content..."):
            model = genai.GenerativeModel(model_name=st.session_state.model)
            st.session_state.generated_title = generate_engaging_title(model, input_text)
            
            current_time = int(time.time())
            content_prompt = f"""
            Write a comprehensive and engaging article about: {input_text}
            Title: {st.session_state.generated_title}
            Current timestamp: {current_time}
            
            Guidelines:
            - Write naturally, as if for a professional blog or magazine
            - Length: 3000 words
            - Include relevant examples and case studies
            - Share practical advice and actionable tips
            - Use a conversational yet professional tone
            - Break complex topics into digestible sections
            - Include relevant data and expert insights
            - Focus on providing value to the reader
            
            Structure the content naturally with clear sections, but do not use explicit headings or markdown formatting.
            Make the content flow smoothly from one topic to the next.
            Focus on readability and engagement while maintaining professionalism.
            """
            
            generation_config = genai.types.GenerationConfig(
                candidate_count=1,
                temperature=0.8,
                top_p=0.95,
                top_k=64,
            )
            
            response = model.generate_content(content_prompt, generation_config=generation_config)
            st.session_state.generated_content = response.text
            st.session_state.images = search_bing_images(input_text, num_images=15)
        
        formatted_content = format_content_with_images(
            st.session_state.generated_content,
            st.session_state.images,
            st.session_state.generated_title
        )
        st.markdown(formatted_content, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")

if input_method == "Enter text manually":
    user_input = st.text_area(
        "Enter your topic or keywords:",
        height=150,
        placeholder="Enter the topic you want to create content about..."
    )
    
    if st.button("Generate Professional Content"):
        generate_content(user_input)
else:
    uploaded_file = st.file_uploader("Upload a text file:", type=["txt"])
    
    if uploaded_file is not None:
        content = uploaded_file.read().decode("utf-8")
        if st.button("Process File"):
            generate_content(content)

st.markdown('</div>', unsafe_allow_html=True)
