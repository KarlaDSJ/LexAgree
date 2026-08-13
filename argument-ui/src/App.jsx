import { useState } from 'react'
import UploadPage from './pages/UploadPage.jsx'
import ResultsPage from './pages/ResultsPage.jsx'

export default function App() {
  const [view, setView] = useState('upload') // 'upload' | 'results'
  const [jobId, setJobId] = useState(null)

  function handleDone(id) {
    setJobId(id)
    setView('results')
  }

  function handleBack() {
    setJobId(null)
    setView('upload')
  }

  return view === 'upload'
    ? <UploadPage onDone={handleDone} />
    : <ResultsPage jobId={jobId} onBack={handleBack} />
}
