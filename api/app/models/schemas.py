from typing import List
from pydantic import BaseModel

class Part(BaseModel):
    length: int
    width: int
    quantity: int
    label: str = ""
    banding_long: str = "none"
    banding_short: str = "none"
    groove_long: str = "none"
    groove_short: str = "none"

class SCTRequest(BaseModel):
    parts: List[Part]
