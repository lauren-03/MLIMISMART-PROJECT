// Administrator dashboard (Module 6).
import { useEffect, useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts'

import { api, errorMessage } from '../api/client'
import { ErrorBox, Footer, PageHeader, Spinner, StatTile } from '../components/Shared'
import { useApp } from '../context/AppContext'
import { topicLabel } from '../i18n/translations'
import AdminTables from './AdminTables'
import BroadcastPanel from './BroadcastPanel'
import DatabasePanel from './DatabasePanel'
import ModelsPanel from './ModelsPanel'
import SystemPanel from './SystemPanel'

const PIE_COLOURS = ['#1b7a3a', '#a4522d', '#b26a00', '#2e9c4f', '#b5e07a']
const TABS = ['stats', 'models', 'database', 'alerts', 'farmers', 'requests', 'knowledge', 'sms', 'ussd']

export default function Admin() {
  const { language, t } = useApp()
  const [tab, setTab] = useState('stats')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.get('/admin/stats'),
      api.get('/admin/system'),
      api.get('/admin/farmers'),
      api.get('/admin/requests'),
      api.get('/admin/knowledge'),
      api.get('/admin/sms-logs'),
      api.get('/admin/ussd-sessions'),
    ])
      .then(([stats, system, farmers, requests, knowledge, smsLogs, ussdSessions]) =>
        setData({
          stats: stats.data,
          system: system.data,
          farmers: farmers.data,
          requests: requests.data,
          knowledge: knowledge.data,
          smsLogs: smsLogs.data,
          ussdSessions: ussdSessions.data,
        }),
      )
      .catch((err) => setError(errorMessage(err, t('errorGeneric')) ?? 'network'))
      .finally(() => setLoading(false))
  }, [t])

  if (loading) return <Spinner />

  const stats = data?.stats

  const topicData = (stats?.most_asked_topics ?? []).map((item) => ({
    name: topicLabel(item.topic, language),
    count: item.count,
  }))

  const channelData = [
    { name: 'Web', value: stats?.web_requests ?? 0 },
    { name: 'SMS', value: stats?.sms_requests ?? 0 },
    { name: 'USSD', value: stats?.ussd_requests ?? 0 },
  ].filter((item) => item.value > 0)

  const tabLabel = {
    stats: t('systemStatus'),
    alerts: t('alertsTitle'),
    models: 'AI models',
    database: t('dbTitle'),
    farmers: t('registeredFarmers'),
    requests: t('allRequests'),
    knowledge: t('knowledgeBase'),
    sms: t('smsLog'),
    ussd: t('ussdLog'),
  }

  return (
    <>
      <div className="container py-4">
        <PageHeader title={t('adminTitle')} />
        <ErrorBox error={error} />

        <div className="row g-3 mb-3">
          <div className="col-6 col-lg">
            <StatTile icon="people" figure={stats?.farmers ?? 0} caption={t('statFarmers')} />
          </div>
          <div className="col-6 col-lg">
            <StatTile icon="chat-square-text" figure={stats?.advice_requests ?? 0} caption={t('statRequests')} />
          </div>
          <div className="col-4 col-lg">
            <StatTile icon="globe2" figure={stats?.web_requests ?? 0} caption={t('statWeb')} />
          </div>
          <div className="col-4 col-lg">
            <StatTile icon="chat-dots" figure={stats?.sms_requests ?? 0} caption={t('statSms')} />
          </div>
          <div className="col-4 col-lg">
            <StatTile icon="telephone" figure={stats?.ussd_requests ?? 0} caption={t('statUssd')} />
          </div>
        </div>
        <div className="row g-3 mb-4">
          {(stats?.farmers_by_district ?? []).map((row) => (
            <div className="col-6 col-lg" key={row.district}>
              <StatTile icon="geo-alt" figure={row.count} caption={`${row.district} · ${t('statFarmers')}`} />
            </div>
          ))}
          <div className="col-6 col-lg">
            <StatTile icon="basket" figure={(stats?.harvest_kg ?? 0).toLocaleString()} caption={t('statHarvestKg')} />
          </div>
          <div className="col-6 col-lg">
            <StatTile icon="bell" figure={stats?.alert_subscribers ?? 0} caption={t('statSubscribers')} />
          </div>
        </div>

        <ul className="nav mb-3 flex-wrap gap-2">
          {TABS.map((name) => (
            <li className="nav-item" key={name}>
              <button
                type="button"
                className={`btn btn-sm ${tab === name ? 'btn-tea' : 'btn-outline-tea'}`}
                aria-pressed={tab === name}
                onClick={() => setTab(name)}
              >
                {tabLabel[name]}
              </button>
            </li>
          ))}
        </ul>

        {tab === 'stats' && (
          <div className="row g-4">
            <div className="col-lg-7">
              <div className="card card-mlimi h-100">
                <div className="card-body">
                  <h2 className="h6 text-tea">{t('mostAsked')}</h2>
                  {topicData.length === 0 ? (
                    <p className="text-muted small mb-0">No requests recorded yet.</p>
                  ) : (
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={topicData}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="name" fontSize={11} />
                        <YAxis allowDecimals={false} fontSize={11} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#2e9c4f" radius={[6, 6, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            </div>

            <div className="col-lg-5">
              <div className="card card-mlimi h-100">
                <div className="card-body">
                  <h2 className="h6 text-tea">{t('channel')}</h2>
                  {channelData.length === 0 ? (
                    <p className="text-muted small mb-0">No requests recorded yet.</p>
                  ) : (
                    <ResponsiveContainer width="100%" height={220}>
                      <PieChart>
                        <Pie data={channelData} dataKey="value" nameKey="name" label>
                          {channelData.map((entry, index) => (
                            <Cell key={entry.name} fill={PIE_COLOURS[index % PIE_COLOURS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            </div>

            <div className="col-12">
              <SystemPanel system={data?.system} />
            </div>
          </div>
        )}

        {tab === 'alerts' && <BroadcastPanel />}

        {tab === 'database' && <DatabasePanel />}
        {tab === 'models' && <ModelsPanel />}

        {tab !== 'stats' && tab !== 'alerts' && tab !== 'database' && <AdminTables tab={tab} data={data} />}
      </div>
      <Footer />
    </>
  )
}
