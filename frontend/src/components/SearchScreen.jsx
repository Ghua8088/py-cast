import { useRef, useEffect } from 'react'
import { Search, Star, Copy, CornerDownLeft } from 'lucide-react'
import { ItemIcon } from './Icons'
import DetailsPanel from './DetailsPanel'

export default function SearchScreen({
  query, setQuery, results, selectedIndex, setSelectedIndex,
  executeItem, sysInfo, setShowActionMenu, togglePin, hideFooter
}) {
  const inputRef = useRef(null)
  const listRef = useRef(null)

  useEffect(() => {
    if (inputRef.current) inputRef.current.focus()
  }, [])

  useEffect(() => {
    const activeItem = listRef.current?.querySelector('.ray-item.active');
    if (activeItem) {
      activeItem.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }, [selectedIndex]);

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
      e.preventDefault();
    } else if (e.key === 'ArrowUp') {
      setSelectedIndex(prev => Math.max(prev - 1, 0));
      e.preventDefault();
    } else if (e.key === 'Enter') {
      if (selectedIndex >= 0 && results[selectedIndex]) {
        executeItem(results[selectedIndex]);
      }
      e.preventDefault();
      e.stopPropagation();
    } else if (e.key === 'Tab') {
      if (selectedIndex >= 0 && results[selectedIndex]) {
        const item = results[selectedIndex];
        if (item.type === 'term_autofill') {
          setQuery(item.new_query);
        } else if (item.path && (item.type === 'file' || item.is_dir)) {
          const isWin = item.path.includes('\\');
          const sep = isWin ? '\\' : '/';
          const newQuery = item.is_dir ? item.path + sep : item.path;
          setQuery(newQuery);
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
    } else if (results.length === 0 && query.trim() !== '') {
      if (e.key.toLowerCase() === 'g') {
        executeItem({ id: 'g_search', type: 'web', url: `https://google.com/search?q=${encodeURIComponent(query)}` });
        e.preventDefault();
      } else if (e.key.toLowerCase() === 'h') {
        executeItem({ id: 'gh_search', type: 'web', url: `https://github.com/search?q=${encodeURIComponent(query)}` });
        e.preventDefault();
      }
    }
  };

  const renderHeader = (index) => {
    const item = results[index]
    const prev = results[index - 1]
    if (item.pinned) return index === 0 ? <div className="ray-cat-header">📌 Pinned Favorites</div> : null
    if (index === 0 || (prev && prev.cat !== item.cat) || (prev && prev.pinned)) return <div className="ray-cat-header">{item.cat}</div>
    return null
  }

  return (
    <>
      <div className="ray-search-bar">
        <div className="ray-search-icon"><Search className="search-icon" size={22} /></div>
        <input
          ref={inputRef}
          type="text"
          placeholder="Search apps, files, or evaluate math..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <div className="ray-stats">
          {sysInfo.battery !== undefined && sysInfo.battery !== null && (
            <div className="stat-pill"><span className="stat-label">BAT</span><span className="stat-value">{sysInfo.battery}%</span></div>
          )}
          <div className="stat-pill"><span className="stat-label">CPU</span><span className="stat-value">{sysInfo.cpu}%</span></div>
          <div className="stat-pill"><span className="stat-label">RAM</span><span className="stat-value">{sysInfo.mem}%</span></div>
          {sysInfo.time && (
            <div className="stat-pill"><span className="stat-label">TIME</span><span className="stat-value">{sysInfo.time}</span></div>
          )}
        </div>
      </div>

      {(!hideFooter || query.trim().length > 0) && (
        <div className="ray-main">
          <div className="ray-results-container">
            <div className="ray-results" ref={listRef}>
              {results.map((item, index) => (
                <div key={item.id || index}>
                  {renderHeader(index)}
                  <div
                    className={`ray-item ${index === selectedIndex ? 'active' : ''} ${item.pinned ? 'is-pinned' : ''} ${index === 0 && query ? 'is-top-hit' : ''}`}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      executeItem(item);
                    }}
                    onMouseEnter={() => setSelectedIndex(index)}
                  >
                    <div className="ray-item-icon"><ItemIcon item={item} /></div>
                    <div className="ray-item-info">
                      <span className="ray-item-name">
                        {item.name}
                        {item.pinned && <Star size={12} fill="#FFD700" stroke="#FFD700" className="pin-star" />}
                        {index === 0 && query && <span className="top-hit-badge">Top Hit</span>}
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
                  <div className="no-res-icon"><Search size={48} strokeWidth={1} /></div>
                  <p className="dim">No matches for "{query}"</p>
                  <div className="fallback-suggestions">
                    <div className="fallback-item" onClick={() => executeItem({ id: 'g_search', type: 'web', url: `https://google.com/search?q=${encodeURIComponent(query)}` })}>
                      <span className="kbd">G</span> Search Google
                    </div>
                    <div className="fallback-item" onClick={() => executeItem({ id: 'gh_search', type: 'web', url: `https://github.com/search?q=${encodeURIComponent(query)}` })}>
                      <span className="kbd">H</span> Search GitHub
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
          {results[selectedIndex] && <DetailsPanel item={results[selectedIndex]} onExecute={executeItem} />}
        </div>
      )}
    </>
  )
}
