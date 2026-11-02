// The table views of the admin dashboard, split out of Admin.jsx to keep each file readable
import { useApp } from '../context/AppContext'
import { topicLabel } from '../i18n/translations'

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : ''
}

export default function AdminTables({ tab, data }) {
  const { language, t } = useApp()

  if (tab === 'farmers') {
    return (
      <div className="table-responsive card card-mlimi">
        <table className="table table-hover mb-0 align-middle">
          <thead className="table-light">
            <tr>
              <th>#</th>
              <th>{t('fullName')}</th>
              <th>{t('phone')}</th>
              <th>{t('location')}</th>
              <th>{t('preferredLanguage')}</th>
              <th>{t('farmSize')}</th>
              <th>Role</th>
            </tr>
          </thead>
          <tbody>
            {data.farmers.map((farmer) => (
              <tr key={farmer.farmer_id}>
                <td>{farmer.farmer_id}</td>
                <td>{farmer.name}</td>
                <td>{farmer.phone}</td>
                <td>{farmer.location}</td>
                <td>{farmer.language}</td>
                <td>{farmer.farm_size_ha ?? '-'}</td>
                <td>
                  <span className={`badge ${farmer.role === 'ADMIN' ? 'bg-dark' : 'bg-success'}`}>
                    {farmer.role}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  if (tab === 'requests') {
    return (
      <div className="table-responsive card card-mlimi">
        <table className="table table-hover mb-0 align-middle">
          <thead className="table-light">
            <tr>
              <th>#</th>
              <th>{t('questionLabel')}</th>
              <th>{t('topic')}</th>
              <th>{t('channel')}</th>
              <th>{t('location')}</th>
              <th>{t('askedOn')}</th>
            </tr>
          </thead>
          <tbody>
            {data.requests.map((item) => (
              <tr key={item.request_id}>
                <td>{item.request_id}</td>
                <td style={{ maxWidth: '320px' }}>{item.question}</td>
                <td>{topicLabel(item.topic, language)}</td>
                <td>
                  <span className="badge bg-secondary">{item.channel}</span>
                </td>
                <td>{item.location}</td>
                <td className="small text-muted">{formatDate(item.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  if (tab === 'knowledge') {
    return (
      <div className="row g-3">
        {data.knowledge.map((item) => (
          <div className="col-md-6" key={item.id}>
            <div className="card card-mlimi h-100">
              <div className="card-body">
                <span className="badge bg-light text-tea border mb-2">{item.topic}</span>
                <h3 className="h6 fw-semibold">{item.title_en}</h3>
                <p className="small text-muted">{item.body_en}</p>
                <h3 className="h6 fw-semibold text-tea">{item.title_ny}</h3>
                <p className="small text-muted mb-0">{item.body_ny}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (tab === 'ussd') {
    return (
      <div className="table-responsive card card-mlimi">
        <table className="table table-hover mb-0 align-middle">
          <thead className="table-light">
            <tr>
              <th>#</th>
              <th>{t('phone')}</th>
              <th>{t('ussdServiceCode')}</th>
              <th>{t('preferredLanguage')}</th>
              <th>{t('ussdInputTrail')}</th>
              <th>{t('topic')}</th>
              <th>Screens</th>
              <th>Gateway</th>
              <th>{t('askedOn')}</th>
            </tr>
          </thead>
          <tbody>
            {data.ussdSessions.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>{row.phone}</td>
                <td className="small">
                  <code>{row.service_code}</code>
                </td>
                <td>{row.language}</td>
                <td className="small">
                  <code>{row.last_input || '-'}</code>
                </td>
                <td>{row.topic ? topicLabel(row.topic, language) : '-'}</td>
                <td>{row.screens_served}</td>
                <td className="small">{row.gateway}</td>
                <td className="small text-muted">{formatDate(row.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  if (tab === 'sms') {
    return (
      <div className="table-responsive card card-mlimi">
        <table className="table table-hover mb-0 align-middle">
          <thead className="table-light">
            <tr>
              <th>#</th>
              <th>{t('phone')}</th>
              <th>Direction</th>
              <th>Message</th>
              <th>Gateway</th>
              <th>{t('askedOn')}</th>
            </tr>
          </thead>
          <tbody>
            {data.smsLogs.map((log) => (
              <tr key={log.id}>
                <td>{log.id}</td>
                <td>{log.phone}</td>
                <td>
                  <span className={`badge ${log.direction === 'IN' ? 'bg-primary' : 'bg-success'}`}>
                    {log.direction}
                  </span>
                </td>
                <td style={{ maxWidth: '340px' }} className="small">
                  {log.message}
                </td>
                <td className="small">{log.gateway}</td>
                <td className="small text-muted">{formatDate(log.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  return null
}
