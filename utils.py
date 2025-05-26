import os
import requests
from bs4 import BeautifulSoup
import json
import urllib.parse
from langdetect import detect, DetectorFactory
from langcodes import Language
import google.generativeai as genai

# Ensure consistent language detection
DetectorFactory.seed = 0

def detect_language(subject):
    """Detect the language of a given subject"""
    try:
        lang_code = detect(subject)
        lang_name = Language.get(lang_code).display_name()
        return lang_name
    except:
        return "English"  # Default to English if detection fails

def read_api_keys(filename="apikey.txt"):
    """Read API keys from a file"""
    if not os.path.exists(filename):
        return []
    
    with open(filename, "r") as file:
        keys = [line.strip() for line in file if line.strip()]
    return keys

def switch_api_key(keys, current_index):
    """Switch to the next API key"""
    if not keys:
        return None, 0
    
    next_index = (current_index + 1) % len(keys)
    return keys[next_index], next_index

def configure_gemini(api_key):
    """Configure the Gemini API with the given key"""
    genai.configure(api_key=api_key)
    
    # Default generation config
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    
    return generation_config

def generate_title(session, subject, language):
    """Generate a title for the subject in the specified language"""
    title_prompt = (
        f"Forget previous instructions. You are a professional clickbait-style blog title writer in {language}. "
        f"Come up with 1 unique, emotional, and curiosity-driven blog title for the topic: \"{subject}\". "
        f"The title must be under 60 characters, avoid clichés, and spark reader curiosity. "
        f"Use metaphor, emotion, or an unexpected twist. Do not repeat the subject word exactly."
    )
    response = session.send_message(title_prompt)
    return response.text.strip().replace('"', '').replace("**", "").replace("##", "")

def generate_article(session, title, subject, language, is_seo=False):
    """Generate an article based on the title and subject"""
    if is_seo:
        article_prompt = (
            f"Forget previous instructions. You are an SEO expert and content writer in {language}. "
            f"Write a 1600-word article with the keyword \"{title}\". Include the keyword 4 times. "
            f"Format it professionally using markdown with proper H1, H2, and H3 headings. "
            f"Include a meta description and optimize for search engines."
        )
    else:
        article_prompt = (
            f"Ignore all previous instructions. You are an expert Pinterest content writer and blogger in {language}. "
            f"Write a blog post of around 3000 words for the title \"{title}\" that is inspiring, informative, "
            f"and visually descriptive. Use a storytelling tone, include tips or how-tos when relevant, and format it professionally using markdown. "
            f"Use short paragraphs and bold important points or keywords to enhance readability. "
            f"Include lists or steps if applicable to help Pinterest readers absorb the content quickly."
        )
    
    response = session.send_message(article_prompt)
    return response.text

def get_soup(url, header):
    """Get BeautifulSoup object from a URL"""
    response = requests.get(url, headers=header)
    soup = BeautifulSoup(response.content, "html.parser")
    return soup

def bing_image_search(query, max_images=10):
    """Search for images using Bing Image Search"""
    try:
        query = '+'.join(query.split())
        url = f"http://www.bing.com/images/search?q={query}&FORM=HDRSC2"
        header = {'User-Agent': "Mozilla/5.0"}
        soup = get_soup(url, header)
        image_results_raw = soup.find_all("a", {"class": "iusc"})[:max_images]
        
        image_html_list = []
        image_data_list = []
        
        for image_result_raw in image_results_raw:
            m = json.loads(image_result_raw["m"])
            murl = m["murl"]  # URL of the image
            mdesc = m.get("desc", "No description available")  # Description of the image if available
            image_name = urllib.parse.urlsplit(murl).path.split("/")[-1]
            
            # HTML representation for embedding
            image_html_list.append(
                f'<div style="text-align: center; margin: 20px 0;">'
                f'<img src="{murl}" alt="{image_name}" width="600" height="400" style="border: 2px solid black;">'
                f'<div style="font-size: 14px; color: gray;">{mdesc}</div>'
                f'</div>'
            )
            
            # Data representation for processing
            image_data_list.append({
                'url': murl,
                'description': mdesc,
                'filename': image_name
            })
        
        return image_html_list, image_data_list
    except Exception as e:
        print(f"Error in image search: {str(e)}")
        return [], []

def format_article_with_images(article, image_html_list, max_images=7):
    """Format the article with images inserted at appropriate positions"""
    # Split article into paragraphs
    paragraphs = article.split('\n\n')
    
    # Add read more tag after first paragraph
    if paragraphs:
        paragraphs[0] += ' <span><!--more--></span>'
    
    # Insert images throughout the article
    images_to_use = image_html_list[:max_images]
    for i, image_html in enumerate(images_to_use):
        # Calculate position - distribute images evenly
        position = min(i + 2, len(paragraphs) - 1)
        paragraphs.insert(position, image_html)
    
    # Rejoin paragraphs
    formatted_article = '\n\n'.join(paragraphs)
    return formatted_article

def generate_html_template(title, article, images):
    """Generate a complete HTML template for the article"""
    clean_title = title.replace("**", "").replace("##", "").strip()
    
    image_urls = []
    for img in images:
        try:
            url = img.split('src=\"')[1].split('\"')[0]
            image_urls.append(url)
        except:
            continue
    
    main_image = image_urls[0] if image_urls else ""
    
    html_output = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{clean_title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 20px;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border: 4px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        img:hover {{
            transform: scale(1.02);
        }}
        .image-container {{
            text-align: center;
            margin: 30px 0;
        }}
        .image-description {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
        h2, h3 {{
            color: #222;
        }}
        strong {{
            color: #C71585;
        }}
        .slideshow-container {{
            text-align: center;
            margin: 40px 0;
        }}
        .slideshow-container .main-image img {{
            width: 100%;
            max-width: 700px;
            height: auto;
            border: 4px solid #ddd;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        }}
        .slideshow-container .thumbnails {{
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 15px;
            gap: 10px;
        }}
        .slideshow-container .thumbnails img {{
            width: 80px;
            height: 60px;
            object-fit: cover;
            border: 2px solid transparent;
            border-radius: 5px;
            cursor: pointer;
            transition: 0.3s;
        }}
        .slideshow-container .thumbnails img:hover {{
            border-color: #C71585;
        }}
    </style>
</head>
<body>
<h1>{clean_title}</h1>

{article}

<div class="slideshow-container">
    <div class="main-image" id="mainImageContainer">
        <img id="mainImage" src="{main_image}" alt="Main Image">
    </div>
    <div class="thumbnails" id="thumbnails">
        {''.join([f'<img src="{url}" onclick="showImage(this)" alt="Thumbnail">' for url in image_urls])}
    </div>
</div>

<script>
    function showImage(elem) {{
        document.getElementById("mainImage").src = elem.src;
    }}
</script>

</body>
</html>
"""
    return html_output
