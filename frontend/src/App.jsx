import { useEffect, useRef, useState } from 'react'
import { BrainCircuit, Menu, Moon, Radio, Sun, Sparkles } from 'lucide-react'
import Sidebar from './components/Sidebar.jsx'
import ChatMessage, { TypingIndicator } from './components/ChatMessage.jsx'
import ChatComposer from './components/ChatComposer.jsx'
import EmptyState from './components/EmptyState.jsx'
import ProblemsPage from './pages/ProblemsPage.jsx'
import MemoryPage from './pages/MemoryPage.jsx'
import SearchPage from './pages/SearchPage.jsx'
import SettingsPage from './pages/SettingsPage.jsx'
import { sendMessage } from './services/api.js'

const STORAGE_KEY = 'devmemory-conversations'
const THEME_KEY = 'rootmind-theme'

const createConversation = () => ({
  id: crypto.randomUUID(),
  title: 'New conversation',
  messages: [],
  updatedAt: Date.now(),
})

function readConversations() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    return Array.isArray(saved) ? saved : []
  } catch {
    return []
  }
}

const pageTitles = {
  chat: 'Engineering Assistant',
  search: 'Search Workspace',
  problems: 'Recurring Problems',
  memory: 'Developer Memory',
  settings: 'Workspace Settings',
}

export default function App() {
  const [conversations, setConversations] = useState(readConversations)
  const [selectedId, setSelectedId] = useState(null)
  const [active, setActive] = useState('chat')
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [backendStatus, setBackendStatus] = useState('idle')
  const [memoryStatus, setMemoryStatus] = useState('idle')

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem(THEME_KEY) || 'light'
  })

  const bottomRef = useRef(null)
  const current = conversations.find((conversation) => conversation.id === selectedId)
  const messages = current?.messages || []

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
  }, [conversations])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem(THEME_KEY, theme)
  }, [theme])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages.length, busy])

  function toggleTheme() {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'))
  }

  function updateConversation(id, updater) {
    setConversations((items) =>
      items.map((conversation) => (conversation.id === id ? updater(conversation) : conversation))
    )
  }

  function newChat() {
    setSelectedId(null)
    setActive('chat')
    setDraft('')
    setError(null)
  }

  function selectConversation(id) {
    setSelectedId(id)
    setActive('chat')
    setError(null)
  }

  async function submitMessage(messageOverride, options = {}) {
    const text = (messageOverride ?? draft).trim()
    if (!text || busy) return

    const retrying = Boolean(options.retry)
    let conversation = options.conversationId
      ? conversations.find((item) => item.id === options.conversationId)
      : current

    if (!conversation && !retrying) {
      conversation = createConversation()
      setConversations((items) => [conversation, ...items])
      setSelectedId(conversation.id)
    }
    if (!conversation) return

    const id = conversation.id
    if (!retrying) {
      const nextMessages = [...conversation.messages, { role: 'user', content: text }]
      updateConversation(id, (item) => ({
        ...item,
        title: item.messages.length ? item.title : text.slice(0, 54),
        messages: nextMessages,
        updatedAt: Date.now(),
      }))
      setDraft('')
    }

    setError(null)
    setBusy(true)

    try {
      const result = await sendMessage(text, id)
      const returnedId = result.conversation_id || id
      updateConversation(id, (item) => ({
        ...item,
        id: returnedId,
        messages: [...item.messages, { role: 'assistant', content: result.response, data: result }],
        updatedAt: Date.now(),
      }))
      if (returnedId !== id) setSelectedId((selected) => (selected === id ? returnedId : selected))
      setBackendStatus('connected')
      setMemoryStatus(result.memory_status || 'available')
    } catch (reason) {
      const detail = reason.message || 'We could not complete this request.'
      setBackendStatus(detail.includes('Could not reach') ? 'offline' : 'connected')
      setError({ message: detail, text, conversationId: id })
    } finally {
      setBusy(false)
    }
  }

  function handleSettings() {
    setActive('settings')
    setMobileOpen(false)
  }

  const currentTitle = active === 'chat' ? current?.title || 'Dashboard / New Chat' : pageTitles[active]

  return (
    <div className="app-shell">
      <Sidebar
        active={active}
        onNavigate={setActive}
        conversations={conversations}
        selectedId={selectedId}
        onNewChat={newChat}
        onSelectConversation={selectConversation}
        collapsed={collapsed}
        onToggle={() => setCollapsed((value) => !value)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
        onSettings={handleSettings}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      <main className="main-shell">
        <header className="workspace-topbar">
          <div className="topbar-leading">
            <button className="mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation">
              <Menu size={20} />
            </button>
            <div className="topbar-brand-mini">
              <span>
                <BrainCircuit size={16} />
              </span>
              <strong>
                Rootmind<span>-AI</span>
              </strong>
            </div>
            <span className="topbar-divider" />
            <div className="topbar-current">
              <span>Workspace</span>
              <span className="breadcrumb-slash">/</span>
              <strong>{currentTitle}</strong>
            </div>
          </div>

          <div className="topbar-trailing">
            <button
              className="status-pill"
              onClick={toggleTheme}
              title={`Switch to ${theme === 'light' ? 'Dark Neon' : 'Light'} theme`}
              style={{ padding: '5px 10px', gap: '6px' }}
            >
              {theme === 'light' ? <Moon size={14} style={{ color: 'var(--accent-indigo)' }} /> : <Sun size={14} style={{ color: '#f59e0b' }} />}
              <span>{theme === 'light' ? 'Dark Neon' : 'Light'}</span>
            </button>

            <span className="topbar-divider" />

            <span className={`status-pill status-${backendStatus}`}>
              <span className="status-pill-dot" />
              {backendStatus === 'connected'
                ? 'Backend Ready'
                : backendStatus === 'offline'
                ? 'Backend Offline'
                : 'Backend Idle'}
            </span>

            <span className="topbar-divider" />

            <span className={`status-pill status-${memoryStatus}`}>
              <Radio size={13} style={{ color: 'var(--accent-indigo)' }} />
              {memoryStatus === 'available'
                ? 'Memory Ready'
                : memoryStatus === 'unavailable'
                ? 'Memory Offline'
                : 'Memory Idle'}
            </span>
          </div>
        </header>

        {active === 'problems' ? (
          <ProblemsPage />
        ) : active === 'memory' ? (
          <MemoryPage />
        ) : active === 'search' ? (
          <SearchPage conversations={conversations} onSelectConversation={selectConversation} />
        ) : active === 'settings' ? (
          <SettingsPage
            collapsed={collapsed}
            onToggleSidebar={setCollapsed}
            backendStatus={backendStatus}
            memoryStatus={memoryStatus}
            conversationCount={conversations.length}
            theme={theme}
            onToggleTheme={toggleTheme}
          />
        ) : (
          <div className="chat-page">
            {!selectedId || messages.length === 0 ? (
              <EmptyState
                onPrompt={(prompt) => submitMessage(prompt)}
                conversations={conversations}
                onSelectConversation={selectConversation}
                memoryStatus={memoryStatus}
                onNavigate={setActive}
              />
            ) : (
              <div className="message-scroll">
                <div className="message-column">
                  {messages.map((message, index) => (
                    <ChatMessage message={message} key={`${index}-${message.role}`} />
                  ))}
                  {busy && <TypingIndicator />}
                  {error && (
                    <div className="error-card" style={{ marginTop: '16px' }}>
                      <div className="error-icon">
                        <span>!</span>
                      </div>
                      <div className="error-copy">
                        <strong>We couldn't complete this request</strong>
                        <span>{error.message}</span>
                      </div>
                      <button
                        onClick={() =>
                          submitMessage(error.text, { retry: true, conversationId: error.conversationId })
                        }
                      >
                        Try again
                      </button>
                    </div>
                  )}
                  <div ref={bottomRef} />
                </div>
              </div>
            )}

            {messages.length === 0 && error && (
              <div className="initial-error error-card" style={{ width: 'min(calc(100% - 48px), 880px)', margin: '0 auto 8px' }}>
                <div className="error-icon">
                  <span>!</span>
                </div>
                <div className="error-copy">
                  <strong>We couldn't complete this request</strong>
                  <span>{error.message}</span>
                </div>
                <button
                  onClick={() =>
                    submitMessage(error.text, { retry: true, conversationId: error.conversationId })
                  }
                >
                  Try again
                </button>
              </div>
            )}

            <ChatComposer value={draft} onChange={setDraft} onSubmit={() => submitMessage()} busy={busy} />
          </div>
        )}
      </main>
    </div>
  )
}
