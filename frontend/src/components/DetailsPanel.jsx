import { ItemIcon } from './Icons'
import { Zap, Clipboard, Share2 } from 'lucide-react'
import pytron from 'pytron-client'

export default function DetailsPanel({ item, onExecute }) {
  if (!item) return null;

  const copyPath = () => {
    if (item.path) {
      pytron.copy_to_clipboard(item.path);
      pytron.notify("Copied", "Path saved to clipboard", "success");
    }
  };

  return (
    <div className="ray-details-panel">
      <div className="details-header">
        <div className="details-icon-large">
          <ItemIcon item={item} large={true} />
        </div>
        <div className="details-title">{item.name}</div>
        <div className="details-desc-hero">{item.desc}</div>
      </div>

      <div className="details-section">
        <div className="details-section-title">Key Actions</div>
        <div className="details-action-grid">
          <div className="details-action-btn primary" onClick={() => onExecute && onExecute(item)}>
            <Zap size={18} color="var(--accent)" />
            <span>Execute</span>
          </div>
          {item.path && (
            <div className="details-action-btn" onClick={copyPath}>
              <Clipboard size={18} />
              <span>Copy Path</span>
            </div>
          )}
          <div className="details-action-btn" onClick={() => pytron.notify("Coming Soon", "Shared functionality is in development", "info")}>
            <Share2 size={18} />
            <span>Share</span>
          </div>
        </div>
      </div>

      <div className="details-section">
        <div className="details-section-title">Metadata</div>
        <div className="meta-list">
          {item.path && (
            <div className="meta-row" onClick={() => pytron.notify("Hint", "Hover to reveal full path", "info")}>
              <span className="meta-label">Location</span>
              <span className="meta-value" title={item.path}>{item.path}</span>
            </div>
          )}
          {item.cat && (
            <div className="meta-row">
              <span className="meta-label">Source</span>
              <span className="meta-value">{item.cat}</span>
            </div>
          )}
          {item.type && (
            <div className="meta-row">
              <span className="meta-label">Identity</span>
              <span className="meta-value">{item.type}</span>
            </div>
          )}
          {item.content && (
            <div className="meta-row" style={{ marginTop: '8px' }}>
              <span className="meta-label">Snippets Content</span>
              <div className="details-content-preview">
                {item.content}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
