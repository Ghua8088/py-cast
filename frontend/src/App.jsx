import { useState, useEffect, useRef } from 'react'
import pytron from 'pytron-client'
import { Star, Search, Plus, Timer, Bell } from 'lucide-react'
import './App.css'

// Modular Components
import SearchScreen from './components/SearchScreen'
import SettingsView from './components/SettingsView'
import ScratchpadScreen from './components/ScratchpadScreen'
import PythonLabScreen from './components/PythonLabScreen'
import ActionMenu from './components/ActionMenu'

function App() {
  const [view, setView] = useState('search') // 'search' | 'settings' | 'scratchpad'
  const [themeColor, setThemeColor] = useState('#5e5ce6')
  const [zenMode, setZenMode] = useState(false)
  const [hideFooter, setHideFooter] = useState(false) // Deprecated, matching zenMode now for compatibility
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [selectedIndex, setSelectedIndex] = useState(-1)
  // eslint-disable-next-line no-unused-vars
  const [mouseActive, setMouseActive] = useState(false)
  const [showActionMenu, setShowActionMenu] = useState(false)
  const [scratchContent, setScratchContent] = useState('')
  const [activeTimer, setActiveTimer] = useState(null) // { remaining: seconds, total: seconds }
  const [isResizing, setIsResizing] = useState(false)
  const timerRef = useRef(null)

  // Single source of truth for the event listeners to prevent stale closures
  // We update this SYNCHRONOUSLY during render to avoid useEffect race conditions
  const stateRef = useRef({ results, selectedIndex, query, view, showActionMenu, isTransitioning: false });
  const lastExecTime = useRef(0);

  stateRef.current = {
    results,
    selectedIndex,
    query,
    view,
    showActionMenu,
    isTransitioning: stateRef.current.isTransitioning
  };

  const interactionLock = useRef(false)
  const execLock = useRef(false)
  const resolving = useRef(new Set())
  const lastPos = useRef({ x: 0, y: 0 })

  // Persistent Theme Sync
  // Persistent Theme & Settings Sync
  const syncSettings = async () => {
    try {
      const s = await pytron.get_settings();
      if (!s) return;

      // Apply Theme
      if (s.theme_color) {
        let color = s.theme_color;
        if (color === 'adaptive') {
          try {
            const t = await pytron.get_adaptive_theme();
            if (t?.accent) color = t.accent;
          } catch (e) {
            console.warn("Sync: Adaptive theme failed", e);
            color = "#3b82f6";
          }
        }

        if (color && color !== 'adaptive') {
          setThemeColor(color);
          document.documentElement.style.setProperty('--accent', color);
          document.documentElement.style.setProperty('--accent-glow', color + '59');
        }
      }

      // Apply Zen Mode & Footer visibility
      if (typeof s.hide_footer !== 'undefined') {
        setZenMode(!!s.hide_footer);
        setHideFooter(!!s.hide_footer);
      }
    } catch (err) {
      console.error("Sync failed", err);
    }
  };

  useEffect(() => {
    syncSettings();
    if (view === 'scratchpad') {
      pytron.get_scratchpad().then(setScratchContent)
    }
  }, [view]);

  useEffect(() => {
    const handleSettingsUpdate = () => syncSettings();
    window.addEventListener('settings_updated', handleSettingsUpdate)

    pytron.on('pytron:theme_updated', (t) => {
      if (t?.accent) {
        setThemeColor(t.accent);
        document.documentElement.style.setProperty('--accent', t.accent);
        document.documentElement.style.setProperty('--accent-glow', t.accent + '59');
      }
    });

    pytron.on('show_view', (v) => {
      setView(v)
      syncSettings();
      pytron.show()
    })

    return () => {
      window.removeEventListener('settings_updated', handleSettingsUpdate)
      clearInterval(timerRef.current)
    }
  }, [])

  useEffect(() => {
    if (activeTimer) {
      timerRef.current = setInterval(() => {
        setActiveTimer(prev => {
          if (!prev) return null;
          if (prev.remaining <= 1) {
            clearInterval(timerRef.current);
            pytron.send_notification("Timer Finished", "Your countdown is complete!");
            return null;
          }
          return { ...prev, remaining: prev.remaining - 1 };
        });
      }, 1000);
    }
    return () => clearInterval(timerRef.current);
  }, [activeTimer === null]); // Re-start interval only when status changes 

  const lastHeight = useRef(450);
  useEffect(() => {
    const isSearch = view === 'search';
    const isZenState = zenMode && query.trim().length === 0;

    let targetHeight = 450;
    if (view === 'settings' || view === 'scratchpad' || view === 'python_lab') {
      targetHeight = 550;
    } else if (isSearch && isZenState) {
      targetHeight = 62;
    }

    // ONLY call IPC if the height actually changed to prevent jitter
    if (targetHeight !== lastHeight.current) {
      const isExpanding = targetHeight > lastHeight.current;
      lastHeight.current = targetHeight;

      if (isExpanding) setIsResizing(true);

      const timer = setTimeout(() => {
        pytron.set_window_size(750, targetHeight);
        setTimeout(() => setIsResizing(false), 50);
      }, 15);
      return () => clearTimeout(timer);
    }
  }, [view, query.trim().length === 0, zenMode]);

  // SYNCHRONOUS RENDER-TIME CHECK (The Anti-Flicker Guard)
  const isSearch = view === 'search';
  const isZenState = zenMode && query.trim().length === 0;
  let targetHeightRender = 450;
  if (view === 'settings' || view === 'scratchpad' || view === 'python_lab') {
    targetHeightRender = 550;
  } else if (isSearch && isZenState) {
    targetHeightRender = 62;
  }
  const effectivelyResizing = isResizing || (targetHeightRender !== lastHeight.current);

  const saveScratch = (val) => {
    setScratchContent(val);
    pytron.save_scratchpad(val);
  };

  useEffect(() => {
    // Lazy Icon Resolution
    const activeItem = results[selectedIndex];
    if (activeItem?.resolve_path && !resolving.current.has(activeItem.id)) {
      resolving.current.add(activeItem.id);
      pytron.resolve_icon(activeItem.resolve_path).then(newUrl => {
        setResults(prev => prev.map(item =>
          item.id === activeItem.id ? { ...item, icon: newUrl || item.icon, is_img: !!newUrl, resolve_path: null } : item
        ));
      });
    }
  }, [selectedIndex, results]);

  useEffect(() => {
    const handleMouseMove = (e) => {
      const dx = Math.abs(e.clientX - lastPos.current.x)
      const dy = Math.abs(e.clientY - lastPos.current.y)
      if (dx > 10 || dy > 10) {
        interactionLock.current = false;
        setMouseActive(true);
      }
      lastPos.current = { x: e.clientX, y: e.clientY }
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  useEffect(() => {
    const handleBlur = () => {
      if (stateRef.current.view === 'search') pytron.hide();
    };
    window.addEventListener('blur', handleBlur);
    return () => window.removeEventListener('blur', handleBlur);
  }, []);

  // (System stats moved to standalone component in SearchScreen)

  const [refreshSeq, setRefreshSeq] = useState(0);
  const onWfPrompt = () => {
    pytron.add_workflow().then(res => {
      if (res.success) {
        pytron.send_notification("Workflow Added", `Imported ${res.name} successfully`);
        setRefreshSeq(p => p + 1);
      } else if (res.error !== "No file selected") {
        pytron.send_notification("Error", res.error || "Failed to add workflow");
      }
    });
  };

  useEffect(() => {
    const onRefresh = () => setRefreshSeq(p => p + 1);

    window.addEventListener('pytron:refresh', onRefresh);
    window.addEventListener('pytron:create_workflow_prompt', onWfPrompt);
    window.onWfPrompt = onWfPrompt; // Expose for other components
    return () => {
      window.removeEventListener('pytron:refresh', onRefresh);
      window.removeEventListener('pytron:create_workflow_prompt', onWfPrompt);
    };
  }, []);

  useEffect(() => {
    if (view !== 'search') return;
    let ignored = false;

    const isExplicitPath = (q) => {
      const c = q.trim();
      return c.startsWith('t:') || c.startsWith('@') || (c.length >= 2 && c[1] === ':') || c.startsWith('/') || c.startsWith('\\');
    };

    const fetchResults = async () => {
      try {
        const data = await pytron.search_items(query)
        if (!ignored) {
          setResults(data)
          if (query.trim() === '') {
            setSelectedIndex(-1);
          } else {
            const isPath = isExplicitPath(query);
            setSelectedIndex(prev => {
              // For paths, ALWAYS snap to the first result to enable instant Enter/Tab
              if (isPath) return 0;
              // For normal search, keep current selection if valid
              if (prev >= 0 && prev < data.length) return prev;
              return data.length > 0 ? 0 : -1;
            });
          }
          setMouseActive(false)
        }
      } catch (e) {
        console.error("Search failed", e)
      }
    }

    // Snappier response for path navigation (like a terminal)
    const delay = isExplicitPath(query) ? 30 : 150;
    const timer = setTimeout(fetchResults, delay);

    return () => {
      ignored = true;
      clearTimeout(timer)
    }
  }, [query, view, refreshSeq])

  const executeItem = (item) => {
    const now = Date.now();
    if (now - lastExecTime.current < 400) return; // Faster response
    if (execLock.current || !item || stateRef.current.isTransitioning) return;

    lastExecTime.current = now;
    execLock.current = true;

    // Quick UI feedback
    const currentQuery = query;

    if (item.action === 'settings') {
      setView('settings');
      setShowActionMenu(false);
      setQuery('');
    } else if (item.action === 'open_scratch') {
      setView('scratchpad');
      setShowActionMenu(false);
      setQuery('');
    } else if (item.action === 'open_lab') {
      setView('python_lab');
      setShowActionMenu(false);
      setQuery('');
    } else if (item.type === 'term_autofill') {
      setQuery(item.new_query);
      execLock.current = false; // Reset lock immediately for typing
      return;
    } else if (item.action === 'start_timer') {
      setActiveTimer({ total: item.seconds, remaining: item.seconds });
      setQuery('');
      pytron.send_notification("Timer Started", `Countdown for ${Math.floor(item.seconds / 60)}m started.`);
      pytron.hide();
    } else {
      pytron.run_item(item, currentQuery);
      // Don't clear query for search commands that might keep window open
      if (!item.keep_open) setQuery('');
    }

    setTimeout(() => {
      execLock.current = false;
    }, 400);
  };

  useEffect(() => {
    if (view === 'search') return;
    const handlePopKeys = (e) => {
      if (e.key === 'Escape') setView('search');
    };
    window.addEventListener('keydown', handlePopKeys);
    return () => window.removeEventListener('keydown', handlePopKeys);
  }, [view]);

  const togglePin = (id) => {
    pytron.toggle_pin(id).then(() => {
      pytron.search_items(stateRef.current.query).then(setResults)
    })
  }

  useEffect(() => {
    if (view !== 'search' || showActionMenu) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (stateRef.current.query) {
          setQuery('');
          e.stopPropagation();
          e.preventDefault();
        } else {
          pytron.hide();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [view, showActionMenu])

  return (
    <div className={`ray-container ${effectivelyResizing ? 'is-resizing' : ''}`} style={{ '--accent': themeColor }}>
      {view === 'search' && (
        <SearchScreen
          query={query} setQuery={setQuery}
          results={results} setResults={setResults}
          selectedIndex={selectedIndex} setSelectedIndex={setSelectedIndex}
          executeItem={executeItem}
          setShowActionMenu={setShowActionMenu}
          togglePin={togglePin}
          zenMode={zenMode}
          openSettings={() => setView('settings')}
          isResizing={effectivelyResizing}
        />
      )}

      {view === 'settings' && <SettingsView onClose={() => setView('search')} isResizing={effectivelyResizing} />}

      {view === 'scratchpad' && (
        <ScratchpadScreen
          content={scratchContent}
          onSave={saveScratch}
          onBack={() => setView('search')}
        />
      )}

      {view === 'python_lab' && (
        <PythonLabScreen
          onBack={() => setView('search')}
        />
      )}

      {showActionMenu && (
        <ActionMenu
          item={results[selectedIndex]}
          query={query}
          onClose={() => setShowActionMenu(false)}
          setView={setView}
          setQuery={setQuery}
          executeItem={executeItem}
        />
      )}

      {/* Search Bar handles footer now for Zen mode alignment */}
      {activeTimer && (
        <div
          className="timer-overlay"
          onClick={() => setActiveTimer(null)}
          title="Click to cancel timer"
        >
          <Timer size={14} className="timer-spin" />
          <span>{Math.floor(activeTimer.remaining / 60)}:{(activeTimer.remaining % 60).toString().padStart(2, '0')}</span>
          <div
            className="timer-progress"
            style={{ width: `${(activeTimer.remaining / activeTimer.total) * 100}%` }}
          />
        </div>
      )}
    </div>
  )
}

export default App
