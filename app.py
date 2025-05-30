import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import json
import random
import time
from datetime import datetime
import os
from jinja2 import Template
import re
import shutil
import zipfile

# Load environment variables
load_dotenv()

# App configuration
st.set_page_config(
    page_title="AI Blog Generator",
    page_icon="✨",
    layout="wide"
)

# Load blog template
with open('templates/blog_template.html', 'r') as f:
    BLOG_TEMPLATE = Template(f.read())

def generate_engaging_title(model, topic):
    """Generate a professional and SEO-optimized title"""
    title_prompt = f"""
    Create one SEO-optimized title about: {topic}

    Requirements:
    - Include primary keyword naturally
    - 50-60 characters (optimal for search engines)
    - Use power words that drive clicks
    - Include numbers or specific benefits when relevant
    - Match search intent
    - Avoid clickbait while maintaining interest
    
    Return only the optimized title, no additional text.
    """
    
    generation_config = {
        "temperature": 0.8,
        "top_p": 0.95,
        "top_k": 64,
    }
    
    response = model.generate_content(title_prompt, generation_config=generation_config)
    return response.text.strip().replace('"', '').replace('#', '').strip()

def generate_meta_description(model, topic, title):
    """Generate an SEO-optimized meta description"""
    meta_prompt = f"""
    Create a compelling meta description for an article about {topic} with title: {title}

    Requirements:
    - 150-160 characters long
    - Include primary keyword naturally
    - Clear value proposition
    - Call-to-action
    - Match search intent
    
    Return only the meta description, no additional text.
    """
    
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 64,
    }
    
    response = model.generate_content(meta_prompt, generation_config=generation_config)
    return response.text.strip()

def generate_article_content(model, topic, title):
    """Generate comprehensive article content in HTML format"""
    content_prompt = f"""
    Write a comprehensive, SEO-optimized article about: {topic}
    Title: {title}
    
    Requirements:
    - 2000-3000 words
    - Return the content in clean HTML format using these tags:
      - <h2> for main sections
      - <h3> for subsections
      - <p> for paragraphs
      - <ul> and <li> for unordered lists
      - <ol> and <li> for ordered lists
      - <strong> for emphasis
      - <em> for italics
      - <blockquote> for quotes
    - Include relevant statistics and examples
    - Make content visually appealing with proper spacing
    - Include a strong introduction and conclusion
    - Add calls-to-action where appropriate
    - Use proper HTML structure
    - NO markdown formatting
    
    Return ONLY the HTML content, no additional text or formatting.
    """
    
    generation_config = {
        "temperature": 0.8,
        "top_p": 0.95,
        "top_k": 64,
    }
    
    response = model.generate_content(content_prompt, generation_config=generation_config)
    return response.text

def clean_filename(title):
    """Convert title to URL-friendly slug"""
    title = title.lower()
    title = re.sub(r'[^a-z0-9\s-]', '', title)
    title = re.sub(r'[-\s]+', '-', title)
    return title.strip('-')

def search_bing_images(query, num_images=15):
    """Search for images using Bing"""
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
                images.append({
                    'url': m['murl'],
                    'title': m.get('t', 'Image')
                })
            except:
                continue
            
            if len(images) >= num_images:
                break
        
        return images
    except Exception as e:
        st.error(f"Error searching images: {str(e)}")
        return []

def format_content_with_images(content, images, title, meta_description):
    """Format content with images interspersed"""
    # Split content into sections (assuming they're separated by </h2> tags)
    sections = content.split('</h2>')
    formatted_content = []
    
    # Add meta description
    formatted_content.append(f'<div class="meta-description">{meta_description}</div>')
    
    # Add featured image
    if images:
        formatted_content.append(f'<div class="featured-image-container"><img src="{images[0]["url"]}" alt="{title}" class="featured-image"></div>')
    
    # Intersperse content with images
    image_index = 1
    for i, section in enumerate(sections):
        if i == 0:  # First section
            formatted_content.append(section + '</h2>' if i < len(sections)-1 else section)
        else:
            formatted_content.append(section + '</h2>' if i < len(sections)-1 else section)
            
            # Add an image after every other section
            if i % 2 == 0 and image_index < len(images):
                formatted_content.append(
                    f'<div class="content-image-container">'
                    f'<img src="{images[image_index]["url"]}" alt="{images[image_index]["title"]}" class="content-image">'
                    f'<p class="image-caption">{images[image_index]["title"]}</p>'
                    f'</div>'
                )
                image_index += 1
    
    return '\n'.join(formatted_content)

def generate_blog_html(title, content, meta_description, images, site_name="My Blog", site_description="", all_articles=None):
    """Generate complete blog HTML using the template"""
    featured_image = images[0]["url"] if images else ""
    read_time = len(content.split()) // 200  # Assuming 200 words per minute reading speed
    
    # Format content with images
    content_with_images = format_content_with_images(content, images, title, meta_description)
    
    # Generate related articles from actual articles
    related_articles = []
    if all_articles:
        # Filter out current article and get up to 2 random articles
        other_articles = [a for a in all_articles if a["title"] != title]
        selected_articles = random.sample(other_articles, min(2, len(other_articles)))
        
        for article in selected_articles:
            related_articles.append({
                "title": article["title"],
                "url": article["filename"],
                "image": images[1]["url"] if len(images) > 1 else "",
                "excerpt": meta_description[:100] + "..."
            })
    
    # If we don't have enough related articles, pad with placeholders
    while len(related_articles) < 2:
        related_articles.append({
            "title": "Explore More Articles",
            "url": "/",
            "image": images[-1]["url"] if images else "",
            "excerpt": "Discover more interesting articles on our site"
        })
    
    # Render template
    html = BLOG_TEMPLATE.render(
        title=title,
        content=content_with_images,
        meta_description=meta_description,
        featured_image=featured_image,
        date=datetime.now().strftime("%B %d, %Y"),
        read_time=read_time,
        site_name=site_name,
        site_description=site_description,
        year=datetime.now().year,
        related_articles=related_articles
    )
    
    return html

def create_github_export(articles, site_name, site_description):
    """Create a GitHub-ready export of the blog"""
    # Create temporary directory for export
    export_dir = "github_export"
    if os.path.exists(export_dir):
        shutil.rmtree(export_dir)
    os.makedirs(export_dir)
    
    # Copy template assets
    os.makedirs(os.path.join(export_dir, 'templates'))
    shutil.copy('templates/blog_template.html', os.path.join(export_dir, 'templates'))
    
    # Create articles directory
    articles_dir = os.path.join(export_dir, 'articles')
    os.makedirs(articles_dir)
    
    # Save articles
    for article in articles:
        filepath = os.path.join(articles_dir, article["filename"])
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(article["html"])
    
    # Create index.html
    index_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{site_name}</title>
        <meta name="description" content="{site_description}">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-50">
        <header class="bg-white shadow-lg py-6">
            <div class="max-w-7xl mx-auto px-4">
                <h1 class="text-3xl font-bold text-gray-900">{site_name}</h1>
                <p class="mt-2 text-gray-600">{site_description}</p>
            </div>
        </header>
        
        <main class="max-w-7xl mx-auto px-4 py-12">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
    """
    
    # Add article cards to index
    for article in articles:
        index_content += f"""
                <a href="articles/{article['filename']}" class="block">
                    <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow">
                        <div class="p-6">
                            <h2 class="text-xl font-semibold mb-2">{article['title']}</h2>
                            <p class="text-gray-600">Click to read more...</p>
                        </div>
                    </div>
                </a>
        """
    
    index_content += """
            </div>
        </main>
        
        <footer class="bg-gray-800 text-white py-8 mt-12">
            <div class="max-w-7xl mx-auto px-4 text-center">
                <p>&copy; 2024 All rights reserved.</p>
            </div>
        </footer>
    </body>
    </html>
    """
    
    with open(os.path.join(export_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    # Create README.md
    readme_content = f"""# {site_name}

A collection of SEO-optimized blog articles generated with AI.

## Articles

{chr(10).join(f'- [{article["title"]}](articles/{article["filename"]})' for article in articles)}

## About

{site_description}

## Setup

1. Clone this repository
2. Open index.html in your browser
3. Deploy to GitHub Pages for online access

## License

MIT
"""
    
    with open(os.path.join(export_dir, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Create zip file
    shutil.make_archive(export_dir, 'zip', export_dir)
    
    return f"{export_dir}.zip"

def process_bulk_topics(topics):
    """Process multiple topics and generate articles"""
    generated_articles = []
    
    for topic in topics:
        topic = topic.strip()
        if not topic:
            continue
            
        try:
            with st.spinner(f"Generating article for: {topic}"):
                # Generate content
                model = genai.GenerativeModel(model_name=st.session_state.model)
                title = generate_engaging_title(model, topic)
                meta_description = generate_meta_description(model, topic, title)
                content = generate_article_content(model, topic, title)
                
                # Search for images
                images = search_bing_images(topic)
                
                # Generate HTML with access to all previously generated articles
                html = generate_blog_html(
                    title=title,
                    content=content,
                    meta_description=meta_description,
                    images=images,
                    site_name=st.session_state.get('site_name', 'My Blog'),
                    site_description=st.session_state.get('site_description', ''),
                    all_articles=generated_articles  # Pass existing articles
                )
                
                # Create filename
                filename = f"{clean_filename(title)}.html"
                
                generated_articles.append({
                    "title": title,
                    "filename": filename,
                    "html": html,
                    "meta_description": meta_description,
                    "content": content  # Store the content for regenerating HTML later
                })
            
        except Exception as e:
            st.error(f"Error processing topic '{topic}': {str(e)}")
    
    # After all articles are generated, update their related articles sections
    for i, article in enumerate(generated_articles):
        # Regenerate HTML with access to all articles
        html = generate_blog_html(
            title=article["title"],
            content=article["content"],
            meta_description=article["meta_description"],
            images=search_bing_images(article["title"]),  # Re-fetch images if needed
            site_name=st.session_state.get('site_name', 'My Blog'),
            site_description=st.session_state.get('site_description', ''),
            all_articles=generated_articles
        )
        generated_articles[i]["html"] = html
    
    return generated_articles

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'model' not in st.session_state:
    st.session_state.model = 'gemini-1.5-pro'

# Main UI
st.markdown('<div class="main-title">SEO-Optimized Blog Generator</div>', unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.markdown("### Configuration")
    
    api_key = st.text_input(
        "Enter your Gemini API key:",
        type="password",
        value=st.session_state.get('api_key', '')
    )
    
    site_name = st.text_input(
        "Site Name:",
        value=st.session_state.get('site_name', 'My Blog')
    )
    
    site_description = st.text_area(
        "Site Description:",
        value=st.session_state.get('site_description', '')
    )
    
    if st.button("Save Configuration"):
        if api_key:
            st.session_state.api_key = api_key
            st.session_state.site_name = site_name
            st.session_state.site_description = site_description
            genai.configure(api_key=api_key)
            st.success("Configuration saved successfully!")
        else:
            st.error("Please enter an API key.")

# Main content area
st.markdown("### Generate Blog Articles")
st.markdown('<div class="card">', unsafe_allow_html=True)

topics_text = st.text_area(
    "Enter topics (one per line):",
    height=150,
    placeholder="Enter your topics here, one per line..."
)

if st.button("Generate Articles"):
    if not st.session_state.get('api_key'):
        st.error("Please configure your API key in the sidebar first.")
    elif not topics_text:
        st.error("Please enter at least one topic.")
    else:
        topics = topics_text.split('\n')
        
        # Process topics and generate articles
        articles = process_bulk_topics(topics)
        
        if articles:
            # Create GitHub-ready export
            export_file = create_github_export(
                articles,
                st.session_state.get('site_name', 'My Blog'),
                st.session_state.get('site_description', '')
            )
            
            # Provide download link
            with open(export_file, 'rb') as f:
                st.download_button(
                    label="📦 Download GitHub-ready package",
                    data=f,
                    file_name="blog_export.zip",
                    mime="application/zip"
                )
            
            st.success(f"""
            ✅ Generated {len(articles)} articles successfully!
            
            To deploy to GitHub:
            1. Download the zip file
            2. Extract the contents
            3. Create a new GitHub repository
            4. Upload the extracted files
            5. Enable GitHub Pages in repository settings
            """)

st.markdown('</div>', unsafe_allow_html=True)
