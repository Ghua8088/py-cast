import { useState, useEffect } from 'react'
import pytron from 'pytron-client'

export default function ActionMenu({ item, query, onClose, setView, setQuery, executeItem }) {
  const [menuIndex, setMenuIndex] = useState(0);
  if (!item) return null;

  const actions = [
    { label: 'Open', kbd: '↵', action: () => { executeItem(item); onClose(); } },
    { label: 'Pin / Unpin', kbd: 'TAB', action: () => { pytron.toggle_pin(item.id).then(onClose); } },
  ];

  if (item.path) {
    actions.push({
      label: 'Reveal in Explorer', kbd: 'CTRL R',
      action: () => { executeItem({ ...item, action: 'reveal', keep_open: true }); onClose(); }
    });
    actions.push({
      label: 'Open Terminal Here', kbd: 'CTRL T',
      action: () => { executeItem({ ...item, action: 'open_term', keep_open: false }); onClose(); }
    });
    actions.push({
      label: 'Open in VS Code', kbd: 'CTRL .',
      action: () => { executeItem({ ...item, action: 'ide_code', keep_open: false }); onClose(); }
    });
  }

  if (item.github_url || item.remote_url) {
    actions.push({
      label: 'Open on GitHub', kbd: 'CTRL G',
      action: () => { executeItem({ ...item, action: 'open_github', keep_open: false }); onClose(); }
    });
  }

  if (item.url && !item.path) {
    actions.push({
      label: 'Open in Browser', kbd: '↵',
      action: () => { executeItem({ ...item, action: 'open_url', keep_open: false }); onClose(); }
    });
  }

  if (item.path || item.content || item.url) {
    actions.push({
      label: 'Copy Path / Content / URL', kbd: 'CTRL C',
      action: () => { pytron.copy_to_clipboard(item.content || item.url || item.path); onClose(); }
    });
  }

  if (item.action === 'settings') {
    actions.push({ label: 'Go to Settings', kbd: 'S', action: () => { setView('settings'); onClose(); setQuery(''); } });
  }

  useEffect(() => {
    const handleMenuKeys = (e) => {
      if (e.key === 'ArrowDown') {
        setMenuIndex(prev => Math.min(prev + 1, actions.length - 1));
        e.preventDefault();
      } else if (e.key === 'ArrowUp') {
        setMenuIndex(prev => Math.max(prev - 1, 0));
        e.preventDefault();
      } else if (e.key === 'Enter') {
        actions[menuIndex].action();
        e.preventDefault();
      } else if (e.key === 'Escape') {
        onClose();
        e.preventDefault();
      }
    };
    window.addEventListener('keydown', handleMenuKeys);
    return () => window.removeEventListener('keydown', handleMenuKeys);
  }, [menuIndex, actions]);

  return (
    <div className="ray-action-menu-overlay" onClick={onClose}>
      <div className="ray-action-menu" onClick={e => e.stopPropagation()}>
        <div className="action-menu-header">Actions</div>
        <div className="action-list">
          {actions.map((a, i) => (
            <div
              key={i}
              className={`action-row ${i === menuIndex ? 'active' : ''}`}
              onClick={a.action}
              onMouseEnter={() => setMenuIndex(i)}
            >
              <span className="action-label">{a.label}</span>
              <span className="kbd">{a.kbd}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
