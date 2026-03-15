from typing import List
from pydantic import BaseModel

class Part(BaseModel):
    length: int
    width: int
    quantity: int
    label: str = ""

class SCTRequest(BaseModel):
    parts: List[Part]
