// The ask-for-advice input, with sample questions from the research questionnaire so a farmer who is unsure what to type has a starting point.
import { useEffect, useRef, useState } from 'react'

import { useApp } from '../context/AppContext'
import { SAMPLE_QUESTIONS } from '../i18n/translations'

const Recognition =
  typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)

export default function QuestionBox({ onAsk, busy }) {
  const { language, t } = useApp()
  const [question, setQuestion] = useState('')
  const [listening, setListening] = useState(false)
  const recognizer = useRef(null)

  useEffect(() => () => recognizer.current?.abort(), [])

  const submit = (event) => {
    event.preventDefault()
    const trimmed = question.trim()
    if (trimmed.length < 2 || busy) return
    onAsk(trimmed)
  }

  const useSample = (sample) => {
    setQuestion(sample)
    if (!busy) onAsk(sample)
  }

  const listen = () => {
    if (!Recognition) return
    if (listening) {
      recognizer.current?.stop()
      return
    }
    const rec = new Recognition()
    // Chichewa recognition is not offered by browsers yet; English-Malawi
    // still captures most Chichewa words well enough to edit before asking.
    rec.lang = language === 'NY' ? 'ny-MW' : 'en-GB'
    rec.interimResults = true
    rec.maxAlternatives = 1
    rec.onresult = (event) => {
      const text = Array.from(event.results).map((r) => r[0].transcript).join(' ')
      setQuestion(text)
    }
    rec.onerror = () => setListening(false)
    rec.onend = () => setListening(false)
    recognizer.current = rec
    setListening(true)
    try {
      rec.start()
    } catch {
      // A second start while one is running throws; the first one continues.
      setListening(false)
    }
  }

  return (
    <div className="card card-mlimi mb-4">
      <div className="card-body">
        <form onSubmit={submit}>
          <label htmlFor="question" className="form-label">
            {t('questionLabel')}
          </label>
          <div className="input-group">
            <input
              id="question"
              type="text"
              className="form-control form-control-lg"
              placeholder={listening ? t('listeningNow') : t('questionHint')}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              maxLength={500}
              disabled={busy}
            />
            {Recognition && (
              <button
                type="button"
                className={`btn ${listening ? 'btn-danger' : 'btn-outline-tea'}`}
                onClick={listen}
                disabled={busy}
                aria-pressed={listening}
                title={t('speakQuestion')}
              >
                <i className={`bi bi-${listening ? 'mic-fill' : 'mic'}`} aria-hidden="true" />
                <span className="visually-hidden">{t('speakQuestion')}</span>
              </button>
            )}
            <button
              className="btn btn-tea px-4"
              type="submit"
              disabled={busy || question.trim().length < 2}
            >
              {busy ? t('asking') : t('askButton')}
            </button>
          </div>
        </form>

        <div className="mt-3">
          <div className="small text-muted mb-2">{t('quickQuestions')}</div>
          {SAMPLE_QUESTIONS[language].map((sample) => (
            <button
              type="button"
              className="chip"
              key={sample}
              onClick={() => useSample(sample)}
              disabled={busy}
            >
              {sample}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
