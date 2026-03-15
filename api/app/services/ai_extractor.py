import os
import json
from tempfile import NamedTemporaryFile
from typing import List
from fastapi import UploadFile
import google.generativeai as genai

from app.models.schemas import Part
from app.core.config import settings

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

async def extract_parts_from_images(files: List[UploadFile]) -> List[Part]:
    temp_paths = []
    uploaded_files = []
    
    try:
        # Save temp files and upload to Gemini
        for file in files:
            with NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
                content = await file.read()
                temp.write(content)
                temp_paths.append(temp.name)
            
            myfile = genai.upload_file(temp_paths[-1])
            uploaded_files.append(myfile)
            
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            uploaded_files + [prompt],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        
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
        return parts

    except Exception as e:
        error_msg = str(e)
        if "Quota exceeded" in error_msg or "429" in error_msg:
            raise Exception("Límite de API gratuito excedido. Por favor, intenta de nuevo en un minuto o añade facturación a tu cuenta de Google AI Studio.")
        print(f"Failed to parse LLM response: {error_msg}")
        raise Exception(f"Error parseando resultados de la IA: {error_msg}")

    finally:
        # Guarantee cleanup of all temp local files
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                os.remove(temp_path)
