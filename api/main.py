import os
from tempfile import NamedTemporaryFile
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import time

from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables de entorno desde el archivo .env
load_dotenv()

from sct_generator import generate_sct, Part

app = FastAPI(title="SCT Extractor API")

# Setup Jinja2 for serving the frontend
templates = Jinja2Templates(directory="templates")

# Initialize Gemini Client
import os
try:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    else:
        print("Warning: No API Key found.")
except Exception as e:
    print(f"Warning: Could not initialize GenAI client. Ensure GOOGLE_API_KEY or GEMINI_API_KEY is set. {e}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

import traceback

@app.post("/api/extract")
async def extract_measurements(files: List[UploadFile] = File(...)):
    """Receives one or more images, passing them to an LLM Vision model to extract cuts."""
    try:
        temp_paths = []
        uploaded_files = []
        
        # Save temp files and upload to Gemini
        for file in files:
            with NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
                content = await file.read()
                temp.write(content)
                temp_paths.append(temp.name)
            
            myfile = genai.upload_file(temp_paths[-1])
            uploaded_files.append(myfile)
            
        # Prompt instructing the model to return a structured JSON list of parts
        prompt = """
        You are an expert at interpreting handwritten or printed notes for melamine wood cutting.
        Analyze the provided image(s) and extract the combined list of pieces to be cut.
        Rules:
        1. Each piece must have a 'length' (dimension along the wood grain), a 'width' (dimension against the grain), and a 'quantity'.
        2. IMPORTANT INVARIANT: Length and Width are always written sequentially as "Length x Width" or "Length Width". 
        3. Length is NOT necessarily larger than width. Do not swap them based on size.
        4. The list format will typically be either "Quantity - Length - Width" OR "Length - Width - Quantity".
        5. EXTREMELY CRITICAL CONVERSION RULE: Sketch Cut Pro REQUIRES ALL measurements in pure MILLIMETERS (mm), but notes are very often in Centimeters (cm).
           - Step A: Analyze the numbers. If you see decimals like 15.4, or numbers that are too small to be millimeters for furniture (like 20, 45, 80, 150), they are CENTIMETERS.
           - Step B: If the numbers are in CENTIMETERS, you MUST multiply EVERY length and width by 10 to convert them to MILLIMETERS (e.g., 15.4 cm -> 154 mm, 80 cm -> 800 mm). This is absolutely mandatory.
           - Step C: Ensure your final output values are strictly INTEGERS representing MILLIMETERS. Do not output decimals.
        6. AGGREGATION & ORDERING: Aggregate ALL pieces found across ALL provided images into a single flat list. You MUST extract and append the measurements strictly in the sequential order of the images provided (e.g., all cuts from Image 1 first, followed by all cuts from Image 2, etc.). Do not sort them.
        7. Return strictly a flat JSON array, where each element is an object with keys: length, width, quantity (all integers). Do not return markdown or any text outside the JSON.
        """
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            uploaded_files + [prompt],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        
        # Cleanup temp files
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        try:
            data = json.loads(response.text)
            parts = []
            for item in data:
                l = int(item.get('length', 0))
                w = int(item.get('width', 0))
                    
                parts.append(Part(
                    length=l,
                    width=w,
                    quantity=int(item.get('quantity', 1))
                ))
            return {"parts": [p.dict() for p in parts]}
        except Exception as e:
            error_msg = str(e)
            if "Quota exceeded" in error_msg or "429" in error_msg:
                raise Exception("Límite de API gratuito excedido. Por favor, intenta de nuevo en un minuto o añade facturación a tu cuenta de Google AI Studio.")
            print(f"Failed to parse LLM response: {error_msg}\nRaw LLM Text: {response.text}")
            raise Exception(f"Error parseando resultados de la IA: {error_msg}")
            
    except Exception as e:
        traceback.print_exc()
        # Ensure cleanup on major outer failure
        if 'temp_paths' in locals():
            for tp in temp_paths:
                if os.path.exists(tp):
                     os.remove(tp)
        raise HTTPException(status_code=500, detail=f"Error processing image(s): {str(e)}")

class SCTRequest(BaseModel):
    parts: List[Part]

@app.post("/api/generate-sct")
async def create_sct_file(request: SCTRequest):
    """Takes JSON parts and returns a downloadable .sct file"""
    try:
        sct_content = generate_sct(request.parts)
        
        timestamp = int(time.time())
        filename = f"cortes_{timestamp}.sct"
        
        return Response(
            content=sct_content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating file: {str(e)}")

# To run the server: uvicorn main:app --reload
