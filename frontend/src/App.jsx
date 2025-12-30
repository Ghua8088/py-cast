import { useState, useEffect, useRef } from 'react'
import pytron from 'pytron-client'
import {
  Calculator, FileText, Terminal, Scissors, Search,
  Youtube, Github, Lock, Moon, Trash2, HelpCircle,
  Code, Globe, Gamepad2, File, Folder, Clipboard,
  Smartphone, Monitor, Hash, Star, LayoutGrid,
  Settings as SettingsIcon, Plus, X, ArrowLeft, Link as LinkIcon, Download, RefreshCw
} from 'lucide-react'
import './App.css'

// Icon mapping helper
const getIcon = (item) => {
  // If it's a native base64 image, render nothing here (handled in JSX)
  if (item.is_img) return null;

  // keyword based mapping for lucide
  const name = item.name.toLowerCase();
  const cat = item.cat.toLowerCase();

  if (item.id === 'calc') return <Calculator size={20} />;
  if (item.id === 'note') return <FileText size={20} />;
  if (item.id === 'term') return <Terminal size={20} />;
  if (item.id === 'snip') return <Scissors size={20} />;
  if (item.id === 'google') return <Globe size={20} />;
  if (item.id === 'yt') return <Youtube size={20} />;
  if (item.id === 'gh') return <Github size={20} />;
  if (item.id === 'lock') return <Lock size={20} />;
  if (item.id === 'sleep') return <Moon size={20} />;
  if (item.id === 'clean') return <Trash2 size={20} />;
  if (item.id === 'help') return <HelpCircle size={20} />;
  if (item.id === 'settings') return <SettingsIcon size={20} />;
  if (item.cat === 'Calc') return <Hash size={20} />;
  if (item.cat === 'Clipboard') return <Clipboard size={20} />;
  if (item.cat === 'Custom') return <LinkIcon size={20} />;

  // Category fallbacks
  if (cat === 'files') {
    return item.icon.includes('folder') || item.icon === '📁' ? <Folder size={20} /> : <File size={20} />;
  }

  // Generic App Fallbacks if no native icon found
  if (name.includes('code')) return <Code size={20} />;
  if (name.includes('game')) return <Gamepad2 size={20} />;
  return <LayoutGrid size={20} />;
}

function SettingsView({ onClose }) {
  const [shortcuts, setShortcuts] = useState([])
  const [form, setForm] = useState({ keyword: '', name: '', url: '' })

  useEffect(() => {
    pytron.get_user_shortcuts().then(setShortcuts)
  }, [])

  const handleAdd = async () => {
    if (!form.keyword || !form.url) return;
    const newShortcuts = await pytron.add_shortcut(form.keyword, form.name || form.keyword, form.url)
    setShortcuts(newShortcuts)
    setForm({ keyword: '', name: '', url: '' })
  }

  const handleDelete = async (id) => {
    const newShortcuts = await pytron.remove_shortcut(id)
    setShortcuts(newShortcuts)
  }

  return (
    <div className="settings-view">
      <div className="settings-header">
        <div className="back-btn" onClick={onClose}><ArrowLeft size={18} /></div>
        <h3>Manage Search Shortcuts</h3>
      </div>

      <div className="add-shortcut-form">
        <input
          placeholder="Keyword (e.g. 'yt')"
          value={form.keyword}
          onChange={e => setForm({ ...form, keyword: e.target.value })}
          className="st-input"
        />
        <input
          placeholder="Name"
          value={form.name}
          onChange={e => setForm({ ...form, name: e.target.value })}
          className="st-input"
        />
        <input
          placeholder="URL (e.g. youtube.com/results?q=)"
          value={form.url}
          onChange={e => setForm({ ...form, url: e.target.value })}
          className="st-input full"
        />
        <button className="st-btn" onClick={handleAdd}>
          <Plus size={14} /> Add Shortcut
        </button>
      </div>

      <div className="shortcuts-list">
        {shortcuts.map(s => (
          <div className="shortcut-item" key={s.id}>
            <div className="sc-icon"><LinkIcon size={14} /></div>
            <div className="sc-info">
              <span className="sc-key">{s.id}</span>
              <span className="sc-url">{s.url}</span>
            </div>
            <div className="sc-del" onClick={() => handleDelete(s.id)}>
              <Trash2 size={14} />
            </div>
          </div>
        ))}
        {shortcuts.length === 0 && <div className="empty-st">No custom shortcuts added.</div>}
      </div>

      <UpdaterSection />
    </div>
  )
}

function UpdaterSection() {
  const [status, setStatus] = useState('idle'); // idle, checking, available, updating
  const [updateInfo, setUpdateInfo] = useState(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const onProgress = (e) => setProgress(e.detail);
    window.addEventListener('pytron:update_progress', onProgress);
    return () => window.removeEventListener('pytron:update_progress', onProgress);
  }, []);

  const check = async () => {
    setStatus('checking');
    try {
      const info = await pytron.check_update();
      if (info) {
        setUpdateInfo(info);
        setStatus('available');
      } else {
        setStatus('idle');
        pytron.notify('Up to Date', 'You are running the latest version.', 'success');
      }
    } catch (e) {
      setStatus('idle');
      console.error(e);
      pytron.notify('Update Check Failed', 'Check internet connection.', 'error');
    }
  };

  const install = async () => {
    if (!updateInfo) return;
    setStatus('updating');
    await pytron.install_update(updateInfo);
  };

  return (
    <div className="updater-section">
      {status === 'idle' && (
        <button className="st-btn secondary" onClick={check} style={{ width: '100%', marginTop: '10px' }}>
          <RefreshCw size={14} /> Check for Updates
        </button>
      )}

      {status === 'checking' && (
        <div className="update-status"><RefreshCw size={14} className="spin" /> Checking...</div>
      )}

      {status === 'available' && (
        <div className="update-card">
          <div className="up-info">
            <span className="up-ver">Version {updateInfo.version} Available</span>
            <span className="up-notes">{updateInfo.notes}</span>
          </div>
          <button className="st-btn primary" onClick={install}>
            <Download size={14} /> Update Now
          </button>
        </div>
      )}

      {status === 'updating' && (
        <div className="update-progress">
          <span>Downloading Update... {progress}%</span>
          <div className="prog-bar"><div className="prog-fill" style={{ width: `${progress}%` }}></div></div>
        </div>
      )}
    </div>
  )
}

function App() {
  const [view, setView] = useState('search') // 'search' | 'settings'
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [sysInfo, setSysInfo] = useState({ cpu: 0, mem: 0 })
  const inputRef = useRef(null)

  useEffect(() => {
    pytron.waitForBackend().then(() => {
      setSysInfo(pytron.state.sys_info || { cpu: 0, mem: 0 })
    })

    const handleState = (e) => {
      if (e.detail.sys_info) setSysInfo(e.detail.sys_info)
    }
    window.addEventListener('pytron:state', handleState)
    return () => window.removeEventListener('pytron:state', handleState)
  }, [])

  const [refreshSeq, setRefreshSeq] = useState(0);

  useEffect(() => {
    const onRefresh = () => setRefreshSeq(p => p + 1);
    window.addEventListener('pytron:refresh', onRefresh);
    return () => window.removeEventListener('pytron:refresh', onRefresh);
  }, []);

  useEffect(() => {
    if (view !== 'search') return;
    let ignored = false;

    const fetchResults = async () => {
      try {
        const data = await pytron.search_items(query)
        if (!ignored) {
          setResults(data)
          setSelectedIndex(0)
        }
      } catch (e) {
        console.error("Search failed", e)
      }
    }
    const timer = setTimeout(fetchResults, 40)
    return () => {
      ignored = true;
      clearTimeout(timer)
    }
  }, [query, view, refreshSeq])

  useEffect(() => {
    if (view === 'search' && inputRef.current) inputRef.current.focus()

    const handleKeyDown = (e) => {
      if (view === 'settings') {
        if (e.key === 'Escape') setView('search');
        return;
      }

      if (e.key === 'ArrowDown') {
        setSelectedIndex(prev => Math.min(prev + 1, results.length - 1))
        e.preventDefault()
      } else if (e.key === 'ArrowUp') {
        setSelectedIndex(prev => Math.max(prev - 1, 0))
        e.preventDefault()
      } else if (e.key === 'Enter') {
        if (results[selectedIndex]) {
          const item = results[selectedIndex];
          if (item.action === 'settings') {
            setView('settings');
            setQuery('');
          } else {
            pytron.run_item(item, query)
            setQuery('')
          }
        }
      } else if (e.key === 'Tab') {
        if (results[selectedIndex]?.id) {
          pytron.toggle_pin(results[selectedIndex].id).then(() => {
            pytron.search_items(query).then(setResults)
          })
          e.preventDefault()
        }
      } else if (e.key === 'Escape') {
        pytron.hide()
      }
    };
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [results, selectedIndex, query, view])

  const renderHeader = (index) => {
    const item = results[index]
    const prev = results[index - 1]

    if (item.pinned) {
      return index === 0 ? <div className="ray-cat-header">📌 Pinned Favorites</div> : null
    }

    if (index === 0 || (prev && prev.cat !== item.cat) || (prev && prev.pinned)) {
      return <div className="ray-cat-header">{item.cat}</div>
    }
    return null
  }

  if (view === 'settings') {
    return (
      <div className="ray-container">
        <SettingsView onClose={() => setView('search')} />
      </div>
    )
  }

  return (
    <div className="ray-container">
      <div className="ray-search-bar">
        <div className="ray-search-icon"><Search size={22} color="var(--accent)" /></div>
        <input
          ref={inputRef}
          type="text"
          placeholder="Search apps, files, or evaluate math..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="ray-stats">
          <div className="stat-pill"><span className="stat-label">CPU</span><span className="stat-value">{sysInfo.cpu}%</span></div>
          <div className="stat-pill"><span className="stat-label">RAM</span><span className="stat-value">{sysInfo.mem}%</span></div>
        </div>
      </div>

      <div className="ray-results">
        {results.map((item, index) => (
          <div key={item.id || index}>
            {renderHeader(index)}
            <div
              className={`ray-item ${index === selectedIndex ? 'active' : ''} ${item.pinned ? 'is-pinned' : ''}`}
              onClick={() => {
                if (item.action === 'settings') {
                  setView('settings');
                  setQuery('');
                } else {
                  pytron.run_item(item, query);
                }
              }}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <div className="ray-item-icon">
                {item.is_img ? (
                  <img src={item.icon} alt="" style={{ width: '28px', height: '28px', objectFit: 'contain' }} />
                ) : (
                  getIcon(item)
                )}
              </div>
              <div className="ray-item-info">
                <span className="ray-item-name">
                  {item.name}
                  {item.pinned && <Star size={12} fill="#FFD700" stroke="#FFD700" className="pin-star" />}
                </span>
                <span className="ray-item-desc">{item.desc}</span>
              </div>

              {index === selectedIndex && (
                <div className="ray-action-bar">
                  <div className="ray-action-item"><span className="kbd">TAB</span> {item.pinned ? 'UNPIN' : 'PIN'}</div>
                  <div className="ray-action-item pulse"><span className="kbd">↵</span> OPEN</div>
                </div>
              )}
            </div>
          </div>
        ))}

        {results.length === 0 && query && (
          <div className="ray-no-results">
            <div className="no-res-icon"><Search size={48} strokeWidth={1} /></div>
            <p className="dim">No matches for "{query}"</p>
          </div>
        )}
      </div>

      <div className="ray-footer">
        <div className="footer-left">
          <span className="brand">Bite</span>
          <span className="sep">|</span>
          <span>v0.3.0 Native</span>
        </div>
        <div className="ray-footer-right">
          <div className="hint"><span className="kbd">Alt + B</span> to Toggle</div>
        </div>
      </div>
    </div>
  )
}

export default App
