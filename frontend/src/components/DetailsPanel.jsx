import { ItemIcon } from './Icons'
import { Zap, Clipboard, Share2, ExternalLink, FileText, Terminal, Info, Globe, Shield, Activity, Database } from 'lucide-react'
import pytron from 'pytron-client'

export default function DetailsPanel({ item, onExecute }) {
  if (!item) return null;

  const copyPath = () => {
    if (item.path) {
      pytron.copy_to_clipboard(item.path);
      pytron.send_notification("Copied", "Path saved to clipboard");
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
        pytron.send_notification("Copied to Share", "Item content copied to clipboard!");
      }
    } catch (err) {
      // User cancelled share or failed
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
          <div className="details-action-btn" onClick={handleShare}>
            <Share2 size={18} />
            <span>Share</span>
          </div>
        </div>
      </div>

      <div className="details-section">
        <div className="details-section-title">Context & Info</div>
        <div className="meta-list">
          {item.path && (
            <div className="meta-row" onClick={copyPath}>
              <div className="meta-item-header">
                <Terminal size={14} className="meta-icon" />
                <span className="meta-label">Path</span>
              </div>
              <span className="meta-value truncate-path" title={item.path}>{item.path}</span>
            </div>
          )}

          {item.url && (
            <div className="meta-row" onClick={() => onExecute(item)}>
              <div className="meta-item-header">
                <Globe size={14} className="meta-icon" />
                <span className="meta-label">Target URL</span>
              </div>
              <span className="meta-value truncate-url" title={item.url}>{item.url}</span>
            </div>
          )}

          <div className="meta-grid">
            {item.cat && (
              <div className="meta-grid-item">
                <Database size={12} />
                <span>{item.cat}</span>
              </div>
            )}
            {item.type && (
              <div className="meta-grid-item">
                <Info size={12} />
                <span>{item.type.toUpperCase()}</span>
              </div>
            )}
          </div>

          {item.content && (
            <div className="meta-row content-preview-box">
              <div className="meta-item-header">
                <FileText size={14} className="meta-icon" />
                <span className="meta-label">Snippet Preview</span>
              </div>
              <div className="details-content-preview">
                {item.content}
              </div>
            </div>
          )}

          {!item.content && !item.path && !item.url && (
            <div className="details-empty-preview">
              <Shield size={24} opacity={0.2} />
              <p>No additional metadata available for this item.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
