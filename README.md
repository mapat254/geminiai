# AI Blog Generator

A powerful Streamlit application for generating professional blog articles with AI and finding relevant images.

## Features

- **Intuitive Interface**: Clean, modern UI for easy article generation
- **Language Detection**: Automatically detects and generates content in the detected language
- **API Key Management**: Handles multiple API keys for quota management
- **Image Search**: Finds relevant images for your articles
- **Customizable Generation**: Adjust temperature, output length, and other parameters
- **Preview & Download**: Preview generated content and download as HTML or ZIP

## Requirements

The application requires the following Python packages:

```
streamlit==1.30.0
langdetect==1.0.9
langcodes==3.3.0
google-generativeai==0.3.1
markdown==3.5
requests==2.31.0
beautifulsoup4==4.12.2
python-dotenv==1.0.0
```

## Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

## Usage

1. Enter your Gemini API key(s) in the sidebar
2. Enter subjects manually or upload a text file with subjects
3. Adjust generation settings as needed
4. Click "Start Generation" to begin
5. Preview and download generated articles

## Environment Variables

You can use a `.env` file to store your API keys:

```
GEMINI_API_KEY=your_api_key_here
```

## License

MIT
