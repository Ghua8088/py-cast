import { useState, useEffect } from 'react'
import pytron from 'pytron-client'
import {
  Plus, Trash2, ArrowLeft, Link as LinkIcon, Scissors, RefreshCw,
  Download, Zap, Edit2, FolderOpen, Sliders, Code, Command, Lock,
  Sparkles, Terminal, Info, Globe, Shield, Check
} from 'lucide-react'
import { ItemIcon } from './Icons'
import VaultSection from './VaultSection'
import biteWordmark from '../assets/bite-wordmark.png'
import biteIcon from '../assets/bite-icon.png'

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
        pytron.send_notification('Up to Date', 'You are running the latest version.');
      }
    } catch (e) {
      setStatus('idle');
      console.error(e);
      pytron.send_notification('Update Check Failed', 'Check internet connection.');
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
        <button className="st-btn secondary" onClick={check} style={{ width: '100%', marginTop: '6px' }}>
          <RefreshCw size={14} /> Check for Updates
        </button>
      )}

      {status === 'checking' && (
        <div className="update-status"><RefreshCw size={14} className="spin" /> Checking for updates...</div>
      )}

      {status === 'available' && (
        <div className="update-card">
          <div className="up-info">
            <span className="up-ver">Version {updateInfo.version} Available</span>
            <span className="up-notes">{updateInfo.notes}</span>
          </div>
          <button className="st-btn primary" onClick={install}>
            <Download size={14} /> Install Update
          </button>
        </div>
      )}

      {status === 'updating' && (
        <div className="update-progress-box">
          <div className="prog-label">Downloading Update: {progress}%</div>
          <div className="prog-bar">
            <div className="prog-fill" style={{ width: `${progress}%` }}></div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function SettingsView({ onClose, isResizing, onOpenOnboarding }) {
  const [activeTab, setActiveTab] = useState('general'); // 'general' | 'developer' | 'shortcuts' | 'workflows' | 'about'
  const [shortcuts, setShortcuts] = useState([])
  const [snippets, setSnippets] = useState([])
  const [settings, setSettings] = useState({ theme_color: '#bfa5ff', start_on_boot: false, excluded_folders: [], hide_footer: false })
  const [pathAliases, setPathAliases] = useState({})
  const [projectRoots, setProjectRoots] = useState([])

  // Forms
  const [scForm, setScForm] = useState({ id: '', name: '', url: '', icon: 'globe' })
  const [snipForm, setSnipForm] = useState({ name: '', content: '' })
  const [newAlias, setNewAlias] = useState({ key: '', path: '' })
  const [editingId, setEditingId] = useState(null)

  useEffect(() => {
    pytron.get_settings().then(setSettings);
    const getShortcutsFn = pytron.get_user_shortcuts || pytron.get_shortcuts;
    if (getShortcutsFn) getShortcutsFn().then(setShortcuts);
    const getSnippetsFn = pytron.get_user_snippets || pytron.get_snippets;
    if (getSnippetsFn) getSnippetsFn().then(setSnippets);
    if (pytron.get_path_aliases) pytron.get_path_aliases().then(setPathAliases)
    if (pytron.get_project_roots) pytron.get_project_roots().then(setProjectRoots)
  }, [])

  const updateSetting = async (key, val) => {
    const updated = { ...settings, [key]: val }
    setSettings(updated)
    await pytron.update_settings(updated)
    window.dispatchEvent(new CustomEvent('settings_updated'))
  }

  const handleSave = async () => {
    await pytron.update_settings(settings)
    pytron.send_notification("Settings Saved", "Preferences updated successfully.")
    window.dispatchEvent(new CustomEvent('settings_updated'))
    onClose()
  }

  // Shortcut CRUD
  const handleAddShortcut = async () => {
    if (!scForm.id || !scForm.url) return
    const shortcutPayload = {
      type: 'search',
      cat: 'Custom',
      icon: 'globe',
      ...scForm,
      name: scForm.name || scForm.id
    }
    const updated = editingId
      ? shortcuts.map(s => s.id === editingId ? { ...s, ...shortcutPayload } : s)
      : [...shortcuts, shortcutPayload]
    setShortcuts(updated)
    if (pytron.update_shortcuts) {
      await pytron.update_shortcuts(updated)
    }
    setScForm({ id: '', name: '', url: '', icon: 'globe' })
    setEditingId(null)
  }

  const handleEditShortcut = (s) => {
    setScForm({
      id: s.id || '',
      name: s.name || '',
      url: s.url || s.path || '',
      icon: s.icon || 'globe'
    })
    setEditingId(s.id)
  }

  const handleDeleteShortcut = async (id) => {
    const updated = shortcuts.filter(s => s.id !== id)
    setShortcuts(updated)
    if (pytron.update_shortcuts) {
      await pytron.update_shortcuts(updated)
    }
  }

  // Snippet CRUD
  const handleAddSnippet = async () => {
    if (!snipForm.name || !snipForm.content) return
    const newItem = { id: `snip_${Date.now()}`, ...snipForm }
    const updated = [...snippets, newItem]
    setSnippets(updated)
    if (pytron.update_snippets) {
      await pytron.update_snippets(updated)
    }
    setSnipForm({ name: '', content: '' })
  }

  const handleDeleteSnippet = async (id) => {
    const updated = snippets.filter(s => s.id !== id)
    setSnippets(updated)
    if (pytron.update_snippets) {
      await pytron.update_snippets(updated)
    }
  }

  const handleAddAlias = async () => {
    if (!newAlias.key || !newAlias.path) return;
    const key = newAlias.key.startsWith('@') ? newAlias.key : `@${newAlias.key}`;
    const res = await pytron.add_path_alias(key, newAlias.path);
    setPathAliases(res);
    setNewAlias({ key: '', path: '' });
  };

  const handleRemoveAlias = async (key) => {
    const res = await pytron.remove_path_alias(key);
    setPathAliases(res);
  };

  const handleAddProjectRoot = async () => {
    if (!pytron.select_project_root) return;
    const res = await pytron.select_project_root();
    if (res && res.path) {
      const updated = await pytron.add_project_root(res.path);
      setProjectRoots(updated || []);
    }
  };

  const handleRemoveProjectRoot = async (p) => {
    if (!pytron.remove_project_root) return;
    const updated = await pytron.remove_project_root(p);
    setProjectRoots(updated || []);
  };

  return (
    <div className="settings-view">
      {/* Top Segmented Tab Navigation Header */}
      <div className="settings-header">
        <div className="back-btn" onClick={onClose} title="Back to Search (Esc)">
          <ArrowLeft size={16} />
        </div>

        <div className="settings-tab-nav">
          <button
            className={`settings-tab-btn ${activeTab === 'general' ? 'active' : ''}`}
            onClick={() => setActiveTab('general')}
          >
            <Sliders size={13} />
            <span>General</span>
          </button>
          <button
            className={`settings-tab-btn ${activeTab === 'developer' ? 'active' : ''}`}
            onClick={() => setActiveTab('developer')}
          >
            <Code size={13} />
            <span>Developer</span>
          </button>
          <button
            className={`settings-tab-btn ${activeTab === 'shortcuts' ? 'active' : ''}`}
            onClick={() => setActiveTab('shortcuts')}
          >
            <Command size={13} />
            <span>Shortcuts</span>
          </button>
          <button
            className={`settings-tab-btn ${activeTab === 'workflows' ? 'active' : ''}`}
            onClick={() => setActiveTab('workflows')}
          >
            <Lock size={13} />
            <span>Vault & Scripts</span>
          </button>
          <button
            className={`settings-tab-btn ${activeTab === 'about' ? 'active' : ''}`}
            onClick={() => setActiveTab('about')}
          >
            <Sparkles size={13} />
            <span>About</span>
          </button>
        </div>

        <button className="action-button-primary" style={{ marginLeft: 'auto', fontSize: '11.5px', padding: '6px 12px' }} onClick={handleSave}>
          Done
        </button>
      </div>

      <div className="settings-content" style={{ flex: 1, overflowY: 'auto' }}>
        {!isResizing && (
          <div className="tab-pane-content">
            {/* =========================================================================
                TAB 1: GENERAL
                ========================================================================= */}
            {activeTab === 'general' && (
              <div className="tab-section-group">
                {/* Appearance */}
                <div className="settings-section">
                  <div className="section-title">Accent Theme</div>
                  <div className="theme-grid" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {[
                      { name: 'Lavender (Default)', color: '#bfa5ff' },
                      { name: 'Wall', color: 'adaptive', icon: 'palette' },
                      { name: 'Iris', color: '#6366f1' },
                      { name: 'Azure', color: '#0a84ff' },
                      { name: 'Emerald', color: '#32d74b' },
                      { name: 'Amber', color: '#ff9f0a' },
                      { name: 'Rose', color: '#ff375f' },
                      { name: 'Candy', color: '#ff2d55' }
                    ].map(t => (
                      <div
                        key={t.color}
                        className={`theme-swatch ${settings.theme_color === t.color ? 'active' : ''}`}
                        title={t.name}
                        style={{
                          width: '32px', height: '32px', borderRadius: '50%',
                          background: t.color === 'adaptive' ? 'linear-gradient(45deg, #ff3d00, #00e5ff)' : t.color,
                          cursor: 'pointer',
                          border: settings.theme_color === t.color ? '2px solid white' : 'none',
                          boxShadow: settings.theme_color === t.color ? `0 0 10px ${t.color === 'adaptive' ? '#00e5ff' : t.color}` : 'none',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '10px', fontWeight: 'bold', color: 'white'
                        }}
                        onClick={async () => {
                          const newTheme = t.color;
                          await updateSetting('theme_color', newTheme);
                          if (newTheme === 'adaptive') {
                            pytron.run_item({ action: 'refresh_theme' });
                          }
                          await pytron.update_settings({ ...settings, theme_color: newTheme });
                          window.dispatchEvent(new CustomEvent('settings_updated'));
                        }}
                      >
                        {t.color === 'adaptive' && 'W'}
                      </div>
                    ))}
                  </div>
                  {settings.theme_color === 'adaptive' && (
                    <p className="dim" style={{ fontSize: '11px', marginTop: '8px' }}>
                      Currently syncing with wallpaper accent. <span className="link-text" onClick={() => pytron.run_item({ action: 'refresh_theme' })}>Refresh Now</span>
                    </p>
                  )}
                </div>

                {/* System & Window Behavior */}
                <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                  <div className="section-title">Window & Behavior</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <label className="st-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
                      <div>
                        <span style={{ fontSize: '13px', display: 'block' }}>Launch on Startup</span>
                        <span className="dim" style={{ fontSize: '11px' }}>Start Bite silently in your background tray when Windows boots.</span>
                      </div>
                      <input
                        type="checkbox"
                        checked={settings.start_on_boot}
                        onChange={e => updateSetting('start_on_boot', e.target.checked)}
                        style={{ width: '18px', height: '18px', accentColor: 'var(--accent)' }}
                      />
                    </label>

                    <label className="st-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
                      <div>
                        <span style={{ fontSize: '13px', display: 'block' }}>Zen Mode (Minimalist Search)</span>
                        <span className="dim" style={{ fontSize: '11px' }}>Hide the body and footer until you start typing a query.</span>
                      </div>
                      <input
                        type="checkbox"
                        checked={settings.hide_footer}
                        onChange={e => updateSetting('hide_footer', e.target.checked)}
                        style={{ width: '18px', height: '18px', accentColor: 'var(--accent)' }}
                      />
                    </label>

                    <label className="st-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
                      <div>
                        <span style={{ fontSize: '13px', display: 'block' }}>System Stats in Search Bar</span>
                        <span className="dim" style={{ fontSize: '11px' }}>Display Battery, CPU, RAM & Clock HUD capsule in the search bar.</span>
                      </div>
                      <input
                        type="checkbox"
                        checked={settings.show_system_stats || false}
                        onChange={e => updateSetting('show_system_stats', e.target.checked)}
                        style={{ width: '18px', height: '18px', accentColor: 'var(--accent)' }}
                      />
                    </label>
                  </div>
                </div>

                {/* Global Launcher Hotkey */}
                <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                  <div className="section-title">Global Launcher Hotkey</div>
                  <p className="dim" style={{ fontSize: '11.5px', marginBottom: '10px' }}>
                    Press this key combination anywhere in Windows to toggle Bite on top of your screen.
                  </p>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <select
                      className="st-input"
                      style={{ width: '180px' }}
                      value={['Alt+B', 'Alt+Space', 'Ctrl+Space', 'Ctrl+Shift+Space', 'Alt+Shift+B'].includes(settings.global_hotkey) ? settings.global_hotkey : 'custom'}
                      onChange={async (e) => {
                        const val = e.target.value;
                        if (val !== 'custom') {
                          updateSetting('global_hotkey', val);
                          if (pytron.set_global_hotkey) {
                            const res = await pytron.set_global_hotkey(val);
                            if (res.success) {
                              pytron.send_notification("Global Hotkey Updated", `Launcher shortcut is now ${val}`);
                            }
                          }
                        }
                      }}
                    >
                      <option value="Alt+B">Alt + B (Default)</option>
                      <option value="Alt+Space">Alt + Space (Raycast style)</option>
                      <option value="Ctrl+Space">Ctrl + Space (Spotlight)</option>
                      <option value="Ctrl+Shift+Space">Ctrl + Shift + Space</option>
                      <option value="Alt+Shift+B">Alt + Shift + B</option>
                      <option value="custom">Custom Combination...</option>
                    </select>

                    <input
                      placeholder="e.g. Alt+B, Ctrl+Shift+B"
                      value={settings.global_hotkey || 'Alt+B'}
                      onChange={(e) => updateSetting('global_hotkey', e.target.value)}
                      className="st-input"
                      style={{ flex: 1 }}
                    />

                    <button
                      className="st-btn"
                      onClick={async () => {
                        if (pytron.set_global_hotkey && settings.global_hotkey) {
                          const res = await pytron.set_global_hotkey(settings.global_hotkey);
                          if (res.success) {
                            pytron.send_notification("Global Hotkey Active", `Launcher shortcut bound to ${settings.global_hotkey}`);
                          } else {
                            pytron.send_notification("Hotkey Error", res.error || "Failed to register shortcut combo");
                          }
                        }
                      }}
                    >
                      <Check size={14} /> Apply
                    </button>
                  </div>
                </div>

                {/* Setup & Onboarding Wizard */}
                {onOpenOnboarding && (
                  <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                    <div className="section-title">Setup Wizard</div>
                    <div className="st-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '4px 0' }}>
                      <div>
                        <span style={{ fontSize: '13px', display: 'block', fontWeight: 500 }}>Re-run Developer Onboarding</span>
                        <span className="dim" style={{ fontSize: '11px' }}>Step-by-step setup for theme, privacy, IDE, and Git roots.</span>
                      </div>
                      <button className="action-button-secondary" onClick={onOpenOnboarding}>
                        <Zap size={12} /> Launch Wizard
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* =========================================================================
                TAB 2: DEVELOPER & IDE
                ========================================================================= */}
            {activeTab === 'developer' && (
              <div className="tab-section-group">
                {/* Code Editor / IDE */}
                <div className="settings-section">
                  <div className="section-title">Preferred Code Editor</div>
                  <p className="dim" style={{ fontSize: '11.5px', marginBottom: '10px' }}>
                    Used by <b>repo:</b>, <b>ide:&lt;alias&gt;</b>, and <b>Open in Editor</b> actions.
                  </p>
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                    <select
                      className="st-input"
                      style={{ width: '150px' }}
                      value={
                        ['cursor', 'code', 'codium', 'pycharm', 'nvim'].includes(settings.preferred_ide)
                          ? settings.preferred_ide
                          : settings.preferred_ide ? 'custom' : ''
                      }
                      onChange={e => {
                        const val = e.target.value;
                        if (val !== 'custom') {
                          updateSetting('preferred_ide', val);
                        }
                      }}
                    >
                      <option value="">Auto-Detect</option>
                      <option value="cursor">Cursor</option>
                      <option value="code">VS Code</option>
                      <option value="codium">VSCodium</option>
                      <option value="pycharm">PyCharm</option>
                      <option value="nvim">Neovim</option>
                      <option value="custom">Custom Path...</option>
                    </select>
                    <input
                      placeholder="Command or full path (e.g. cursor or C:\...\Code.exe)"
                      value={settings.preferred_ide || ''}
                      onChange={e => updateSetting('preferred_ide', e.target.value)}
                      className="st-input"
                      style={{ flex: 1 }}
                    />
                    <button
                      className="st-btn secondary"
                      title="Browse Executable..."
                      onClick={async () => {
                        if (pytron.select_ide_path) {
                          const res = await pytron.select_ide_path();
                          if (res && res.path) {
                            updateSetting('preferred_ide', res.path);
                            pytron.send_notification("Editor Updated", `Preferred editor set to ${res.path}`);
                          }
                        }
                      }}
                    >
                      <FolderOpen size={16} />
                    </button>
                  </div>
                </div>

                {/* Git & Workspace Roots */}
                <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                  <div className="section-title">Git Workspace Roots</div>
                  <p className="dim" style={{ fontSize: '11.5px', marginBottom: '10px' }}>
                    Folders scanned automatically for repositories (searchable via <b>repo:</b>).
                  </p>
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                    <button className="st-btn" onClick={handleAddProjectRoot}>
                      <FolderOpen size={14} /> Add Project Root Folder...
                    </button>
                  </div>
                  <div className="shortcuts-list">
                    {projectRoots.map((rootPath, i) => (
                      <div className="shortcut-item" key={i}>
                        <div className="sc-icon"><FolderOpen size={14} /></div>
                        <div className="sc-info">
                          <span className="sc-url">{rootPath}</span>
                        </div>
                        <div className="sc-del" onClick={() => handleRemoveProjectRoot(rootPath)}>
                          <Trash2 size={14} />
                        </div>
                      </div>
                    ))}
                    {projectRoots.length === 0 && (
                      <div className="dim" style={{ fontSize: '11px' }}>
                        Scanning standard developer directories (projects, dev, repos, source) automatically.
                      </div>
                    )}
                  </div>
                </div>

                {/* Path Aliases */}
                <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                  <div className="section-title">Path Aliases</div>
                  <p className="dim" style={{ fontSize: '11.5px', marginBottom: '10px' }}>
                    Create aliases like <b>@project</b> for quick terminal navigation and <b>ide:@project</b>.
                  </p>
                  <div className="add-shortcut-form">
                    <input
                      placeholder="@project"
                      value={newAlias.key}
                      onChange={e => setNewAlias({ ...newAlias, key: e.target.value })}
                      className="st-input"
                      style={{ width: '140px' }}
                    />
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <input
                        placeholder="Full path to folder"
                        value={newAlias.path}
                        onChange={e => setNewAlias({ ...newAlias, path: e.target.value })}
                        className="st-input"
                        style={{ flex: 1 }}
                      />
                      <button className="st-btn secondary" title="Browse Folder..." onClick={async () => {
                        const res = await pytron.select_folder_for_alias();
                        if (res.path) {
                          setNewAlias(prev => ({ ...prev, path: res.path }));
                        }
                      }}>
                        <FolderOpen size={16} />
                      </button>
                    </div>
                    <button className="st-btn" onClick={handleAddAlias} style={{ gridColumn: '1 / -1' }}>
                      <Plus size={14} /> Add Alias
                    </button>
                  </div>

                  <div className="shortcuts-list" style={{ marginTop: '12px' }}>
                    {Object.entries(pathAliases || {}).map(([key, path]) => (
                      <div className="shortcut-item" key={key}>
                        <div className="sc-icon"><FolderOpen size={14} /></div>
                        <div className="sc-info">
                          <span className="sc-key">{key}</span>
                          <span className="sc-url">{path}</span>
                        </div>
                        <div className="sc-del" onClick={() => handleRemoveAlias(key)}>
                          <Trash2 size={14} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* =========================================================================
                TAB 3: SHORTCUTS & SNIPPETS
                ========================================================================= */}
            {activeTab === 'shortcuts' && (
              <div className="tab-section-group">
                {/* Custom Shortcuts */}
                <div className="settings-section">
                  <div className="section-title">Web & App Shortcuts</div>
                  <p className="dim" style={{ fontSize: '11.5px', marginBottom: '10px' }}>
                    Custom triggers for search queries (use <code>{`{}`}</code> as query placeholder).
                  </p>
                  <div className="add-shortcut-form">
                    <input
                      placeholder="Keyword (e.g. g)"
                      value={scForm.id}
                      onChange={e => setScForm({ ...scForm, id: e.target.value })}
                      className="st-input"
                    />
                    <input
                      placeholder="Name (e.g. Google Search)"
                      value={scForm.name}
                      onChange={e => setScForm({ ...scForm, name: e.target.value })}
                      className="st-input"
                    />
                    <input
                      placeholder="URL with {} (e.g. https://google.com/search?q={})"
                      value={scForm.url}
                      onChange={e => setScForm({ ...scForm, url: e.target.value })}
                      className="st-input full"
                    />
                    <button className="st-btn" onClick={handleAddShortcut}>
                      <Plus size={14} /> {editingId ? 'Update' : 'Add'} Shortcut
                    </button>
                  </div>

                  <div className="shortcuts-list">
                    {shortcuts.map(s => (
                      <div className="shortcut-item" key={s.id}>
                        <div className="sc-icon"><ItemIcon icon={s.icon || 'globe'} /></div>
                        <div className="sc-info">
                          <span className="sc-key">{s.id}</span>
                          <span className="sc-name">{s.name}</span>
                          <span className="sc-url">{s.url}</span>
                        </div>
                        <div className="sc-actions">
                          <div className="sc-edit" onClick={() => handleEditShortcut(s)}><Edit2 size={13} /></div>
                          <div className="sc-del" onClick={() => handleDeleteShortcut(s.id)}><Trash2 size={13} /></div>
                        </div>
                      </div>
                    ))}
                    {shortcuts.length === 0 && <div className="empty-st">No custom shortcuts yet.</div>}
                  </div>
                </div>

                {/* Text Snippets */}
                <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                  <div className="section-title">Text Expansion Snippets</div>
                  <div className="add-shortcut-form">
                    <input
                      placeholder="Snippet Name"
                      value={snipForm.name}
                      onChange={e => setSnipForm({ ...snipForm, name: e.target.value })}
                      className="st-input"
                    />
                    <textarea
                      placeholder="Content to copy or paste..."
                      value={snipForm.content}
                      onChange={e => setSnipForm({ ...snipForm, content: e.target.value })}
                      className="st-input full"
                      style={{ minHeight: '60px', resize: 'vertical' }}
                    />
                    <button className="st-btn" onClick={handleAddSnippet}>
                      <Plus size={14} /> Create Snippet
                    </button>
                  </div>

                  <div className="shortcuts-list">
                    {snippets.map(s => (
                      <div className="shortcut-item" key={s.id}>
                        <div className="sc-icon"><Scissors size={14} /></div>
                        <div className="sc-info">
                          <span className="sc-key">{s.name}</span>
                          <span className="sc-url">{s.content.substring(0, 50)}...</span>
                        </div>
                        <div className="sc-del" onClick={() => handleDeleteSnippet(s.id)}>
                          <Trash2 size={14} />
                        </div>
                      </div>
                    ))}
                    {snippets.length === 0 && <div className="empty-st">No snippets yet.</div>}
                  </div>
                </div>
              </div>
            )}

            {/* =========================================================================
                TAB 4: VAULT & WORKFLOWS
                ========================================================================= */}
            {activeTab === 'workflows' && (
              <div className="tab-section-group">
                {/* Workflows */}
                <div className="settings-section">
                  <div className="section-title">Python Workflows</div>
                  <p className="dim" style={{ fontSize: '11.5px', marginBottom: '12px' }}>
                    Extend Bite with custom scripts. Python scripts in your workflows folder are indexed automatically (search via <b>wf:</b>).
                  </p>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="st-btn secondary" onClick={() => window.onWfPrompt?.()}>
                      <Plus size={14} /> Import Script
                    </button>
                    <button className="st-btn" onClick={async () => {
                      const name = prompt("Workflow Name:");
                      if (name) {
                        const res = await pytron.create_workflow(name);
                        if (res.success) {
                          pytron.send_notification("Workflow Created", `Created ${name} successfully`);
                          pytron.open_file(res.path);
                        } else {
                          pytron.send_notification("Error", res.error || "Failed");
                        }
                      }
                    }}>
                      <Plus size={14} /> Create New
                    </button>
                    <button className="st-btn secondary" onClick={() => pytron.run_item({ action: 'open_wf' })}>
                      Open Folder
                    </button>
                  </div>
                </div>

                {/* Secure Vault */}
                <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px', marginTop: '16px' }}>
                  <VaultSection />
                </div>
              </div>
            )}

            {/* =========================================================================
                TAB 5: ABOUT & UPDATES
                ========================================================================= */}
            {activeTab === 'about' && (
              <div className="tab-section-group">
                {/* App Brand Hero Card */}
                <div className="about-hero-card">
                  <img src={biteIcon} alt="Bite" className="about-app-icon" />
                  <div className="about-details">
                    <span
                      className="brand-logo"
                      style={{
                        WebkitMaskImage: `url(${biteWordmark})`,
                        maskImage: `url(${biteWordmark})`,
                        height: '32px',
                        width: '72px'
                      }}
                      title="Bite"
                    />
                    <div className="about-version">Version 0.4.0 (Dev Edition)</div>
                    <div className="about-desc">The lightning-fast developer command launcher and workflow engine.</div>
                    <div className="about-copy">Copyright © 2025 Ghua8088. Crafted with Pytron.</div>
                  </div>
                </div>

                {/* Updates */}
                <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                  <div className="section-title">Software Updates</div>
                  <UpdaterSection />
                </div>

                {/* Quick Cheatsheet Reference */}
                <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                  <div className="section-title">Keybindings & Prefixes</div>
                  <div className="about-cheatsheet-grid">
                    <div className="about-cheat-row"><code>ide:&lt;alias&gt;</code> <span>Open alias or workspace in IDE</span></div>
                    <div className="about-cheat-row"><code>repo:&lt;query&gt;</code> <span>Search Git repositories</span></div>
                    <div className="about-cheat-row"><code>t:&lt;cmd&gt;</code> <span>Execute terminal command</span></div>
                    <div className="about-cheat-row"><code>@&lt;alias&gt;</code> <span>Browse smart folder path</span></div>
                    <div className="about-cheat-row"><code>Ctrl + K</code> <span>Open context action menu</span></div>
                    <div className="about-cheat-row"><code>Ctrl + ,</code> <span>Open Bite Settings</span></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
