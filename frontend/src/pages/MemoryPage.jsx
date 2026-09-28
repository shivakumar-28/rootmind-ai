import { useEffect, useState } from 'react'
import { Brain, Check, CircleHelp, Code2, History, Sparkles } from 'lucide-react'
import { getMemory } from '../services/api.js'

function MemorySection({ title, icon: Icon, items, emptyText }) {
  return (
    <section className="settings-card" style={{ padding: '20px' }}>
      <div className="settings-card-heading" style={{ padding: 0, paddingBottom: '14px', borderBottom: '1px solid #f1f5f9' }}>
        <div className="settings-heading-icon">
          <Icon size={18} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyBetween: 'space-between', width: '100%' }}>
          <strong style={{ fontSize: '14px' }}>{title}</strong>
          <span className="recent-count" style={{ marginLeft: 'auto', fontSize: '11px' }}>
            {items.length}
          </span>
        </div>
      </div>
      {items.length ? (
        <ul style={{ display: 'flex', flexDirection: 'column', gap: '10px', margin: '14px 0 0', padding: 0, listStyle: 'none' }}>
          {items.map((item) => (
            <li key={item} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', color: 'var(--ink-secondary)', fontSize: '12.5px' }}>
              <span style={{ width: '18px', height: '18px', borderRadius: '50%', background: '#ecfdf5', color: '#10b981', display: 'grid', placeItems: 'center', flex: 'none', marginTop: '2px' }}>
                <Check size={12} />
              </span>
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p style={{ margin: '14px 0 0', color: 'var(--ink-muted)', fontSize: '12px' }}>{emptyText}</p>
      )}
    </section>
  )
}

export default function MemoryPage() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getMemory()
      .then(setData)
      .catch((reason) => setError(reason.message))
  }, [])

  return (
    <section className="data-page memory-page">
      <div className="page-eyebrow">
        <Brain size={14} /> YOUR PERSONAL DEBUGGING CONTEXT
      </div>
      <div className="page-title-row">
        <div>
          <h1>Developer Memory</h1>
          <p>A living snapshot of the tools you use and fixes you've found useful.</p>
        </div>
        {data && (
          <div className="status-pill status-available">
            <History size={15} />
            <strong>{data.incidents_count}</strong> saved {data.incidents_count === 1 ? 'incident' : 'incidents'}
          </div>
        )}
      </div>

      {error ? (
        <div className="error-card">
          <CircleHelp size={18} />
          <span>{error}</span>
        </div>
      ) : !data ? (
        <div className="settings-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--ink-muted)' }}>
          Gathering your developer memory…
        </div>
      ) : (
        <>
          <div className="settings-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '20px' }}>
            <div className="settings-heading-icon">
              <Sparkles size={20} />
            </div>
            <p style={{ margin: 0, color: 'var(--ink-secondary)', fontSize: '13px', lineHeight: 1.6 }}>
              This context is built from the incidents you have discussed with Rootmind-AI. Hindsight provides semantic recall; this overview summarizes your locally stored incident history.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '16px' }}>
            <MemorySection
              title="Common Technologies"
              icon={Code2}
              items={data.technologies}
              emptyText="Technologies will appear as you work through incidents."
            />
            <MemorySection
              title="Frequent Problem Areas"
              icon={Brain}
              items={data.frequent_problems}
              emptyText="Repeated categories become visible as your history grows."
            />
            <MemorySection
              title="Solutions That Worked"
              icon={Check}
              items={data.successful_solutions}
              emptyText="Resolved incidents with confirmed solutions will show up here."
            />
          </div>
        </>
      )}
    </section>
  )
}
