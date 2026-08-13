import { useEffect, useMemo, useRef, useState } from 'react'
import { getResults, ApiError } from '../api'
import { buildSegments, backgroundFor, colorForLlm } from '../highlight.js'
import Fingerprint from '../components/Fingerprint.jsx'
import './ResultsPage.css'


/**
 * Resolve the real position of an argument part inside document_text.
 */
function resolvePartOffsets(documentText, part) {
  const text = part.text || ''

  if (!text) {
    return {
      start: part.start ?? 0,
      end: part.end ?? 0,
    }
  }

  /*
   * 1. First, trust the backend offsets if they are actually correct.
   */
  if (
    Number.isInteger(part.start) &&
    part.start >= 0 &&
    documentText.slice(part.start, part.start + text.length) === text
  ) {
    return {
      start: part.start,
      end: part.start + text.length,
    }
  }

  /*
   * 2. Search near the backend-provided position.
   *
   * This is preferable to searching the whole document because the same
   * sentence/text could theoretically occur more than once.
   */
  if (Number.isInteger(part.start)) {
    const windowSize = 1000

    const searchStart = Math.max(0, part.start - windowSize)
    const searchEnd = Math.min(
      documentText.length,
      part.start + windowSize + text.length
    )

    const window = documentText.slice(searchStart, searchEnd)
    const relativeStart = window.indexOf(text)

    if (relativeStart !== -1) {
      const start = searchStart + relativeStart

      return {
        start,
        end: start + text.length,
      }
    }
  }

  /*
   * 3. Last resort: search the complete document.
   */
  const start = documentText.indexOf(text)

  if (start !== -1) {
    return {
      start,
      end: start + text.length,
    }
  }

  /*
   * 4. If nothing worked, keep the backend offsets.
   * This should ideally never happen, but it prevents the UI from crashing.
   */
  return {
    start: part.start ?? 0,
    end: part.end ?? part.start ?? 0,
  }
}


export default function ResultsPage({ jobId, onBack }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState(null)
  const [mode, setMode] = useState('consensus') // 'consensus' | 'per-llm'
  const [selectedLlms, setSelectedLlms] = useState(new Set())
  const [activeArgId, setActiveArgId] = useState(null)

  const docRef = useRef(null)


  /*
   * Fetch results.
   */
  useEffect(() => {
    let cancelled = false

    setLoading(true)
    setError('')

    getResults(jobId)
      .then((res) => {
        if (cancelled) return

        setData(res)

        setSelectedLlms(
          new Set(Object.keys(res.llms || {}))
        )
      })
      .catch((err) => {
        if (cancelled) return

        setError(
          err instanceof ApiError
            ? err.message
            : 'Could not load the results. Check the connection to the server.'
        )
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [jobId])


  /*
   * "llms" comes as:
   *
   * {
   *   llama: "...",
   *   saul: "...",
   *   qwen: "..."
   * }
   *
   * Normalize it into an array of names.
   */
  const llmNames = useMemo(
    () => (data ? Object.keys(data.llms || {}) : []),
    [data]
  )


  /*
   * Assign one color to each LLM.
   */
  const llmColorMap = useMemo(() => {
    const map = {}

    llmNames.forEach((name, i) => {
      map[name] = colorForLlm(i)
    })

    return map
  }, [llmNames])


  /*
   * Number of models participating in the consensus.
   */
  const totalLlms = llmNames.length || 1


  const argumentsWithMeta = useMemo(() => {
    if (!data) return []

    const documentText = data.document_text || ''

    return (data.arguments || []).map((arg, i) => {
      const rawParts = arg.consensus_text || []

      const resolvedParts = rawParts.map((part, pi) => {
        const { start, end } = resolvePartOffsets(
          documentText,
          part
        )

        return {
          text: part.text || '',
          start,
          end,

          isClaim: pi === rawParts.length - 1,
        }
      })


      resolvedParts.sort((a, b) => {
        if (a.start !== b.start) {
          return a.start - b.start
        }

        return a.end - b.end
      })

      return {
        id: `arg_${i}`,

        parts: resolvedParts,

        agreementCount: arg.agreement_score ?? 0,

        agreementRatio:
          (arg.agreement_score ?? 0) / totalLlms,

        supportingLlms: Array.from(
          arg.supporting_llms || []
        ),
      }
    })
  }, [data, totalLlms])


  const spans = useMemo(() => {
    if (!data) return []

    if (mode === 'consensus') {
      return argumentsWithMeta.flatMap((arg) =>
        arg.parts.map((part, pi) => ({
          id: `${arg.id}__${pi}`,

          argId: arg.id,

          start: part.start,

          end: part.end,

          color: '#C99A2E',

          score: arg.agreementRatio,

          isClaim: part.isClaim,
        }))
      )
    }


    /*
     * Per-model mode:
     *
     * Same argument spans, but colored according to the LLMs
     * supporting the argument.
     */
    const out = []

    argumentsWithMeta.forEach((arg) => {
      const activeLlms = arg.supportingLlms.filter(
        (llm) => selectedLlms.has(llm)
      )

      arg.parts.forEach((part, pi) => {
        activeLlms.forEach((llmName) => {
          out.push({
            id: `${arg.id}__${pi}__${llmName}`,

            argId: arg.id,

            start: part.start,

            end: part.end,

            color: llmColorMap[llmName],

            isClaim: part.isClaim,
          })
        })
      })
    })

    return out
  }, [
    data,
    mode,
    argumentsWithMeta,
    selectedLlms,
    llmColorMap,
  ])


  /*
   * Build the actual document segments.
   */
  const segments = useMemo(() => {
    if (!data) return []

    return buildSegments(
      data.document_text,
      spans
    )
  }, [data, spans])


  /*
   * Toggle an LLM in "By model" mode.
   */
  function toggleLlm(name) {
    setSelectedLlms((prev) => {
      const next = new Set(prev)

      if (next.has(name)) {
        next.delete(name)
      } else {
        next.add(name)
      }

      return next
    })
  }


  /*
   * Scroll to the first visible span belonging to an argument.
   */
  function scrollToArg(argId) {
    setActiveArgId(argId)

    const el = docRef.current?.querySelector(
      `[data-arg-id="${argId}"]`
    )

    if (el) {
      el.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      })
    }
  }


  /*
   * Loading state.
   */
  if (loading) {
    return (
      <div className="results-shell results-shell--center">
        <p className="mono status-line">
          Loading results…
        </p>
      </div>
    )
  }


  /*
   * Error state.
   */
  if (error) {
    return (
      <div className="results-shell results-shell--center">
        <div className="error-card">
          <p className="eyebrow mono">
            Couldn't continue
          </p>

          <h2>
            Something failed while fetching the arguments
          </h2>

          <p className="error-card__msg">
            {error}
          </p>

          <button
            className="btn btn--secondary"
            onClick={onBack}
          >
            Try another document
          </button>
        </div>
      </div>
    )
  }


  const argCount = argumentsWithMeta.length


  return (
    <div className="results-shell">

      <header className="results-header">
        <div>
          <p className="eyebrow mono">
            02 · Results
          </p>

          <h1>
            Arguments found
          </h1>

          <p className="results-header__stats mono">
            {argCount}{' '}
            {argCount === 1
              ? 'argument'
              : 'arguments'}{' '}
            · {llmNames.length} models consulted
          </p>
        </div>

        <button
          className="btn btn--secondary"
          onClick={onBack}
        >
          Analyze another document
        </button>
      </header>


      <div className="toolbar">

        <div
          className="segmented"
          role="tablist"
          aria-label="Display mode"
        >

          <button
            role="tab"
            aria-selected={mode === 'consensus'}
            className={
              `segmented__option ${
                mode === 'consensus'
                  ? 'segmented__option--active'
                  : ''
              }`
            }
            onClick={() => setMode('consensus')}
          >
            Final result
          </button>


          <button
            role="tab"
            aria-selected={mode === 'per-llm'}
            className={
              `segmented__option ${
                mode === 'per-llm'
                  ? 'segmented__option--active'
                  : ''
              }`
            }
            onClick={() => setMode('per-llm')}
          >
            By model
          </button>

        </div>


        {mode === 'per-llm' && (
          <div className="llm-legend">

            {llmNames.map((name) => (
              <button
                key={name}
                className={
                  `llm-chip ${
                    selectedLlms.has(name)
                      ? ''
                      : 'llm-chip--off'
                  }`
                }
                onClick={() => toggleLlm(name)}
                style={{
                  '--chip-color': llmColorMap[name],
                }}
                title={data.llms[name]}
              >

                <span className="llm-chip__dot" />

                {name}

              </button>
            ))}

          </div>
        )}

      </div>


      {argCount === 0 ? (

        <div className="empty-state">

          <p className="eyebrow mono">
            No matches
          </p>

          <h2>
            No model found any arguments in this document
          </h2>

          <p>
            Check whether the document contains
            argumentative text, or try another file.
          </p>

        </div>

      ) : (

        <div className="results-grid">

          {/* =========================================================
              DOCUMENT
              ========================================================= */}

          <div
            className="doc-panel"
            ref={docRef}
          >

            {segments.map((seg, i) => {

              const style = backgroundFor(
                seg.active,

                mode === 'consensus'
                  ? (s) => 0.18 + s.score * 0.42
                  : () => 0.4
              )

              const isPlain =
                seg.active.length === 0

              const argIds = [
                ...new Set(
                  seg.active.map(
                    (s) => s.argId
                  )
                ),
              ]

              const isActive =
                argIds.includes(activeArgId)

              const isClaimSeg =
                seg.active.some(
                  (s) => s.isClaim
                )


              /*
               * Normal text.
               */
              if (isPlain) {
                return (
                  <span key={i}>
                    {seg.text}
                  </span>
                )
              }


              /*
               * Highlighted argument text.
               */
              return (
                <mark
                  key={i}

                  className={
                    `hl ${
                      isActive
                        ? 'hl--active'
                        : ''
                    } ${
                      isClaimSeg
                        ? 'hl--claim'
                        : ''
                    }`
                  }

                  style={style}

                  /*
                   * The first argument ID is enough for scrolling.
                   */
                  data-arg-id={argIds[0]}

                  title={
                    isClaimSeg
                      ? 'Argument conclusion (claim)'
                      : 'Argument premise'
                  }

                  onClick={() =>
                    scrollToArg(argIds[0])
                  }
                >
                  {seg.text}
                </mark>
              )
            })}

          </div>


          {/* =========================================================
              ARGUMENT LIST
              ========================================================= */}

          <aside
            className="arg-list"
            aria-label="List of arguments"
          >

            {argumentsWithMeta

              /*
               * In consensus mode show all arguments.
               *
               * In per-model mode only show arguments supported
               * by at least one selected LLM.
               */
              .filter(
                (arg) =>
                  mode === 'consensus' ||
                  arg.supportingLlms.some(
                    (l) => selectedLlms.has(l)
                  )
              )

              .map((arg) => {

                const detectedBy =
                  new Set(
                    arg.supportingLlms
                  )
                const partTexts = arg.parts
                  .map((part) =>
                    data.document_text
                      .slice(
                        part.start,
                        part.end
                      )
                      .trim()
                  )
                  .filter(Boolean)

                const premiseTexts = arg.parts
                  .filter(
                    (part) => !part.isClaim
                  )
                  .map((part) =>
                    data.document_text
                      .slice(
                        part.start,
                        part.end
                      )
                      .trim()
                  )
                  .filter(Boolean)


                const claimPart =
                  arg.parts.find(
                    (part) => part.isClaim
                  )


                const claimText =
                  claimPart
                    ? data.document_text
                        .slice(
                          claimPart.start,
                          claimPart.end
                        )
                        .trim()
                    : ''


                return (
                  <button
                    key={arg.id}

                    className={
                      `arg-item ${
                        activeArgId === arg.id
                          ? 'arg-item--active'
                          : ''
                      }`
                    }

                    onClick={() =>
                      scrollToArg(arg.id)
                    }
                  >

                    {/* ===============================
                        PREMISES
                        =============================== */}

                    {premiseTexts.length > 0 && (
                      <ul className="arg-item__premises">

                        {premiseTexts.map(
                          (text, pi) => (
                            <li key={pi}>
                              {text}
                            </li>
                          )
                        )}

                      </ul>
                    )}


                    {/* ===============================
                        CLAIM / CONCLUSION
                        =============================== */}

                    {claimText && (
                      <p className="arg-item__claim">

                        <span className="arg-item__claim-label mono">
                          Conclusion
                        </span>

                        {claimText}

                      </p>
                    )}


                    {/* ===============================
                        METADATA
                        =============================== */}

                    <div className="arg-item__meta">

                      <Fingerprint
                        llms={llmNames.map(
                          (name) => ({
                            name,
                            color:
                              llmColorMap[name],
                          })
                        )}

                        detectedBy={detectedBy}
                      />

                      <span className="arg-item__score mono">
                        {arg.agreementCount}/
                        {llmNames.length} models
                      </span>

                    </div>

                  </button>
                )
              })}

          </aside>

        </div>
      )}

    </div>
  )
}