import { useState } from 'react'
import { ItemIcon } from './Icons'
import { Zap, Clipboard, Share2, ExternalLink, FileText, Terminal, Info, Globe, Shield, Activity, Database, Check, GitBranch } from 'lucide-react'
import pytron from 'pytron-client'

export default function DetailsPanel({ item, onExecute }) {
  const [copied, setCopied] = useState(false);

  if (!item) return null;

  const copyPath = () => {
    if (item.path) {
      pytron.copy_to_clipboard(item.path);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
      pytron.send_notification("Copied", "Path copied to clipboard");
    }
  };

  const handleShare = async () => {
    const textToShare = item.content || item.path || item.url || item.name;
    try {
      if (navigator.share) {
        await navigator.share({
          title: item.name,
          text: item.desc,
          url: item.url || item.path || undefined
        });
      } else {
        pytron.copy_to_clipboard(textToShare);
        pytron.send_notification("Shared", "Copied to clipboard");
      }
    } catch (err) {
      // ignore
    }
  };

  return (
    <div className="ray-details-panel">
      {/* Hero Header */}
      <div className="details-hero">
        <div className="details-icon-wrapper">
          <ItemIcon item={item} large={true} />
        </div>
        <div className="details-hero-text">
          <h2 className="details-title">{item.name}</h2>
          <div className="details-tags">
            {item.cat && <span className="details-pill">{item.cat}</span>}
            {item.branch && (
              <span className="details-pill branch-pill">
                <GitBranch size={11} />
                {item.branch}
              </span>
            )}
            {item.is_dirty !== undefined && (
              <span className={`details-pill status-pill ${item.is_dirty ? 'dirty' : 'clean'}`}>
                {item.is_dirty ? 'Modified' : 'Clean'}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* AI Summary / Special Brain Block */}
      {item.cat === 'AI Brain' && item.content && (
        <div className="details-card ai-card">
          <div className="details-card-header">
            <Zap size={13} className="card-header-icon" />
            <span>Intelligence Summary</span>
          </div>
          <div className="ai-content-body">{item.content}</div>
        </div>
      )}

      {/* Primary Actions */}
      <div className="details-card actions-card">
        <div className="details-card-header">
          <span>Quick Actions</span>
        </div>
        <div className="details-action-row">
          <button className="action-pill primary" onClick={() => onExecute && onExecute(item)}>
            <Zap size={14} />
            <span>Open</span>
          </button>
          {item.path && (
            <button className={`action-pill ${copied ? 'success' : ''}`} onClick={copyPath}>
              {copied ? <Check size={14} /> : <Clipboard size={14} />}
              <span>{copied ? 'Copied' : 'Copy Path'}</span>
            </button>
          )}
          <button className="action-pill" onClick={handleShare}>
            <Share2 size={14} />
            <span>Share</span>
          </button>
        </div>
      </div>

      {/* Metadata & Context */}
      <div className="details-card meta-card">
        <div className="details-card-header">
          <span>Information</span>
        </div>
        <div className="meta-entries">
          {item.path && (
            <div className="meta-entry" onClick={copyPath} title="Click to copy path">
              <div className="meta-entry-label">
                <Terminal size={12} />
                <span>Path</span>
              </div>
              <div className="meta-entry-value">{item.path}</div>
            </div>
          )}

          {item.url && (
            <div className="meta-entry" onClick={() => onExecute && onExecute(item)} title="Click to open URL">
              <div className="meta-entry-label">
                <Globe size={12} />
                <span>URL</span>
              </div>
              <div className="meta-entry-value">{item.url}</div>
            </div>
          )}

          {item.desc && !item.path && !item.url && (
            <div className="meta-entry">
              <div className="meta-entry-label">
                <Info size={12} />
                <span>Description</span>
              </div>
              <div className="meta-entry-value">{item.desc}</div>
            </div>
          )}

          {item.content && (
            <div className="snippet-preview-container">
              <div className="meta-entry-label">
                <FileText size={12} />
                <span>Content</span>
              </div>
              <pre className="snippet-code-block">{item.content}</pre>
            </div>
          )}

          {!item.content && !item.path && !item.url && !item.desc && (
            <div className="meta-empty">
              <Shield size={18} opacity={0.3} />
              <span>Ready to execute</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
