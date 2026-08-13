import './Fingerprint.css'

// llms: [{ name, color }]
// detectedBy: Set of LLM names that detected this argument
export default function Fingerprint({ llms, detectedBy }) {
  return (
    <span className="fingerprint" aria-hidden="true">
      {llms.map((llm) => {
        const filled = detectedBy.has(llm.name)
        return (
          <span
            key={llm.name}
            className="fingerprint__dot"
            title={`${llm.name}${filled ? ' — detected' : ' — not detected'}`}
            style={{
              backgroundColor: filled ? llm.color : 'transparent',
              borderColor: llm.color,
            }}
          />
        )
      })}
    </span>
  )
}