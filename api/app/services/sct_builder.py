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

    banding_map = {
        "none": 0, "1_grueso": 1, "2_grueso": 2, "1_delgado": 3, "2_delgado": 4, "mixto": 5
    }
    groove_map = {
        "none": 0, "1": 1, "2": 2
    }

    parts_strings = []
    for part in parts:
        val_blong = banding_map.get(part.banding_long.lower(), 0)
        val_bshort = banding_map.get(part.banding_short.lower(), 0)
        val_glong = groove_map.get(part.groove_long.lower(), 0)
        val_gshort = groove_map.get(part.groove_short.lower(), 0)

        # "Largo" always means the physically larger dimension.
        if part.length >= part.width:
            # Length axis is the long side
            len_c, wid_c = val_blong, val_bshort
            len_g, wid_g = val_glong, val_gshort
        else:
            # Width axis is the long side
            len_c, wid_c = val_bshort, val_blong
            len_g, wid_g = val_gshort, val_glong

        part_data = f"{part.length}X{part.width}X{part.quantity}\n{len_c}X{wid_c}_{len_g}X{wid_g}\n00"
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
