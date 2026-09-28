import {
  Activity,
  ArrowUpRight,
  BrainCircuit,
  Bug,
  CheckCircle2,
  Clock,
  Code2,
  Cpu,
  History,
  MessageSquareText,
  Radio,
  Search,
  Server,
  Sparkles,
  Zap,
} from 'lucide-react'

const quickActions = [
  {
    icon: Bug,
    colorClass: 'icon-blue',
    title: 'Debug an Issue',
    description: 'Explain an error and help me debug it.',
    prompt: 'Explain this error and help me debug it: ',
  },
  {
    icon: History,
    colorClass: 'icon-indigo',
    title: 'Past Solutions',
    description: 'What did we fix previously?',
    prompt: 'What did we fix previously in our past incidents?',
  },
  {
    icon: BrainCircuit,
    colorClass: 'icon-violet',
    title: 'Developer Memory',
    description: 'Recall something from my engineering history.',
    prompt: 'Recall my past engineering history and saved memories.',
  },
  {
    icon: Code2,
    colorClass: 'icon-purple',
    title: 'Save a Solution',
    description: 'Remember this debugging solution.',
    prompt: 'Remember this debugging solution for future incidents: ',
  },
  {
    icon: Server,
    colorClass: 'icon-sky',
    title: 'API Reliability',
    description: 'Investigate API failures and errors.',
    prompt: 'Investigate API failures and 503 error codes in our backend.',
  },
  {
    icon: Zap,
    colorClass: 'icon-emerald',
    title: 'Continue Debugging',
    description: 'Continue from my previous conversation.',
    prompt: 'Continue debugging from our previous conversation.',
  },
]

export default function EmptyState({ onPrompt, conversations = [], onSelectConversation, memoryStatus, onNavigate }) {
  const recentItems = conversations.slice(0, 3)

  return (
    <div className="dashboard-scroll">
      <div className="dashboard-container">
        {/* HERO SECTION */}
        <section className="hero-card">
          <div className="hero-glow-bg" />
          <div className="hero-content">
            <div className="hero-text">
              <div className="hero-badge">
                <Sparkles size={13} /> Good to see you 👋
              </div>
              <h1 className="hero-title">
                Welcome to <span>Rootmind-AI</span>
              </h1>
              <div className="hero-subtitle">Your AI engineering memory</div>
              <p className="hero-description">
                Debug faster. Remember fixes. Continue where you left off with intelligent context recall.
              </p>
            </div>
            <div className="hero-visual">
              <div className="hero-visual-icon">
                <BrainCircuit size={44} strokeWidth={1.8} />
              </div>
              <span className="hero-orbit" />
            </div>
          </div>
        </section>

        {/* QUICK ACTION CARDS SECTION */}
        <section>
          <div className="dashboard-section-header">
            <div className="dashboard-section-title">
              <Sparkles size={16} />
              <span>Quick Actions</span>
            </div>
          </div>

          <div className="quick-actions-grid" style={{ marginTop: '16px' }}>
            {quickActions.map(({ icon: Icon, colorClass, title, description, prompt }) => (
              <button
                key={title}
                className="action-card"
                onClick={() => onPrompt(prompt)}
                title={title}
              >
                <div className={`action-card-icon ${colorClass}`}>
                  <Icon size={20} />
                </div>
                <div className="action-card-copy">
                  <strong>{title}</strong>
                  <small>{description}</small>
                </div>
                <ArrowUpRight size={16} className="action-card-arrow" />
              </button>
            ))}
          </div>
        </section>

        {/* DUAL WIDGETS SECTION: DEVELOPER MEMORY & RECENT ACTIVITY */}
        <div className="dashboard-dual-grid">
          {/* DEVELOPER MEMORY / HINDSIGHT SECTION */}
          <div className="dashboard-widget-card">
            <div className="widget-header">
              <div className="widget-title">
                <div className="widget-icon">
                  <BrainCircuit size={18} />
                </div>
                <span>Developer Memory</span>
              </div>
              <span className="widget-badge">
                <Radio size={11} style={{ display: 'inline', marginRight: '4px' }} />
                {memoryStatus === 'available' ? 'Hindsight Active' : 'Memory Ready'}
              </span>
            </div>
            <p style={{ margin: 0, color: 'var(--ink-muted)', fontSize: '12.5px', lineHeight: 1.6 }}>
              Hindsight memory engine retains root cause analyses, technology stacks, and debugging solutions across sessions.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: 'auto' }}>
              <button
                className="sidebar-nav-item sidebar-nav-active"
                style={{ height: '36px', width: 'auto', padding: '0 14px', fontSize: '12px' }}
                onClick={() => onNavigate('memory')}
              >
                <BrainCircuit size={15} /> View Saved Memories
              </button>
            </div>
          </div>

          {/* RECENT ACTIVITY SECTION */}
          <div className="dashboard-widget-card">
            <div className="widget-header">
              <div className="widget-title">
                <div className="widget-icon">
                  <Clock size={18} />
                </div>
                <span>Recent Activity</span>
              </div>
              {conversations.length > 0 && (
                <span className="recent-count" style={{ fontSize: '11px' }}>
                  {conversations.length} chats
                </span>
              )}
            </div>

            {recentItems.length === 0 ? (
              <div style={{ color: 'var(--ink-subtle)', fontSize: '12px', padding: '12px 0' }}>
                No recent conversations yet. Start a new chat above to record your debugging sessions.
              </div>
            ) : (
              <div className="activity-list">
                {recentItems.map((item) => (
                  <button
                    key={item.id}
                    className="activity-item"
                    onClick={() => onSelectConversation(item.id)}
                  >
                    <div className="activity-item-icon">
                      <MessageSquareText size={16} />
                    </div>
                    <div className="activity-item-content">
                      <span className="activity-item-title">{item.title}</span>
                      <span className="activity-item-meta">
                        {item.messages.length} messages · {new Date(item.updatedAt).toLocaleDateString()}
                      </span>
                    </div>
                    <ArrowUpRight size={14} style={{ color: '#94a3b8' }} />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
