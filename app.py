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
    """Generate a professional and engaging title with high CPM and low competition focus"""
    current_time = int(time.time())
    title_prompt = f"""
    As an expert headline writer specializing in viral content and unique angles, create ONE compelling title about: {topic}
    Current timestamp: {current_time}

    Requirements for the perfect title:
    - Must be completely unique and never-before-seen
    - Use unexpected word combinations or metaphors
    - Include specific, unusual numbers (avoid round numbers)
    - Target length: 45-60 characters
    - Must create intense curiosity
    
    Use one of these unique title formats:
    - "The {number} Minute {topic} Hack That {unexpected benefit}"
    - "Why {common belief} Is Actually {surprising truth}: {specific data point}"
    - "How {unusual method} Can {desired outcome} ({specific metric})"
    - "The Forgotten {ancient/historical reference} Secret to {modern topic}"
    - "What {unexpected profession} Can Teach Us About {topic}"
    
    Advanced techniques to use:
    - Combine concepts from different fields
    - Use contrast between old and new
    - Include specific, unusual metrics
    - Reference unexpected experts or sources
    - Create intrigue through partial revelation
    
    Return ONLY the title, no explanations or additional text.
    Make it impossible to resist clicking.
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
        # Add randomization to search query
        variations = [
            f"{query} {random.choice(['guide', 'tutorial', 'tips', 'examples', 'ideas'])}",
            f"{query} {random.choice(['professional', 'modern', 'creative', 'innovative'])}",
            f"{query} {random.choice(['2024', 'latest', 'trending', 'best'])}"
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
        
        # Shuffle and return unique images
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
    # Split content into paragraphs
    paragraphs = [p for p in content.split('\n\n') if p.strip()]
    
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
        if image_index < len(images) - 5:  # Reserve last 5 images for gallery
            formatted_content += f'<img src="{images[image_index]["url"]}" alt="{images[image_index]["title"]}" class="content-image">'
    
    # Add image gallery
    formatted_content += '<div class="gallery-title">Image Gallery</div>'
    formatted_content += '<div class="image-gallery">'
    for img in images[-5:]:  # Use last 5 images for gallery
        formatted_content += f'<img src="{img["url"]}" alt="{img["title"]}" class="gallery-image" onclick="window.open(this.src)">'
    formatted_content += '</div>'
    
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
if 'generated_title' not in st.session_state:
    st.session_state.generated_title = None

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
                    
                    # Generate engaging title first
                    st.session_state.generated_title = generate_engaging_title(model, user_input)
                    
                    # Generate content with proper configuration
                    current_time = int(time.time())
                    content_prompt = f"""
                    Write a comprehensive, engaging, and detailed 3000-word article about: {user_input}
                    Use this title: {st.session_state.generated_title}
                    Current timestamp: {current_time}
                    
                    Article Requirements:
                    - Exactly 3000 words
                    - Divide into clear sections with subheadings
                    - Include expert insights and analysis
                    - Use storytelling techniques
                    - Add real-world examples
                    - Include data and statistics
                    - Make it highly engaging and informative
                    - Use a conversational yet professional tone
                    - Break down complex concepts
                    - End with actionable takeaways
                    
                    Structure:
                    1. Compelling introduction (300 words)
                    2. Background/Context (400 words)
                    3. Main analysis (1500 words)
                    4. Expert insights (400 words)
                    5. Practical applications (300 words)
                    6. Conclusion with actionable steps (100 words)
                    
                    Make every section unique and valuable.
                    Focus on depth and quality.
                    """
                    
                    generation_config = genai.types.GenerationConfig(
                        candidate_count=1,
                        temperature=0.8,
                        top_p=0.95,
                        top_k=64,
                    )
                    
                    response = model.generate_content(content_prompt, generation_config=generation_config)
                    st.session_state.generated_content = response.text
                    
                    # Search for relevant images with increased count
                    st.session_state.images = search_bing_images(user_input, num_images=15)
                
                # Format and display content with interleaved images and gallery
                formatted_content = format_content_with_images(
                    st.session_state.generated_content,
                    st.session_state.images,
                    st.session_state.generated_title
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
                        
                        # Generate engaging title first
                        st.session_state.generated_title = generate_engaging_title(model, content[:200])
                        
                        # Generate content with proper configuration
                        current_time = int(time.time())
                        content_prompt = f"""
                        Write a comprehensive, engaging, and detailed 3000-word article about this topic: {content}
                        Use this title: {st.session_state.generated_title}
                        Current timestamp: {current_time}
                        
                        Article Requirements:
                        - Exactly 3000 words
                        - Divide into clear sections with subheadings
                        - Include expert insights and analysis
                        - Use storytelling techniques
                        - Add real-world examples
                        - Include data and statistics
                        - Make it highly engaging and informative
                        - Use a conversational yet professional tone
                        - Break down complex concepts
                        - End with actionable takeaways
                        
                        Structure:
                        1. Compelling introduction (300 words)
                        2. Background/Context (400 words)
                        3. Main analysis (1500 words)
                        4. Expert insights (400 words)
                        5. Practical applications (300 words)
                        6. Conclusion with actionable steps (100 words)
                        
                        Make every section unique and valuable.
                        Focus on depth and quality.
                        """
                        
                        generation_config = genai.types.GenerationConfig(
                            candidate_count=1,
                            temperature=0.8,
                            top_p=0.95,
                            top_k=64,
                        )
                        
                        response = model.generate_content(content_prompt, generation_config=generation_config)
                        st.session_state.generated_content = response.text
                        
                        # Search for relevant images with increased count
                        st.session_state.images = search_bing_images(content[:100], num_images=15)
                    
                    # Format and display content with interleaved images and gallery
                    formatted_content = format_content_with_images(
                        st.session_state.generated_content,
                        st.session_state.images,
                        st.session_state.generated_title
                    )
                    st.markdown(formatted_content, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)
