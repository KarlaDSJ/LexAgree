import { STEP_ORDER, STEP_LABELS } from '../api'
import './PipelineSteps.css'

// currentStatus: una de las claves de STEP_ORDER ('queued' | 'segmenting' | ...)
export default function PipelineSteps({ currentStatus, errorMessage }) {
  const steps = STEP_ORDER.filter((s) => s !== 'queued')
  const currentIndex = STEP_ORDER.indexOf(currentStatus)

  return (
    <ol className="pipeline" aria-label="Analysis progress">
      {steps.map((key, i) => {
        const stepIndex = STEP_ORDER.indexOf(key)
        const state = errorMessage && stepIndex === currentIndex
          ? 'error'
          : stepIndex < currentIndex
          ? 'done'
          : stepIndex === currentIndex
          ? 'active'
          : 'pending'

        return (
          <li key={key} className={`pipeline__step pipeline__step--${state}`}>
            <span className="pipeline__marker mono">
              {state === 'done' ? '✓' : String(i + 1).padStart(2, '0')}
            </span>
            <span className="pipeline__label">{STEP_LABELS[key]}</span>
          </li>
        )
      })}
      {errorMessage && (
        <p className="pipeline__error" role="alert">{errorMessage}</p>
      )}
    </ol>
  )
}