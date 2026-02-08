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
      </div>

      <div className="details-section">
        <div className="details-section-title">Quick Actions</div>
        <div className="details-action-grid">
            <div className="details-action-btn" onClick={() => onExecute && onExecute(item)}>
                <Zap size={14} />
                <span>Run</span>
            </div>
            {item.path && (
                <div className="details-action-btn" onClick={copyPath}>
                    <Clipboard size={14} />
                    <span>Path</span>
                </div>
            )}
            <div className="details-action-btn">
                <Share2 size={14} />
                <span>Share</span>
            </div>
        </div>
      </div>

      <div className="details-section">
        <div className="details-section-title">Information</div>
        <div className="meta-grid">
           {item.desc && (
            <div className="meta-row">
              <span className="meta-label">Description</span>
              <span className="meta-value">{item.desc}</span>
            </div>
          )}
          {item.path && (
            <div className="meta-row">
              <span className="meta-label">Path</span>
              <span className="meta-value">{item.path}</span>
            </div>
          )}
          {item.cat && (
            <div className="meta-row">
              <span className="meta-label">Category</span>
              <span className="meta-value">{item.cat}</span>
            </div>
          )}
          {item.content && (
            <div className="meta-row">
              <span className="meta-label">Content</span>
              <span className="meta-value" style={{ whiteSpace: 'pre-wrap', maxHeight: '200px', overflow: 'hidden' }}>{item.content}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
