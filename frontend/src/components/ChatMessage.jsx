import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  AlertCircle,
  Bot,
  BrainCircuit,
  Check,
  ChevronDown,
  CircleCheck,
  Copy,
  FileCode2,
  Sparkles,
  UserRound,
  Zap,
} from 'lucide-react'

function CodeBlock({ children, className }) {
  const [copied, setCopied] = useState(false)
  const language = /language-(\w+)/.exec(className || '')?.[1] || 'code'
  const code = String(children).replace(/\n$/, '')

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1400)
    } catch {
      setCopied(false)
    }
  }

  return (
    <div className="code-frame">
      <div className="code-frame-header">
        <span>
          <FileCode2 size={14} />
          {language}
        </span>
        <button onClick={copyCode} aria-label="Copy code">
          {copied ? <Check size={13} /> : <Copy size={13} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre>
        <code>{children}</code>
      </pre>
    </div>
  )
}

function IncidentCard({ incident }) {
  const fields = [
    ['Problem', incident.problem],
    ['Technology', incident.technology],
    ['Error', incident.error],
    ['Root cause', incident.root_cause],
    ['Solution', incident.solution],
    ['Outcome', incident.outcome],
  ].filter(([, value]) => value)

  if (!fields.length) return null
  const resolved = Boolean(incident.outcome && /resolved|fixed|working|successful|recovered/i.test(incident.outcome))

  return (
    <section className="dashboard-widget-card" style={{ marginTop: '16px', padding: '18px 20px' }}>
      <div className="widget-header" style={{ paddingBottom: '12px', borderBottom: '1px solid #f1f5f9' }}>
        <div className="widget-title">
          <div className="widget-icon" style={{ background: '#f3e8ff', color: 'var(--accent-violet)' }}>
            <Zap size={18} />
          </div>
          <div>
            <div style={{ fontSize: '10px', color: 'var(--ink-subtle)', fontWeight: 700, letterSpacing: '0.8px' }}>
              INCIDENT CAPTURED
            </div>
            <div style={{ color: 'var(--ink-primary)', fontSize: '13px', fontWeight: 700 }}>
              {incident.problem || incident.category || 'Engineering Incident'}
            </div>
          </div>
        </div>
        {incident.category && <span className="widget-badge">{incident.category}</span>}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '12px', paddingTop: '10px' }}>
        {fields
          .filter(([label]) => label !== 'Problem')
          .map(([label, value]) => (
            <div key={label} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <span style={{ fontSize: '11px', color: 'var(--ink-muted)', fontWeight: 600 }}>{label}</span>
              <strong style={{ fontSize: '12.5px', color: 'var(--ink-primary)', fontWeight: 600, overflowWrap: 'anywhere' }}>
                {value}
              </strong>
            </div>
          ))}
      </div>

      {resolved && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10b981', fontSize: '12px', fontWeight: 600, marginTop: '8px', paddingTop: '10px', borderTop: '1px solid #f1f5f9' }}>
          <CircleCheck size={15} /> Outcome recorded as resolved
        </div>
      )}
    </section>
  )
}

function MemoryDetails({ memories, status }) {
  const [open, setOpen] = useState(false)
  if (status === 'unavailable' && !memories.length) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px', color: '#d97706', fontSize: '12px' }}>
        <AlertCircle size={15} /> Memory service unavailable for this response
      </div>
    )
  }
  if (!memories.length) return null

  return (
    <section className={`memory-panel ${open ? 'memory-panel-open' : ''}`}>
      <button className="memory-panel-toggle" onClick={() => setOpen((value) => !value)} aria-expanded={open}>
        <span className="memory-panel-icon">
          <BrainCircuit size={17} />
        </span>
        <span className="memory-panel-copy">
          <strong>Memory assisted</strong>
          <small>
            {memories.length} relevant {memories.length === 1 ? 'memory' : 'memories'} retrieved from Hindsight
          </small>
        </span>
        <ChevronDown size={17} className="memory-chevron" />
      </button>
      {open && (
        <div className="memory-panel-content">
          {memories.map((memory, index) => (
            <div key={`${index}-${memory.content}`} className="memory-item">
              <span className="memory-item-dot" />
              <p>{memory.content}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const data = message.data

  return (
    <article className={`message-row ${isUser ? 'message-user' : 'message-assistant'}`}>
      <div className={`message-avatar ${isUser ? 'user-avatar' : 'assistant-avatar'}`}>
        {isUser ? <UserRound size={17} /> : <Bot size={18} />}
      </div>
      <div className="message-content">
        <div className="message-meta">
          <span className="message-author">{isUser ? 'You' : 'Rootmind-AI'}</span>
          {!isUser && (
            <span className="message-badge badge-assistant">
              {data?.incident_detected ? 'INCIDENT ANALYSIS' : 'ENGINEERING ASSISTANT'}
            </span>
          )}
          {!isUser && data?.memory_used && (
            <span className="message-badge badge-memory">
              <BrainCircuit size={13} /> Memory assisted
            </span>
          )}
        </div>
        <div className={`markdown-body ${isUser ? 'user-message-body' : ''}`}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ inline, className, children, ...props }) {
                return inline ? (
                  <code className={className} {...props}>
                    {children}
                  </code>
                ) : (
                  <CodeBlock className={className}>{children}</CodeBlock>
                )
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {!isUser && data && <MemoryDetails memories={data.relevant_memories || []} status={data.memory_status} />}
        {!isUser && data?.incident_detected && data.incident && <IncidentCard incident={data.incident} />}
      </div>
    </article>
  )
}

export function TypingIndicator() {
  return (
    <div className="message-row message-assistant typing-row" style={{ alignItems: 'center' }}>
      <div className="message-avatar assistant-avatar">
        <Bot size={18} />
      </div>
      <div className="typing-content" style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--ink-muted)', fontSize: '13px' }}>
        <div className="typing-dots" style={{ display: 'flex', gap: '4px' }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-indigo)', animation: 'pulse-dot .9s ease-in-out infinite' }} />
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-indigo)', animation: 'pulse-dot .9s ease-in-out infinite 0.15s' }} />
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-indigo)', animation: 'pulse-dot .9s ease-in-out infinite 0.3s' }} />
        </div>
        <span>Rootmind is analyzing...</span>
        <Sparkles size={14} style={{ color: 'var(--accent-indigo)' }} />
      </div>
    </div>
  )
}
