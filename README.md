# Extractor de Medidas - Sketch Cut Pro AI Assistant

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)

An AI-powered web application designed to automate the extraction of furniture measurements (Length, Width, Quantity) from handwritten notes and printed photos. It processes the extracted data and generates `.sct` files natively compatible with **Sketch Cut Pro**.

## Features

- **AI Image Processing**: Uses Google's Gemini 2.5 Flash model underneath to accurately read handwritten dimension notes.
- **Smart Unit Conversion**: Automatically detects if measurements are provided in Centimeters (cm) and rigorously converts them to absolute Millimeters (mm), as required by Sketch Cut Pro.
- **Multi-File Upload**: Supports batch processing. You can upload multiple note photos at once, and the application will sequentially append them all into a single file.
- **Editable UI**: Before exporting, users can review and easily live-edit the extracted measurements within the web interface.
- **SCT Generation**: One-click download of valid `.sct` files for direct import into your Sketch Cut software.

## Tech Stack

- **Backend**: Python, FastAPI, Uvicorn (ASGI)
- **AI Core**: `google-generativeai` (Gemini-2.5-Flash Vision model)
- **Frontend**: Lightweight HTML5/Javascript, Vanilla CSS (Tailwind styled layout), Phosphor Icons.
- **Templating**: Jinja2

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/sketchcut-ai-extractor.git
   cd sketchcut-ai-extractor/api
   ```

2. **Set up a Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file in the root `api/` directory and add your Google AI Studio API key:
   ```env
   GEMINI_API_KEY="your_google_gemini_api_key_here"
   ```

## Running the Application

### Local Web Server (Development)
You can run the FastAPI server using Uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Then, open your browser and navigate to `http://localhost:8000`.

### Production Deployment (VPS / Amazon EC2)

The most secure and robust way to deploy this application on a Linux server is using **Docker**:

1. Ensure `docker` and `docker-compose` are installed on your VPS.
2. Clone this repository on the server and `cd api`.
3. Create your `.env` file with the `GEMINI_API_KEY`.
4. Run the container in the background:
   ```bash
   docker-compose up -d
   ```
5. The application will be live at `http://YOUR_SERVER_IP:8000`. 
   *(Note: Remember to configure a reverse proxy like Nginx or Traefik for SSL/HTTPS in production).*

## How it works

1. End-user uploads images containing width and length notes through the `/` frontend.
2. The WebApp packages the images into a sequence and streams them to the `/api/extract` REST endpoint.
3. The server uses `Gemini 2.5 Flash` to process the images alongside a strict instructional system prompt enforcing ordering, millimeter conversions, and a JSON format invariant.
4. Extracted components are temporarily staged in the interactive HTML datatable.
5. Emitting the 'Export' event triggers `/api/generate-sct`, executing `sct_generator.py` to compile the standard byte-format layout expected by Sketch Cut Pro.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
