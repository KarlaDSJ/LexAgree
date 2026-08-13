// Convierte un texto y una lista de "spans" (start, end, color, id) en
// segmentos contiguos, cada uno con la lista de spans activos en ese tramo.
// Esto permite resaltar correctamente aunque los spans se superpongan
// (por ejemplo, dos LLMs que detectan el mismo argumento con límites
// ligeramente distintos).
export function buildSegments(text, spans) {
  if (!spans || spans.length === 0) {
    return [{ text, start: 0, end: text.length, active: [] }]
  }

  const points = new Set([0, text.length])
  for (const s of spans) {
    points.add(clamp(s.start, 0, text.length))
    points.add(clamp(s.end, 0, text.length))
  }
  const sorted = Array.from(points).sort((a, b) => a - b)

  const segments = []
  for (let i = 0; i < sorted.length - 1; i++) {
    const start = sorted[i]
    const end = sorted[i + 1]
    if (start >= end) continue
    const active = spans.filter((s) => s.start <= start && s.end >= end)
    segments.push({ text: text.slice(start, end), start, end, active })
  }
  return segments
}

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n))
}

// Construye un estilo de fondo para un segmento con uno o más colores activos.
// Un solo color -> tono plano con alpha. Varios colores -> franjas iguales,
// así se ve de un vistazo cuántos modelos coinciden en ese tramo.
// (El elemento .hl usa mix-blend-mode: multiply en CSS, así que estos
// colores se comportan como tinta de resaltador real sobre el texto.)
export function backgroundFor(active, alphaFor) {
  if (active.length === 0) return {}
  if (active.length === 1) {
    const a = alphaFor ? alphaFor(active[0]) : 0.55
    return { backgroundColor: hexToRgba(active[0].color, a) }
  }
  const n = active.length
  const stops = active
    .map((s, i) => {
      const a = alphaFor ? alphaFor(s) : 0.6
      const c = hexToRgba(s.color, a)
      const from = (i / n) * 100
      const to = ((i + 1) / n) * 100
      return `${c} ${from}%, ${c} ${to}%`
    })
    .join(', ')
  return { backgroundImage: `linear-gradient(180deg, ${stops})` }
}

export function hexToRgba(hex, alpha) {
  const clean = hex.replace('#', '')
  const r = parseInt(clean.substring(0, 2), 16)
  const g = parseInt(clean.substring(2, 4), 16)
  const b = parseInt(clean.substring(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

// Color del resaltador en modo "Resultado final" (consenso). Amarillo
// resaltador real, a propósito — es el mismo lenguaje visual que los
// colores por LLM (los 3 primarios), pero reservado solo para esta vista.
export const CONSENSUS_COLOR = '#FFD400'

export const LLM_PALETTE = ['var(--llm-1)', 'var(--llm-2)', 'var(--llm-3)']

// Como los valores CSS var() no se pueden convertir a rgba directamente,
// mantenemos también la paleta en hex para usar en backgroundFor().
// Exactamente los 3 primarios (rojo/azul/amarillo) — si algún día hay más
// de 3 LLMs, la paleta cicla de vuelta sobre estos mismos.
export const LLM_PALETTE_HEX = ['#E8352B', '#0044FF', '#FFD400']

export function colorForLlm(index) {
  return LLM_PALETTE_HEX[index % LLM_PALETTE_HEX.length]
}