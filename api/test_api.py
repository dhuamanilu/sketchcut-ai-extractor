import requests
import sys

image_path = r"c:\Users\Usuario\OneDrive\Escritorio\EXTRACTOR DE MEDIDAS\PRUEBA1.jpeg"

try:
    with open(image_path, "rb") as image_file:
        files = {"file": ("PRUEBA1.jpeg", image_file, "image/jpeg")}
        response = requests.post("http://127.0.0.1:8000/api/extract", files=files)
        
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(response.text)
except Exception as e:
    print(f"Error connecting to server or reading file: {e}")
