import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import json
import markdown
import random
import time
from datetime import datetime
import os
from jinja2 import Template
import re

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

def clean_filename(title):
    """Convert title to URL-friendly slug"""
    title = title.lower()
    title = re.sub(r'[^a-z0-9\s-]', '', title)
    title = re.sub(r'[-\s]+', '-', title)
    return title.strip('-')

def generate_blog_html(title, content, meta_description, images, site_name="My Blog", site_description=""):
    """Generate complete blog HTML using the template"""
    featured_image = images[0]["url"] if images else ""
    read_time = len(content.split()) // 200  # Assuming 200 words per minute reading speed
    
    # Format content with images
    content_with_images = format_content_with_images(content, images, title, meta_description)
    
    # Generate related articles (placeholder)
    related_articles = [
        {
            "title": "Related Article 1",
            "url": "#",
            "image": images[1]["url"] if len(images) > 1 else "",
            "excerpt": "Sample excerpt for related article 1"
        },
        {
            "title": "Related Article 2",
            "url": "#",
            "image": images[2]["url"] if len(images) > 2 else "",
            "excerpt": "Sample excerpt for related article 2"
        }
    ]
    
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

def process_bulk_topics(topics):
    """Process multiple topics and generate articles"""
    generated_articles = []
    
    for topic in topics:
        topic = topic.strip()
        if not topic:
            continue
            
        try:
            # Generate content
            model = genai.GenerativeModel(model_name=st.session_state.model)
            title = generate_engaging_title(model, topic)
            meta_description = generate_meta_description(model, topic, title)
            content = st.session_state.generated_content = model.generate_content(
                f"Write a comprehensive article about: {topic}"
            ).text
            
            # Search for images
            images = search_bing_images(topic)
            
            # Generate HTML
            html = generate_blog_html(
                title=title,
                content=content,
                meta_description=meta_description,
                images=images
            )
            
            # Create filename
            filename = f"{clean_filename(title)}.html"
            
            generated_articles.append({
                "title": title,
                "filename": filename,
                "html": html
            })
            
        except Exception as e:
            st.error(f"Error processing topic '{topic}': {str(e)}")
    
    return generated_articles

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
        with st.spinner("Generating articles..."):
            articles = process_bulk_topics(topics)
            
            # Create output directory
            output_dir = "generated_articles"
            os.makedirs(output_dir, exist_ok=True)
            
            # Save articles
            for article in articles:
                filepath = os.path.join(output_dir, article["filename"])
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(article["html"])
            
            st.success(f"Generated {len(articles)} articles in the '{output_dir}' directory!")
            
            # Create download links
            for article in articles:
                st.markdown(f"📄 [{article['title']}](generated_articles/{article['filename']})")

st.markdown('</div>', unsafe_allow_html=True)
