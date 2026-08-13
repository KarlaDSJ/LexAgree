import { useEffect, useRef, useState } from 'react'
import { uploadDocument, getStatus, ApiError, AVAILABLE_MODELS } from '../api'
import PipelineSteps from '../components/PipelineSteps.jsx'
import './UploadPage.css'

const POLL_INTERVAL_MS = 1500

export default function UploadPage({ onDone }) {
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [selectedModels, setSelectedModels] = useState(new Set(AVAILABLE_MODELS.map((m) => m.id)))
  const [phase, setPhase] = useState('idle') // idle | uploading | processing | error | processing-error
  const [status, setStatus] = useState('queued')
  const [errorMessage, setErrorMessage] = useState('')
  const pollRef = useRef(null)

  useEffect(() => () => clearInterval(pollRef.current), [])

  function pickFile(f) {
    if (!f) return
    if (!f.name.toLowerCase().endsWith('.txt')) {
      setErrorMessage('Only .txt files are accepted for now.')
      return
    }
    setErrorMessage('')
    setFile(f)
  }

  function toggleModel(modelId) {
    setSelectedModels((prev) => {
      const next = new Set(prev)
      if (next.has(modelId)) next.delete(modelId)
      else next.add(modelId)
      return next
    })
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    pickFile(e.dataTransfer.files?.[0])
  }

  async function handleSubmit() {
    if (!file || selectedModels.size === 0) return
    setPhase('uploading')
    setErrorMessage('')
    try {
      const { job_id } = await uploadDocument(file, Array.from(selectedModels))
      setPhase('processing')
      setStatus('segmenting')
      pollRef.current = setInterval(() => pollStatus(job_id), POLL_INTERVAL_MS)
      pollStatus(job_id)
    } catch (err) {
      handleError(err, 'idle')
    }
  }

  async function pollStatus(jobId) {
    try {
      const res = await getStatus(jobId)
      setStatus(res.status)
      if (res.status === 'done') {
        clearInterval(pollRef.current)
        onDone(jobId)
      } else if (res.status === 'error') {
        clearInterval(pollRef.current)
        setPhase('processing-error')
        setErrorMessage(res.error || 'Processing failed on the server.')
      }
    } catch (err) {
      clearInterval(pollRef.current)
      handleError(err, 'processing-error')
    }
  }

  // fallbackPhase: 'idle' -> the error happened before the pipeline
  // started, shown over the upload zone. 'processing-error' -> it
  // happened during the pipeline, shown over the progress card.
  function handleError(err, fallbackPhase) {
    setPhase(fallbackPhase === 'idle' ? 'error' : 'processing-error')
    setErrorMessage(
      err instanceof ApiError
        ? err.message
        : 'Could not connect to the server. Check that the API is running.'
    )
  }

  function reset() {
    setFile(null)
    setPhase('idle')
    setStatus('queued')
    setErrorMessage('')
  }

  const canSubmit = !!file && selectedModels.size > 0

  return (
    <div className="upload-page">
      <header className="upload-page__header">
        <p className="eyebrow mono">01 · Upload document</p>
        <h1>Argument Analyzer</h1>
        <p className="upload-page__subtitle">
          Upload a text document. Several language models will read each
          segment looking for arguments, and we'll cross-check their
          answers against the original text.
        </p>
      </header>

      {phase === 'idle' || phase === 'error' ? (
        <>
          <div
            className={`dropzone ${dragOver ? 'dropzone--over' : ''} ${file ? 'dropzone--filled' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input').click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && document.getElementById('file-input').click()}
          >
            <input
              id="file-input"
              type="file"
              accept=".txt,text/plain"
              hidden
              onChange={(e) => pickFile(e.target.files?.[0])}
            />
            {file ? (
              <>
                <p className="dropzone__filename mono">{file.name}</p>
                <p className="dropzone__hint">{(file.size / 1024).toFixed(1)} KB — click to change the file</p>
              </>
            ) : (
              <>
                <p className="dropzone__title">Drag your .txt file here</p>
                <p className="dropzone__hint">or click to select it</p>
              </>
            )}
          </div>

          <div className="model-picker">
            <p className="model-picker__label mono">Models to consult</p>
            <div className="model-picker__options">
              {AVAILABLE_MODELS.map((model) => (
                <label key={model.id} className="model-option">
                  <input
                    type="checkbox"
                    checked={selectedModels.has(model.id)}
                    onChange={() => toggleModel(model.id)}
                  />
                  <span>{model.label}</span>
                </label>
              ))}
            </div>
            {selectedModels.size === 0 && (
              <p className="upload-page__error">Select at least one model.</p>
            )}
          </div>

          {errorMessage && (
            <p className="upload-page__error" role="alert">{errorMessage}</p>
          )}

          <button
            className="btn btn--primary"
            disabled={!canSubmit}
            onClick={handleSubmit}
          >
            Analyze document
          </button>
        </>
      ) : (
        <div className="processing-card">
          <p className="eyebrow mono">Processing “{file?.name}”</p>
          <PipelineSteps currentStatus={status} errorMessage={phase === 'processing-error' ? errorMessage : ''} />
          {phase === 'processing-error' && (
            <button className="btn btn--secondary" onClick={reset}>Try again</button>
          )}
        </div>
      )}
    </div>
  )
}