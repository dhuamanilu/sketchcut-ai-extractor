import os
import json
from tempfile import NamedTemporaryFile
from typing import List
from fastapi import UploadFile
import pandas as pd
import google.generativeai as genai

from app.models.schemas import Part
from app.core.config import settings

prompt = """
You are an expert at interpreting handwritten or printed notes, as well as unstructured spreadsheet data arrays, for melamine wood cutting.
Analyze the provided images AND/OR the provided raw spreadsheet text string and extract the combined list of pieces to be cut.
Rules:
1. Each piece must have a 'length', 'width', and 'quantity'. YOU MUST EXTRACT LENGTH AND WIDTH IN THE EXACT ORDER THEY ARE WRITTEN (e.g., if note says 200x500, length=200, width=500. DO NOT reorder them by size!).
2. EXTREMELY CRITICAL CONVERSION RULE: Sketch Cut Pro REQUIRES ALL measurements in pure MILLIMETERS (mm), but notes are very often in Centimeters (cm).
   - Step A: Analyze the numbers. If you see decimals like 15.4, or numbers that are too small to be millimeters for furniture (like 20, 45, 80, 150), they are CENTIMETERS.
   - Step B: If the numbers are in CENTIMETERS, you MUST multiply EVERY length and width by 10 to convert them to MILLIMETERS (e.g., 15.4 cm -> 154 mm).
   - Step C: Ensure your final output values are strictly INTEGERS representing MILLIMETERS.
3. EDGE BANDING (Cantos) AND GROOVES (Surcos):
   - "Largo" (Long/L) ALWAYS refers to the physically LARGER dimension of the piece. "Corto" (Short/C) ALWAYS refers to the physically SMALLER dimension.
   - Standard edge abbreviations:
     - '1L' = 1 delgado en largo, '1L grueso' or '1L cg' = 1 grueso en largo.
     - '4LG' = 4 lados grueso -> banding_long="2_grueso", banding_short="2_grueso".
     - '4LD' = 4 lados delgado -> banding_long="2_delgado", banding_short="2_delgado".
     - 'RANURA' or 'CANAL' = 1 surco en el largo -> groove_long="1".
   - Extract edge banding into: `banding_long`, `banding_short`. Valid values: "none", "1_grueso", "2_grueso", "1_delgado", "2_delgado", "mixto". 
     - Use "mixto" ONLY if a single axis has BOTH 1 thick and 1 thin edge (e.g. "1 largo grueso y 1 largo delgado").
     - CRITICAL: If no edges are mentioned, YOU MUST DEFAULT TO "none". Do NOT hallucinate edge banding.
   - Extract grooves into: `groove_long`, `groove_short`. Valid values: "none", "1", "2". (If note says '1 surco en el largo', then groove_long="1").
     - CRITICAL: If no grooves are mentioned, YOU MUST DEFAULT TO "none".
4. AGGREGATION & ORDERING: Aggregate ALL pieces found across ALL provided images into a single flat list sequentially.
5. Return strictly a flat JSON array, where each element is an object with: length, width, quantity, banding_long, banding_short, groove_long, groove_short. Do not return markdown.
"""

async def extract_parts_from_images(files: List[UploadFile]) -> List[Part]:
    temp_paths = []
    uploaded_files = []
    spreadsheet_texts = []
    
    try:
        # Save temp files and upload to Gemini
        for file in files:
            extension = os.path.splitext(file.filename)[1].lower() if file.filename else ""
            
            # Read into memory
            content = await file.read()
            
            if extension in ['.xlsx', '.xls', '.csv']:
                # Handle Spreadsheets
                with NamedTemporaryFile(delete=False, suffix=extension) as temp:
                    temp.write(content)
                    temp_paths.append(temp.name)
                
                # Parse with Pandas
                if extension == '.csv':
                    df = pd.read_csv(temp_paths[-1])
                else:
                    df = pd.read_excel(temp_paths[-1])
                
                # Convert unstructured dataframe to pure text representation
                spreadsheet_texts.append(f"SPREADSHEET CONTENT DUMP ({file.filename}):\n{df.to_string()}\n---")
            
            else:
                # Handle Images
                suffix = extension if extension else ".jpg"
                with NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                    temp.write(content)
                    temp_paths.append(temp.name)
                
                myfile = genai.upload_file(temp_paths[-1])
                uploaded_files.append(myfile)
            
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Build payload combining images, spreadsheet strings, and prompt
        payload = uploaded_files + spreadsheet_texts + [prompt]
        
        response = model.generate_content(
            payload,
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
            
            # Extract cantos and surcos safely falling back to 'none' if AI failed to emit
            b_long = str(item.get('banding_long', 'none'))
            b_short = str(item.get('banding_short', 'none'))
            g_long = str(item.get('groove_long', 'none'))
            g_short = str(item.get('groove_short', 'none'))

            parts.append(Part(
                length=l,
                width=w,
                quantity=int(item.get('quantity', 1)),
                banding_long=b_long,
                banding_short=b_short,
                groove_long=g_long,
                groove_short=g_short
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
