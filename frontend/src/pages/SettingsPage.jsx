import { useState } from 'react'
import { Check, ChevronRight, HardDrive, Monitor, Moon, PanelLeft, ShieldCheck, SlidersHorizontal, Sun } from 'lucide-react'

export default function SettingsPage({
  collapsed,
  onToggleSidebar,
  backendStatus,
  memoryStatus,
  conversationCount,
  theme,
  onToggleTheme,
}) {
  const [compact, setCompact] = useState(collapsed)

  function toggleCompact() {
    const next = !compact
    setCompact(next)
    onToggleSidebar(next)
  }

  return (
    <section className="workspace-page settings-page">
      <div className="page-eyebrow">
        <SlidersHorizontal size={14} /> WORKSPACE PREFERENCES
      </div>
      <div className="page-title-row">
        <div>
          <h1>Settings</h1>
          <p>Workspace status and display preferences.</p>
        </div>
      </div>

      <div className="settings-card">
        <div className="settings-card-heading">
          <div className="settings-heading-icon">
            <Monitor size={18} />
          </div>
          <div>
            <strong>Appearance & Theme</strong>
            <span>Choose between Light SaaS and Dark Neon AI engineering themes.</span>
          </div>
        </div>

        <div className="settings-row">
          <span className="sidebar-nav-icon nav-icon-violet">
            {theme === 'light' ? <Sun size={16} /> : <Moon size={16} />}
          </span>
          <span className="settings-row-copy">
            <strong>Active Theme</strong>
            <small>{theme === 'light' ? 'Light mode is active' : 'Dark Neon mode is active'}</small>
          </span>
          <div className="theme-switcher" style={{ width: '200px' }}>
            <button
              className={`theme-switcher-btn ${theme === 'light' ? 'active' : ''}`}
              onClick={() => theme !== 'light' && onToggleTheme()}
            >
              <Sun size={13} /> ☀ Light
            </button>
            <button
              className={`theme-switcher-btn ${theme === 'dark' ? 'active' : ''}`}
              onClick={() => theme !== 'dark' && onToggleTheme()}
            >
              <Moon size={13} /> 🌙 Dark Neon
            </button>
          </div>
        </div>

        <button className="settings-row" onClick={toggleCompact}>
          <span className="sidebar-nav-icon nav-icon-blue">
            <PanelLeft size={16} />
          </span>
          <span className="settings-row-copy">
            <strong>Compact sidebar</strong>
            <small>Keep more room for your conversation.</small>
          </span>
          <span className={`settings-switch ${compact ? 'settings-switch-on' : ''}`}>
            <span />
          </span>
        </button>
      </div>

      <div className="settings-card">
        <div className="settings-card-heading">
          <div className="settings-heading-icon">
            <ShieldCheck size={18} />
          </div>
          <div>
            <strong>Connections</strong>
            <span>Updated when the app makes a request. No background polling.</span>
          </div>
        </div>
        <div className="settings-row settings-row-static">
          <span className="sidebar-nav-icon nav-icon-emerald">
            <span className={`status-pill-dot ${backendStatus === 'connected' ? 'status-connected' : 'status-offline'}`} style={{ width: '10px', height: '10px' }} />
          </span>
          <span className="settings-row-copy">
            <strong>Backend API</strong>
            <small>
              {backendStatus === 'connected'
                ? 'Connected on the most recent request'
                : backendStatus === 'offline'
                ? 'The most recent request could not reach the backend'
                : 'Not checked yet'}
            </small>
          </span>
          <span className="status-pill">{backendStatus === 'connected' ? 'Backend Ready' : backendStatus === 'offline' ? 'Offline' : 'Idle'}</span>
        </div>
        <div className="settings-row settings-row-static">
          <span className="sidebar-nav-icon nav-icon-indigo">
            <span className={`status-pill-dot ${memoryStatus === 'available' ? 'status-available' : 'status-offline'}`} style={{ width: '10px', height: '10px' }} />
          </span>
          <span className="settings-row-copy">
            <strong>Long-term Memory</strong>
            <small>
              {memoryStatus === 'available'
                ? 'Available on the most recent chat response'
                : memoryStatus === 'unavailable'
                ? 'Unavailable on the most recent chat response'
                : 'Status appears after your first chat'}
            </small>
          </span>
          <span className="status-pill">{memoryStatus === 'available' ? 'Memory Ready' : memoryStatus === 'unavailable' ? 'Unavailable' : 'Idle'}</span>
        </div>
      </div>

      <div className="settings-card">
        <div className="settings-card-heading">
          <div className="settings-heading-icon">
            <HardDrive size={18} />
          </div>
          <div>
            <strong>Conversation Storage</strong>
            <span>Your recent chat list is stored securely in this browser.</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px 20px', background: 'var(--pill-active)', margin: '14px', borderRadius: '12px' }}>
          <span style={{ font: '700 20px "Manrope", sans-serif', color: 'var(--accent-indigo)' }}>
            {conversationCount}
          </span>
          <small style={{ flex: 1, color: 'var(--ink-secondary)', fontSize: '13px' }}>
            {conversationCount === 1 ? 'saved conversation' : 'saved conversations'}
          </small>
          <Check size={18} style={{ color: '#10b981' }} />
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--ink-muted)', fontSize: '12px', marginTop: '16px' }}>
        <ChevronRight size={14} /> API credentials are configured on the backend and are never sent to the browser.
      </div>
    </section>
  )
}
