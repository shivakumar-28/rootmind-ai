import { useRef } from 'react'
import { ArrowUp, CornerDownLeft, Sparkles } from 'lucide-react'

export default function ChatComposer({ value, onChange, onSubmit, busy }) {
  const inputRef = useRef(null)

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      onSubmit()
    }
  }

  return (
    <div className="composer-wrap">
      <div className={`composer ${busy ? 'composer-busy' : ''}`}>
        <textarea
          ref={inputRef}
          rows={2}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe the bug, error, or incident you're investigating..."
          aria-label="Message Rootmind-AI"
          disabled={busy}
        />
        <div className="composer-bottom">
          <div className="composer-hints">
            <span className="composer-memory-mark">
              <Sparkles size={14} />
            </span>
            <span>Rootmind-AI remembers your engineering context.</span>
          </div>
          <div className="composer-actions">
            <span className="composer-shortcut">
              <CornerDownLeft size={12} /> <kbd>Enter</kbd> to send
            </span>
            <button
              className="send-button"
              onClick={onSubmit}
              disabled={busy || !value.trim()}
              aria-label="Send message"
            >
              {busy ? <span className="send-spinner" /> : <ArrowUp size={18} />}
            </button>
          </div>
        </div>
      </div>
      <p className="composer-disclaimer">
        AI-generated guidance can be imperfect. Verify commands before running them.
      </p>
    </div>
  )
}
