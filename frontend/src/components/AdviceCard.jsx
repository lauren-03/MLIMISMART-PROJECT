// One piece of advice, with "Listen", "Share" and a helpful / not helpful
// rating. Ratings are sent to the advice model, which retrains on them.
import { useEffect, useState } from 'react'

import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import { seasonLabel, topicLabel } from '../i18n/translations'

const URGENCY_STYLE = {
  urgent: { css: 'advice-urgent', badge: 'bg-danger', key: 'urgent', icon: 'exclamation-octagon-fill' },
  caution: { css: 'advice-caution', badge: 'bg-warning text-dark', key: 'caution', icon: 'exclamation-triangle-fill' },
  normal: { css: 'advice-normal', badge: 'bg-success', key: 'normal', icon: 'check-circle-fill' },
}

const canSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window

export default function AdviceCard({ advice, showReasoning = true }) {
  const { farmer, language, t } = useApp()
  const [open, setOpen] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [rating, setRating] = useState(null)
  const [ratingError, setRatingError] = useState(false)

  useEffect(() => {
    setRating(null)
    setRatingError(false)
  }, [advice?.request_id])

  // Stop reading if the card disappears or the advice changes.
  useEffect(() => () => canSpeak && window.speechSynthesis.cancel(), [advice])

  if (!advice) return null

  const style = URGENCY_STYLE[advice.urgency] ?? URGENCY_STYLE.normal
  const fromGemini = advice.source === 'gemini' || advice.source === 'llm'
  const openAnswer = advice.rules_fired?.some((rule) => rule.includes('Gemini answered'))

  const speak = () => {
    if (!canSpeak) return
    if (speaking) {
      window.speechSynthesis.cancel()
      setSpeaking(false)
      return
    }
    const utterance = new SpeechSynthesisUtterance(advice.advice)
    utterance.lang = language === 'NY' ? 'ny-MW' : 'en-GB'
    utterance.rate = 0.92
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utterance)
    setSpeaking(true)
  }

  const canRate = farmer && advice.request_id && advice.action

  const rate = async (helpful) => {
    setRatingError(false)
    try {
      await api.post(`/advice/${advice.request_id}/rate`, { helpful })
      setRating(helpful)
    } catch {
      setRatingError(true)
    }
  }

  const shareText = `MlimiSmart (${advice.location}): ${advice.advice}`
  const shareUrl = `https://wa.me/?text=${encodeURIComponent(shareText)}`

  return (
    <div className={`card card-mlimi ${style.css} mb-3`}>
      <div className="card-body">
        <div className="d-flex justify-content-between align-items-start flex-wrap gap-2 mb-2">
          <div className="d-flex flex-wrap gap-2">
            <span className="badge bg-light text-tea border">
              {topicLabel(advice.topic, language)}
            </span>
            <span className={`badge ${style.badge}`}>
              {t(style.key)}
            </span>
            {fromGemini && (
              <span className="badge badge-ai">
                {openAnswer ? t('aiAnswered') : t('aiWorded')}
              </span>
            )}
          </div>
          <div className="small text-muted text-end">
            {advice.location}
            {advice.season ? ` · ${seasonLabel(advice.season, language)}` : ''}
          </div>
        </div>

        <p className="advice-text mb-2">{advice.advice}</p>

        {advice.weather_summary && (
          <p className="small text-muted mb-2">
            {advice.weather_summary}
          </p>
        )}

        <div className="d-flex flex-wrap gap-2 align-items-center">
          {canSpeak && (
            <button type="button" className="btn btn-sm btn-outline-tea" onClick={speak}
                    aria-pressed={speaking}>
              {speaking ? t('stopListening') : t('listen')}
            </button>
          )}
          <a className="btn btn-sm btn-outline-tea" href={shareUrl} target="_blank" rel="noreferrer">
            {t('shareWhatsapp')}
          </a>
          {showReasoning && advice.rules_fired?.length > 0 && (
            <button
              type="button"
              className="btn btn-sm btn-link text-tea text-decoration-none"
              onClick={() => setOpen((value) => !value)}
              aria-expanded={open}
            >
              {t('whyThisAdvice')}
            </button>
          )}
        </div>

        {canRate && (
          <div className="rating-row mt-3 pt-2 border-top small">
            {rating === null ? (
              <>
                <span className="me-2">{t('wasHelpful')}</span>
                <button type="button" className="btn btn-sm btn-outline-tea me-2" onClick={() => rate(true)}>
                  {t('yes')}
                </button>
                <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => rate(false)}>
                  {t('no')}
                </button>
                {ratingError && <span className="text-danger ms-2">{t('ratingFailed')}</span>}
              </>
            ) : (
              <span className="text-muted">{t('thanksRating')}</span>
            )}
          </div>
        )}

        {open && (
          <div className="reasoning-box mt-2">
            {advice.rules_fired.map((rule, index) => (
              <div key={index}>{`• ${rule}`}</div>
            ))}
            <div className="mt-2 text-muted">
              {`topic: ${advice.topic} · confidence: ${advice.confidence} · `}
              {`classified by: ${advice.classification_method} · wording: ${advice.source}`}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
