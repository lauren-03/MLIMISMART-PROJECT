// The ask-for-advice input, with sample questions from the research questionnaire so a farmer who is unsure what to type has a starting point.
import { useState } from 'react'

import { useApp } from '../context/AppContext'
import { SAMPLE_QUESTIONS } from '../i18n/translations'

export default function QuestionBox({ onAsk, busy }) {
  const { language, t } = useApp()
  const [question, setQuestion] = useState('')

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
              placeholder={t('questionHint')}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              maxLength={500}
              disabled={busy}
            />
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
