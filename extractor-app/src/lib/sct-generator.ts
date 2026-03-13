export interface Part {
  length: number;
  width: number;
  quantity: number;
  label?: string;
}

export function generateSCT(parts: Part[]): string {
  const currentDate = new Date().toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });

  const header = `<V4.0i>
1
2440X2140_0
3X3X5_True


LectorIA
${currentDate}



3
grueso
0.45
delgado
1

<Parts>${parts.length}`;

  const partsString = parts.map((part) => {
    let partData = `${part.length}X${part.width}X${part.quantity}\n0X0_0X0\n00`;
    // For each quantity, it needs a "000_0X-1X-1" line when uncalculated
    for (let i = 0; i < part.quantity; i++) {
        // However, in the provided example:
        // 300X500X2 has 2 lines of 000_0X-1X-1, but the "10" is before it instead of "00"
        // And 100X400X4 has "00" before the 4 lines.
        // The difference between "10" and "00" is related to edge banding or rotation allowance, 
        // For simplicity and safety we use "00" (no edge banding, can rotate)
        partData += `\n000_0X-1X-1`;
    }
    return partData;
  }).join('\n');

  const footer = `<USnips>0
<NSnips>0
8
15
4
`;

  return `${header}\n${partsString}\n${footer}`;
}
