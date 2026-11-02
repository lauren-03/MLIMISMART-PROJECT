// Admin: the two trained models, their test results, training history and
// farmer ratings, with buttons to retrain or run the daily update now.
import { useCallback, useEffect, useState } from 'react'

import { api, errorMessage } from '../api/client'
import { ErrorBox, Spinner } from '../components/Shared'
import { useApp } from '../context/AppContext'

const pct = (v) => (v === null || v === undefined ? '--' : `${(v * 100).toFixed(1)}%`)
const when = (v) => (v ? new Date(v).toLocaleString('en-GB') : '--')

function RunTable({ runs, columns }) {
  if (!runs?.length) return <p className="text-muted small">Not trained yet.</p>
  return (
    <div className="table-responsive">
      <table className="table table-sm small align-middle">
        <thead>
          <tr>
            <th>Version</th>
            <th>Trained</th>
            <th>Training rows</th>
            {columns.map(([label]) => <th key={label}>{label}</th>)}
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.version}>
              <td>v{run.version}</td>
              <td>{when(run.trained_at)}</td>
              <td>{run.train_rows.toLocaleString()}</td>
              {columns.map(([label, show]) => <td key={label}>{show(run.metrics)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function ModelsPanel() {
  const { t } = useApp()
  const [data, setData] = useState(null)
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    api.get('/admin/models')
      .then(({ data: body }) => setData(body))
      .catch((err) => setError(errorMessage(err, t('errorGeneric')) ?? 'network'))
  }, [t])

  useEffect(load, [load])

  const run = async (key, url) => {
    setBusy(key)
    setError(null)
    try {
      await api.post(url, null, { timeout: 30 * 60 * 1000 })
      load()
    } catch (err) {
      setError(errorMessage(err, t('errorGeneric')) ?? 'network')
    } finally {
      setBusy(null)
    }
  }

  if (!data) return error ? <ErrorBox error={error} /> : <Spinner />

  const { rain, advice } = data
  const latestRain = rain.runs[0]?.metrics
  const latestAdvice = advice.runs[0]?.metrics

  return (
    <div>
      <ErrorBox error={error} />
      <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
        <p className="text-muted small mb-0">
          Weather history: {rain.history_days.toLocaleString()} days ({rain.history_from} to {rain.history_to}).
          Updated and retrained every day.
        </p>
        <button type="button" className="btn btn-sm btn-tea" disabled={busy !== null}
                onClick={() => run('update', '/admin/models/update')}>
          {busy === 'update' ? 'Updating…' : 'Update now'}
        </button>
      </div>

      <div className="card card-mlimi mb-4">
        <div className="card-body">
          <div className="d-flex justify-content-between align-items-start flex-wrap gap-2">
            <div>
              <h2 className="h6 fw-semibold text-tea mb-1">Rain prediction model</h2>
              <p className="small text-muted mb-2">
                Gradient boosting classifier. Predicts whether tomorrow will have 1 mm of rain or more,
                from the last days' weather in each area. Tested on the most recent 365 days, which it
                does not see during training.
              </p>
            </div>
            <button type="button" className="btn btn-sm btn-outline-tea" disabled={busy !== null}
                    onClick={() => run('rain', '/admin/models/rain/retrain')}>
              {busy === 'rain' ? 'Training…' : 'Retrain'}
            </button>
          </div>
          {latestRain && (
            <div className="row g-2 mb-3 small">
              <div className="col-6 col-md-3"><strong>{pct(latestRain.accuracy)}</strong><br />test accuracy</div>
              <div className="col-6 col-md-3"><strong>{pct(latestRain.baseline_same_as_today)}</strong><br />"same as today" guess</div>
              <div className="col-6 col-md-3"><strong>{latestRain.roc_auc}</strong><br />ROC AUC</div>
              <div className="col-6 col-md-3">
                <strong>{rain.live.checked ? pct(rain.live.accuracy) : '--'}</strong><br />
                live accuracy ({rain.live.checked} checked)
              </div>
            </div>
          )}
          {latestRain?.sources && (
            <div className="small mb-3">
              <div className="fw-semibold mb-1">Data used ({latestRain.inputs} inputs per area per day)</div>
              <ul className="mb-2">
                {latestRain.sources.map((source) => <li key={source}>{source}</li>)}
              </ul>
              {latestRain.accuracy_weather_only !== undefined && (
                <p className="mb-2 text-muted">
                  Same model with daily weather only: {pct(latestRain.accuracy_weather_only)} accuracy,
                  AUC {latestRain.roc_auc_weather_only}. With all datasets: {pct(latestRain.accuracy)},
                  AUC {latestRain.roc_auc}.
                </p>
              )}
              {latestRain.top_inputs && (
                <>
                  <div className="fw-semibold mb-1">Inputs the model relies on most</div>
                  {latestRain.top_inputs.map(([name, value]) => (
                    <div key={name} className="d-flex align-items-center gap-2">
                      <span style={{ width: 150 }}>{name.replaceAll('_', ' ')}</span>
                      <div className="progress flex-grow-1" style={{ height: 8, maxWidth: 260 }}>
                        <div className="progress-bar bg-success"
                             style={{ width: `${Math.max(2, (value / latestRain.top_inputs[0][1]) * 100)}%` }} />
                      </div>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
          <RunTable runs={rain.runs} columns={[
            ['Accuracy', (m) => pct(m.accuracy)],
            ['Precision', (m) => pct(m.precision)],
            ['Recall', (m) => pct(m.recall)],
            ['AUC', (m) => m.roc_auc],
          ]} />
        </div>
      </div>

      <div className="card card-mlimi">
        <div className="card-body">
          <div className="d-flex justify-content-between align-items-start flex-wrap gap-2">
            <div>
              <h2 className="h6 fw-semibold text-tea mb-1">Advice decision model</h2>
              <p className="small text-muted mb-2">
                Scores every possible action for a topic in the current situation and picks the best one.
                Starts from past weather days labelled with tea guidance (using ERA5-Land soil moisture
                for dry-soil decisions and the CHIRPS rainfall anomaly), then learns from farmers'
                ratings. Retrains after every {advice.retrain_every} new ratings.
              </p>
            </div>
            <button type="button" className="btn btn-sm btn-outline-tea" disabled={busy !== null}
                    onClick={() => run('advice', '/admin/models/advice/retrain')}>
              {busy === 'advice' ? 'Training…' : 'Retrain'}
            </button>
          </div>
          <div className="row g-2 mb-3 small">
            <div className="col-6 col-md-3"><strong>{pct(latestAdvice?.decision_accuracy)}</strong><br />decision accuracy</div>
            <div className="col-6 col-md-3"><strong>{advice.decisions}</strong><br />decisions made</div>
            <div className="col-6 col-md-3">
              <strong>{advice.ratings}</strong><br />
              farmer ratings ({advice.ratings ? pct(advice.helpful / advice.ratings) : '--'} helpful)
            </div>
            <div className="col-6 col-md-3"><strong>{advice.since_training}</strong><br />new since last training</div>
          </div>
          <RunTable runs={advice.runs} columns={[
            ['Decision accuracy', (m) => pct(m.decision_accuracy)],
            ['Farmer ratings', (m) => m.farmer_ratings],
            ['Rated helpful', (m) => pct(m.rated_helpful)],
          ]} />
        </div>
      </div>
    </div>
  )
}
