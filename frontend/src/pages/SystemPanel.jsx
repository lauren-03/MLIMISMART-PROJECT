// Shows what the running system is actually connected to.
import { useApp } from '../context/AppContext'

function Field({ label, value, note }) {
  return (
    <>
      <div className="text-muted text-uppercase" style={{ fontSize: '0.7rem' }}>
        {label}
      </div>
      <div className="fw-semibold">{value ?? '-'}</div>
      {note && <div className="text-muted">{note}</div>}
    </>
  )
}

export default function SystemPanel({ system }) {
  const { t } = useApp()
  const classifier = system?.classifier

  return (
    <div className="card card-mlimi">
      <div className="card-body">
        <h2 className="h6 text-tea mb-3">{t('systemStatus')}</h2>
        <div className="row g-3 small">
          <div className="col-md-3 col-lg-2">
            <Field label="Database" value={system?.database} note={system?.database_target} />
          </div>
          <div className="col-md-3">
            <Field label="Weather" value="Open-Meteo" note="no API key required" />
          </div>
          <div className="col-md-3">
            <Field
              label={`AI · ${system?.ai?.provider ?? 'Gemini'}`}
              value={system?.ai?.mode}
              note={
                system?.ai?.last_error
                  ? `${system.ai.model} · last call failed: ${system.ai.last_error}`
                  : system?.ai?.enabled
                    ? `${system.ai.model}${system.ai.last_call_ok ? ' · working' : ''}`
                    : 'add GEMINI_API_KEY to backend/.env'
              }
            />
          </div>
          <div className="col-md-3">
            <Field label="SMS" value={system?.sms?.mode} note={system?.sms?.gateway} />
          </div>
          <div className="col-md-3">
            <Field
              label="USSD"
              value={system?.ussd?.mode}
              note={system?.ussd?.service_code}
            />
          </div>
          <div className="col-12">
            <Field
              label="Topic classifier"
              value={classifier?.algorithm}
              note={
                classifier
                  ? `${classifier.training_examples} training examples · ` +
                    `${classifier.topics?.length} topics · ` +
                    `fit accuracy ${classifier.fit_accuracy}`
                  : null
              }
            />
          </div>
        </div>
      </div>
    </div>
  )
}
