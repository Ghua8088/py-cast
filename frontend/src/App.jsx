import { useState, useEffect, useRef } from 'react'
import pytron from 'pytron-client'
import { Star, Search, Plus } from 'lucide-react'
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
  const [hideFooter, setHideFooter] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [sysInfo, setSysInfo] = useState({ cpu: 0, mem: 0 })
  // eslint-disable-next-line no-unused-vars
  const [mouseActive, setMouseActive] = useState(false)
  const [showActionMenu, setShowActionMenu] = useState(false)
  const [scratchContent, setScratchContent] = useState('')

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

  useEffect(() => {
    pytron.get_settings().then(s => {
      if (s?.theme_color) setThemeColor(s.theme_color)
      setHideFooter(!!s?.hide_footer)
    })

    if (view === 'scratchpad') {
      pytron.get_scratchpad().then(setScratchContent)
    }
  }, [view]);

  useEffect(() => {
    const handleSettingsUpdate = () => {
      pytron.get_settings().then(s => {
        if (s?.theme_color) setThemeColor(s.theme_color)
        setHideFooter(!!s?.hide_footer)
      })
    }
    window.addEventListener('settings_updated', handleSettingsUpdate)

    pytron.on('show_view', (v) => {
      setView(v)
      pytron.show()
    })

    return () => {
      window.removeEventListener('settings_updated', handleSettingsUpdate)
    }
  }, [])

  useEffect(() => {
    const isSearch = view === 'search';
    const isZen = hideFooter && query.trim().length === 0;
    const isEmpty = query.trim().length === 0;

    let targetHeight = 450;
    if (view === 'settings' || view === 'scratchpad') {
      targetHeight = 550;
    } else if (isSearch && isZen) {
      targetHeight = 60;
    }

    pytron.set_window_size(750, targetHeight);
  }, [view, query, hideFooter, results.length]);

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
      pytron.hide();
    };
    window.addEventListener('blur', handleBlur);
    return () => window.removeEventListener('blur', handleBlur);
  }, []);

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
  const onWfPrompt = () => {
    pytron.add_workflow().then(res => {
      if (res.success) {
        pytron.notify("Workflow Added", `Imported ${res.name} successfully`, "success");
        setRefreshSeq(p => p + 1);
      } else if (res.error !== "No file selected") {
        pytron.notify("Error", res.error || "Failed to add workflow", "error");
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

    const fetchResults = async () => {
      try {
        const data = await pytron.search_items(query)
        if (!ignored) {
          setResults(data)
          if (query.trim() === '') {
            setSelectedIndex(-1);
          } else {
            // Keep selection if it exists and is valid
            setSelectedIndex(prev => {
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
    const timer = setTimeout(fetchResults, 10); // Ultra-fast response
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
      setQuery('');
    } else if (item.action === 'open_scratch') {
      setView('scratchpad');
      setQuery('');
    } else if (item.action === 'open_lab') {
      setView('python_lab');
      setQuery('');
    } else if (item.type === 'term_autofill') {
      setQuery(item.new_query);
      execLock.current = false; // Reset lock immediately for typing
      return;
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
        pytron.hide()
      }
    };
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [view, showActionMenu])

  return (
    <div className="ray-container" style={{ '--accent': themeColor }}>
      {view === 'search' && (
        <SearchScreen
          query={query} setQuery={setQuery}
          results={results} setResults={setResults}
          selectedIndex={selectedIndex} setSelectedIndex={setSelectedIndex}
          executeItem={executeItem} sysInfo={sysInfo}
          setShowActionMenu={setShowActionMenu}
          togglePin={togglePin}
          hideFooter={hideFooter}
          openSettings={() => setView('settings')}
        />
      )}

      {view === 'settings' && <SettingsView onClose={() => setView('search')} />}

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

      {((!hideFooter && view === 'search') || (hideFooter && query.trim().length > 0)) && (
        <div className="ray-footer">
          <div className="footer-left">
            <span className="brand">Bite</span>
          </div>
          <div className="ray-footer-right">
            {results[selectedIndex]?.url && <div className="hint"><span className="kbd">↵</span> Open Browser</div>}
            {results[selectedIndex]?.path && <div className="hint"><span className="kbd">↵</span> Open File</div>}
            {results[selectedIndex]?.action === 'calc_res' && <div className="hint"><span className="kbd">↵</span> Copy Result</div>}
            <div className="action-button-primary" onClick={() => setView('settings')}>
              Settings
            </div>
            <div className="action-button-primary" onClick={() => setShowActionMenu(true)}>
              Actions
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
