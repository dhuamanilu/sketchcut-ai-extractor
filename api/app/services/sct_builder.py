from datetime import datetime
from typing import List
from app.models.schemas import Part

def generate_sct(parts: List[Part]) -> str:
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    header = f"""<V4.0i>
1
2440X2140_0
3X3X5_True


LectorIA
{current_date}



3
grueso
0.45
delgado
1

<Parts>{len(parts)}"""

    parts_strings = []
    for part in parts:
        part_data = f"{part.length}X{part.width}X{part.quantity}\n0X0_0X0\n00"
        for _ in range(part.quantity):
            part_data += "\n000_0X-1X-1"
        parts_strings.append(part_data)
        
    parts_content = "\n".join(parts_strings)
    
    footer = """<USnips>0
<NSnips>0
8
15
4
"""

    return f"{header}\n{parts_content}\n{footer}"
