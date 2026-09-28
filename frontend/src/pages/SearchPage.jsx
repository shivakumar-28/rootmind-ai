import { useMemo, useState } from 'react'
import { ArrowUpRight, MessageSquareText, Search as SearchIcon, X } from 'lucide-react'

export default function SearchPage({ conversations, onSelectConversation }) {
  const [query, setQuery] = useState('')

  const results = useMemo(() => {
    const value = query.trim().toLowerCase()
    if (!value) return []
    return conversations
      .filter(
        (conversation) =>
          conversation.title.toLowerCase().includes(value) ||
          conversation.messages.some((message) => message.content.toLowerCase().includes(value))
      )
      .sort((left, right) => right.updatedAt - left.updatedAt)
  }, [conversations, query])

  return (
    <section className="workspace-page search-page">
      <div className="page-eyebrow">
        <SearchIcon size={14} /> SEARCH YOUR WORKSPACE
      </div>
      <div className="page-title-row">
        <div>
          <h1>Find a Conversation</h1>
          <p>Search locally saved chat titles and messages from this browser.</p>
        </div>
      </div>

      <label className="sidebar-search" style={{ height: '50px', padding: '0 16px', borderRadius: '14px', marginBottom: '20px' }}>
        <SearchIcon size={18} />
        <input
          autoFocus
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search debugging notes, errors, or fixes..."
          aria-label="Search conversations"
          style={{ fontSize: '13px' }}
        />
        {query && (
          <button onClick={() => setQuery('')} aria-label="Clear search" style={{ background: 'transparent', border: 0, color: 'var(--ink-muted)' }}>
            <X size={16} />
          </button>
        )}
        <kbd style={{ font: '10px "DM Mono", monospace', color: 'var(--ink-subtle)', background: '#f1f5f9', padding: '2px 6px', borderRadius: '4px' }}>ESC</kbd>
      </label>

      {!query.trim() ? (
        <div className="settings-card" style={{ padding: '40px', textAlign: 'center' }}>
          <div className="settings-heading-icon" style={{ margin: '0 auto 16px' }}>
            <MessageSquareText size={22} />
          </div>
          <h2 style={{ margin: '0 0 8px', fontSize: '16px', color: 'var(--ink-primary)' }}>
            Your conversation history, searchable
          </h2>
          <p style={{ margin: 0, color: 'var(--ink-muted)', fontSize: '13px' }}>
            Search terms are matched against your saved conversation titles and messages. No conversations are fabricated.
          </p>
        </div>
      ) : results.length === 0 ? (
        <div className="settings-card" style={{ padding: '40px', textAlign: 'center' }}>
          <div className="settings-heading-icon" style={{ margin: '0 auto 16px' }}>
            <SearchIcon size={22} />
          </div>
          <h2 style={{ margin: '0 0 8px', fontSize: '16px', color: 'var(--ink-primary)' }}>
            No matching conversations
          </h2>
          <p style={{ margin: 0, color: 'var(--ink-muted)', fontSize: '13px' }}>
            Try a different search term.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {results.map((conversation) => (
            <button
              className="activity-item"
              style={{ padding: '14px 18px' }}
              key={conversation.id}
              onClick={() => onSelectConversation(conversation.id)}
            >
              <div className="activity-item-icon">
                <MessageSquareText size={18} />
              </div>
              <div className="activity-item-content">
                <span className="activity-item-title">{conversation.title}</span>
                <span className="activity-item-meta">
                  {conversation.messages.length} messages · {new Date(conversation.updatedAt).toLocaleDateString()}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--ink-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {conversation.messages.find((m) => m.role === 'user')?.content}
                </span>
              </div>
              <ArrowUpRight size={18} style={{ color: 'var(--ink-subtle)' }} />
            </button>
          ))}
        </div>
      )}
    </section>
  )
}
