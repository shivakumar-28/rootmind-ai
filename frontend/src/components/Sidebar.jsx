import { useMemo, useState } from 'react'
import {
  Activity,
  BrainCircuit,
  ChevronLeft,
  ChevronRight,
  Command,
  MessageSquarePlus,
  Moon,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Sun,
  X,
} from 'lucide-react'

const navigation = [
  { id: 'chat', label: 'Dashboard / New Chat', icon: MessageSquarePlus, colorClass: 'nav-icon-blue' },
  { id: 'search', label: 'Search', icon: Search, colorClass: 'nav-icon-indigo' },
  { id: 'memory', label: 'Developer Memory', icon: BrainCircuit, colorClass: 'nav-icon-violet' },
  { id: 'problems', label: 'Recurring Problems', icon: Activity, colorClass: 'nav-icon-purple' },
]

export default function Sidebar({
  active,
  onNavigate,
  conversations,
  selectedId,
  onNewChat,
  onSelectConversation,
  collapsed,
  onToggle,
  mobileOpen,
  onCloseMobile,
  onSettings,
  theme,
  onToggleTheme,
}) {
  const [query, setQuery] = useState('')

  const filteredConversations = useMemo(
    () =>
      conversations
        .filter((conversation) => conversation.title.toLowerCase().includes(query.toLowerCase()))
        .slice(0, 10),
    [conversations, query]
  )

  function navigate(id) {
    if (id === 'chat') onNewChat()
    else onNavigate(id)
    onCloseMobile()
  }

  return (
    <>
      {mobileOpen && <button className="drawer-scrim" onClick={onCloseMobile} aria-label="Close navigation" />}
      <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''} ${mobileOpen ? 'sidebar-mobile-open' : ''}`}>
        <div className="sidebar-brand">
          <div className="brand-symbol">
            <BrainCircuit size={23} strokeWidth={2} />
          </div>
          {!collapsed && (
            <div className="brand-wordmark">
              <strong>
                Rootmind<span>-AI</span>
              </strong>
              <small>Engineering workspace</small>
            </div>
          )}
          {!collapsed && (
            <button className="sidebar-icon-button mobile-close" onClick={onCloseMobile} aria-label="Close navigation">
              <X size={17} />
            </button>
          )}
          <button
            className="sidebar-icon-button collapse-control"
            onClick={onToggle}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        <button
          className={`sidebar-new-chat ${active === 'chat' && !selectedId ? 'sidebar-new-chat-active' : ''}`}
          onClick={() => navigate('chat')}
          title="Start a new chat"
        >
          <span className="sidebar-new-chat-icon">
            <MessageSquarePlus size={17} />
          </span>
          {!collapsed && (
            <>
              <span>Dashboard / New Chat</span>
              <kbd>
                <Command size={10} /> K
              </kbd>
            </>
          )}
        </button>

        <nav className="sidebar-nav" aria-label="Workspace navigation">
          {!collapsed && <div className="sidebar-section-label">WORKSPACE</div>}
          {navigation.slice(1).map(({ id, label, icon: Icon, colorClass }) => (
            <button
              key={id}
              className={`sidebar-nav-item ${active === id ? 'sidebar-nav-active' : ''}`}
              onClick={() => navigate(id)}
              title={label}
            >
              <span className={`sidebar-nav-icon ${colorClass}`}>
                <Icon size={16} strokeWidth={2} />
              </span>
              {!collapsed && <span>{label}</span>}
              {!collapsed && id === 'memory' && (
                <span className="nav-spark">
                  <Sparkles size={13} />
                </span>
              )}
            </button>
          ))}
        </nav>

        <section className="sidebar-recents">
          {!collapsed && (
            <div className="sidebar-recents-heading">
              <span className="sidebar-section-label">RECENT CONVERSATIONS</span>
              {conversations.length > 0 && <span className="recent-count">{conversations.length}</span>}
            </div>
          )}
          {!collapsed && conversations.length > 3 && (
            <label className="sidebar-search">
              <Search size={14} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Find a conversation..."
                aria-label="Find a conversation"
              />
            </label>
          )}
          {filteredConversations.length === 0 ? (
            !collapsed && (
              <p className="sidebar-empty">
                {conversations.length ? 'No matching conversations.' : 'Recent chats will appear here.'}
              </p>
            )
          ) : (
            filteredConversations.map((conversation) => (
              <button
                key={conversation.id}
                className={`recent-chat ${selectedId === conversation.id && active === 'chat' ? 'recent-chat-active' : ''}`}
                onClick={() => {
                  onSelectConversation(conversation.id)
                  onCloseMobile()
                }}
                title={conversation.title}
              >
                <span className="recent-chat-indicator">
                  <span />
                </span>
                {!collapsed && <span className="recent-chat-title">{conversation.title}</span>}
              </button>
            ))
          )}
        </section>

        <div className="sidebar-bottom">
          {!collapsed && (
            <div className="theme-switcher">
              <button
                className={`theme-switcher-btn ${theme === 'light' ? 'active' : ''}`}
                onClick={() => theme !== 'light' && onToggleTheme()}
                title="Light Mode"
              >
                <Sun size={13} /> ☀ Light
              </button>
              <button
                className={`theme-switcher-btn ${theme === 'dark' ? 'active' : ''}`}
                onClick={() => theme !== 'dark' && onToggleTheme()}
                title="Dark Neon Mode"
              >
                <Moon size={13} /> 🌙 Dark Neon
              </button>
            </div>
          )}

          <div className="workspace-security">
            <span className="security-icon">
              <ShieldCheck size={16} />
            </span>
            {!collapsed && <span>Private Workspace</span>}
          </div>
          <button
            className={`sidebar-nav-item sidebar-settings ${active === 'settings' ? 'sidebar-nav-active' : ''}`}
            onClick={() => {
              onSettings()
              onCloseMobile()
            }}
            title="Settings"
          >
            <span className="sidebar-nav-icon nav-icon-emerald">
              <Settings2 size={16} strokeWidth={2} />
            </span>
            {!collapsed && <span>Settings</span>}
          </button>
          {!collapsed && <div className="sidebar-version">ROOTMIND WORKSPACE <span>LOCAL</span></div>}
        </div>
      </aside>
    </>
  )
}
