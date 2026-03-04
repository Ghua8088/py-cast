import { useRef, useState, useEffect } from 'react'
import { Search, Star, Copy, CornerDownLeft, Settings, Globe, Github } from 'lucide-react'
import { ItemIcon } from './Icons'
import DetailsPanel from './DetailsPanel'
import pytron from 'pytron-client'

function SysStats() {
  const [sysInfo, setSysInfo] = useState({ cpu: 0, mem: 0 });
  useEffect(() => {
    pytron.waitForBackend().then(() => {
      setSysInfo(pytron.state.sys_info || { cpu: 0, mem: 0 });
    });
    const handleState = (e) => {
      if (e.detail.sys_info) setSysInfo(e.detail.sys_info);
    };
    window.addEventListener('pytron:state', handleState);
    return () => window.removeEventListener('pytron:state', handleState);
  }, []);

  return (
    <div className="ray-stats-container">
      {sysInfo.battery !== undefined && sysInfo.battery !== null && (
        <div className="stat-pill"><span className="stat-label">BAT</span><span className="stat-value">{sysInfo.battery}%</span></div>
      )}
      <div className="stat-pill"><span className="stat-label">CPU</span><span className="stat-value">{sysInfo.cpu}%</span></div>
      <div className="stat-pill"><span className="stat-label">RAM</span><span className="stat-value">{sysInfo.mem}%</span></div>
      {sysInfo.time && (
        <div className="stat-pill"><span className="stat-label">TIME</span><span className="stat-value">{sysInfo.time}</span></div>
      )}
    </div>
  );
}

export default function SearchScreen({
  query, setQuery, results, selectedIndex, setSelectedIndex,
  executeItem, setShowActionMenu, togglePin, zenMode, openSettings, isResizing
}) {
  const inputRef = useRef(null)
  const listRef = useRef(null)

  useEffect(() => {
    if (inputRef.current) inputRef.current.focus()
  }, [])

  const lastInteraction = useRef('keyboard')

  useEffect(() => {
    if (lastInteraction.current === 'keyboard' && selectedIndex >= 0) {
      const activeItem = listRef.current?.querySelector('.ray-item.active');
      if (activeItem) {
        activeItem.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    }
  }, [selectedIndex]);

  const handleKeyDown = (e) => {
    lastInteraction.current = 'keyboard';
    if (e.key === 'ArrowDown') {
      setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
      e.preventDefault();
    } else if (e.key === 'ArrowUp') {
      setSelectedIndex(prev => Math.max(prev - 1, 0));
      e.preventDefault();
    } else if (e.key === 'Enter') {
      const isPathLike = (q) => {
        const c = q.trim();
        return c.startsWith('t:') || c.startsWith('@') || (c.length >= 2 && c[1] === ':') || c.startsWith('/') || c.startsWith('\\');
      };

      let targetItem = results[selectedIndex];
      if (!targetItem && results.length > 0 && (query.startsWith('t:') || isPathLike(query))) {
        targetItem = results[0];
      }

      if (targetItem) {
        executeItem(targetItem);
      } else if (query.startsWith('t:')) {
        // Fallback for terminal: execute the direct command if no item selected
        executeItem({ id: 'run_term', cmd: query.substring(2).trim(), action: 'run_term_cmd' });
      }
      e.preventDefault();
      e.stopPropagation();
    } else if (e.key === 'Tab') {
      const isPathLike = (q) => {
        const c = q.trim();
        return c.startsWith('t:') || c.startsWith('@') || (c.length >= 2 && c[1] === ':') || c.startsWith('/') || c.startsWith('\\');
      };

      let targetIndex = selectedIndex;
      // If no item is selected but it's a path or terminal query, auto-target the first result
      if (targetIndex < 0 && results.length > 0 && isPathLike(query)) {
        targetIndex = 0;
      }

      if (targetIndex >= 0 && results[targetIndex]) {
        const item = results[targetIndex];
        if (item.type === 'term_autofill' || item.action === 'run_term_cmd') {
          setQuery(item.new_query || `t: ${item.path || item.cmd}`);
          setSelectedIndex(-1);
        } else if (item.path && (item.type === 'file' || item.is_dir)) {
          const newPath = item.path + (item.is_dir ? '\\' : '');
          const finalQuery = query.startsWith('t:') ? `t: ${newPath}` : newPath;
          setQuery(finalQuery);
          setSelectedIndex(-1);
        } else {
          togglePin(item.id);
        }
      }
      e.preventDefault();
    } else if (e.key === 'k' && (e.ctrlKey || e.metaKey)) {
      if (selectedIndex >= 0 && results[selectedIndex]) {
        setShowActionMenu(true);
      }
      e.preventDefault();
    } else if (e.key === 'c' && (e.ctrlKey || e.metaKey)) {
      if (selectedIndex >= 0 && results[selectedIndex]) {
        const item = results[selectedIndex];
        if (item.path || item.content) {
          pytron.copy_to_clipboard(item.content || item.path);
          pytron.send_notification("Copied", "Item copied to clipboard");
        }
      }
      e.preventDefault();
    } else if (results.length === 0 && query.trim() !== '') {
      if (e.key.toLowerCase() === 'g' && (e.ctrlKey || e.metaKey)) {
        executeItem({ id: 'g_search', type: 'web', url: `https://google.com/search?q=${encodeURIComponent(query)}` });
        e.preventDefault();
      } else if (e.key.toLowerCase() === 'h' && (e.ctrlKey || e.metaKey)) {
        executeItem({ id: 'gh_search', type: 'web', url: `https://github.com/search?q=${encodeURIComponent(query)}` });
        e.preventDefault();
      }
    }
  };

  const renderHeader = (index) => {
    const item = results[index]
    const prev = results[index - 1]
    if (item.pinned) return index === 0 ? <div className="ray-cat-header" data-cat="Pinned">📌 Pinned Favorites</div> : null
    if (index === 0 || (prev && prev.cat !== item.cat) || (prev && prev.pinned)) return <div className="ray-cat-header" data-cat={item.cat}>{item.cat}</div>
    return null
  }

  const showBody = (!zenMode || query.trim().length > 0) && !isResizing;

  return (
    <>
      <div className="ray-search-bar">
        <div className="ray-search-icon"><Search className="search-icon" size={22} /></div>
        <input
          ref={inputRef}
          className="ray-search-input"
          type="text"
          placeholder="Search or command..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <SysStats />
      </div>

      {showBody && (
        <>
          <div className="ray-main">
            <div className="ray-results-container">
              <div className="ray-results" ref={listRef}>
                {results.map((item, index) => (
                  <div key={item.id || index}>
                    {renderHeader(index)}
                    <div
                      style={{ '--index': index }}
                      className={`ray-item ${index === selectedIndex ? 'active' : ''} ${item.pinned ? 'is-pinned' : ''} ${index === 0 && query ? 'is-top-hit' : ''}`}
                      onMouseDown={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        executeItem(item);
                      }}
                      onMouseEnter={() => {
                        lastInteraction.current = 'mouse';
                        setSelectedIndex(index);
                      }}
                    >
                      <div className="ray-item-icon">
                        {item.preview_color ? (
                          <div style={{ width: 18, height: 18, borderRadius: 4, background: item.preview_color, border: '1px solid rgba(255,255,255,0.2)' }} />
                        ) : (
                          <ItemIcon item={item} />
                        )}
                      </div>
                      <div className="ray-item-info">
                        <span className="ray-item-name">
                          {item.name}
                          {item.pinned && <Star size={12} fill="#FFD700" stroke="#FFD700" className="pin-star" />}
                          {index === 0 && query && !item.learned && <span className="top-hit-badge">Top Hit</span>}
                        </span>
                        <span className="ray-item-desc">{item.desc}</span>
                      </div>
                      {index === selectedIndex && (
                        <div className="ray-action-bar">
                          {(item.path || item.content) && (
                            <div className="ray-action-item">
                              <Copy size={12} style={{ opacity: 0.6 }} />
                              <span className="kbd">CTRL C</span>
                            </div>
                          )}
                          <div className="ray-action-item">
                            <Star size={12} style={{ opacity: 0.6 }} />
                            <span className="kbd">TAB</span>
                          </div>
                          <div className="ray-action-item pulse">
                            <CornerDownLeft size={12} style={{ opacity: 0.6 }} />
                            <span className="kbd">↵</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {results.length === 0 && query && (
                  <div className="ray-no-results">
                    <div className="no-res-icon"><Search size={32} strokeWidth={1.5} /></div>
                    <p className="dim">No results for <span className="query-highlight">"{query}"</span></p>
                    <p className="no-res-sub">Try searching with a global provider instead</p>
                    <div className="fallback-suggestions">
                      <div className="fallback-item" onClick={() => executeItem({ id: 'g_search', type: 'web', url: `https://google.com/search?q=${encodeURIComponent(query)}` })}>
                        <div className="fallback-label">
                          <Globe size={16} />
                          <span>Search Google</span>
                        </div>
                        <span className="kbd">Ctrl+G</span>
                      </div>
                      <div className="fallback-item" onClick={() => executeItem({ id: 'gh_search', type: 'web', url: `https://github.com/search?q=${encodeURIComponent(query)}` })}>
                        <div className="fallback-label">
                          <Github size={16} />
                          <span>Search GitHub</span>
                        </div>
                        <span className="kbd">Ctrl+H</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
            {results[selectedIndex] && <DetailsPanel item={results[selectedIndex]} onExecute={executeItem} />}
          </div>

          <div className="ray-footer">
            <div className="footer-left">
              <span className="brand">Bite</span>
            </div>
            <div className="ray-footer-right">
              {results[selectedIndex]?.url && <div className="hint"><span className="kbd">↵</span> Open Browser</div>}
              {results[selectedIndex]?.path && <div className="hint"><span className="kbd">↵</span> Open File</div>}
              {results[selectedIndex]?.action === 'calc_res' && <div className="hint"><span className="kbd">↵</span> Copy Result</div>}
              <div className="action-button-primary" onClick={openSettings}>
                Settings
              </div>
              <div className="action-button-primary" onClick={() => setShowActionMenu(true)}>
                Actions
              </div>
            </div>
          </div>
        </>
      )}
    </>
  )
}
