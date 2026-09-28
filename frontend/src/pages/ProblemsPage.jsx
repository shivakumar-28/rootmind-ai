import { useEffect, useState } from 'react'
import { Activity, ArrowUpRight, BarChart3, CircleHelp, Code2, Database, Layers3 } from 'lucide-react'
import { getProblems } from '../services/api.js'

const icons = [Activity, Database, Code2, Layers3]

export default function ProblemsPage() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getProblems()
      .then(setData)
      .catch((reason) => setError(reason.message))
  }, [])

  return (
    <section className="data-page">
      <div className="page-eyebrow">
        <BarChart3 size={14} /> PATTERNS FROM YOUR HISTORY
      </div>
      <div className="page-title-row">
        <div>
          <h1>Recurring Problems</h1>
          <p>Spot the issues that keep coming back, and the fixes that have worked before.</p>
        </div>
        <div className="status-pill status-available">
          <span className="status-pill-dot" /> Historical Insights
        </div>
      </div>

      {error ? (
        <div className="error-card">
          <CircleHelp size={18} />
          <span>{error}</span>
        </div>
      ) : !data ? (
        <div className="settings-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--ink-muted)' }}>
          Loading incident patterns…
        </div>
      ) : data.problems.length === 0 ? (
        <div className="settings-card" style={{ padding: '40px', textAlign: 'center' }}>
          <div className="settings-heading-icon" style={{ margin: '0 auto 16px' }}>
            <Activity size={24} />
          </div>
          <h2 style={{ margin: '0 0 8px', fontSize: '16px', color: 'var(--ink-primary)' }}>
            Your patterns will take shape here
          </h2>
          <p style={{ margin: 0, color: 'var(--ink-muted)', fontSize: '13px' }}>
            As you investigate incidents, Rootmind-AI will group them by category and surface common technologies, errors, and successful resolutions.
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '16px' }}>
          {data.problems.map((problem, index) => {
            const Icon = icons[index % icons.length]
            return (
              <article className="settings-card" style={{ padding: '20px' }} key={problem.category}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                  <div className="settings-heading-icon">
                    <Icon size={18} />
                  </div>
                  <span className="widget-badge">
                    {problem.count} {problem.count === 1 ? 'incident' : 'incidents'}
                  </span>
                </div>
                <h2 style={{ margin: '0 0 14px', fontSize: '16px', color: 'var(--ink-primary)' }}>
                  {problem.category}
                </h2>
                {problem.technologies?.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <label style={{ display: 'block', fontSize: '10px', fontWeight: 700, color: 'var(--ink-subtle)', marginBottom: '6px', letterSpacing: '0.8px' }}>
                      COMMON TECHNOLOGIES
                    </label>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {problem.technologies.map((technology) => (
                        <span key={technology} style={{ padding: '4px 8px', borderRadius: '6px', background: '#f1f5f9', color: 'var(--ink-secondary)', fontSize: '11px', fontWeight: 500 }}>
                          {technology}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {problem.common_errors?.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <label style={{ display: 'block', fontSize: '10px', fontWeight: 700, color: 'var(--ink-subtle)', marginBottom: '6px', letterSpacing: '0.8px' }}>
                      COMMON ERRORS
                    </label>
                    {problem.common_errors.map((err) => (
                      <p key={err} style={{ margin: '4px 0', paddingLeft: '10px', borderLeft: '2px solid var(--accent-indigo)', color: 'var(--ink-secondary)', fontSize: '12px' }}>
                        {err}
                      </p>
                    ))}
                  </div>
                )}
                {problem.successful_solutions?.length > 0 && (
                  <div style={{ paddingTop: '12px', borderTop: '1px solid #f1f5f9' }}>
                    <label style={{ display: 'block', fontSize: '10px', fontWeight: 700, color: '#10b981', marginBottom: '6px', letterSpacing: '0.8px' }}>
                      PREVIOUSLY SUCCESSFUL
                    </label>
                    {problem.successful_solutions.map((solution) => (
                      <p key={solution} style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', margin: '4px 0', color: '#059669', fontSize: '12px' }}>
                        <ArrowUpRight size={14} style={{ flex: 'none', marginTop: '2px' }} />
                        {solution}
                      </p>
                    ))}
                  </div>
                )}
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
