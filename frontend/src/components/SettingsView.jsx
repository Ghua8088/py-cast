import { useState, useEffect } from 'react'
import pytron from 'pytron-client'
import { Plus, Trash2, ArrowLeft, Link as LinkIcon, Scissors, RefreshCw, Download, Zap, Edit2, FolderOpen } from 'lucide-react'

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

export default function SettingsView({ onClose, isResizing }) {
  const [shortcuts, setShortcuts] = useState([])
  const [snippets, setSnippets] = useState([])
  const [settings, setSettings] = useState({ theme_color: '#5e5ce6', start_on_boot: false, excluded_folders: [], hide_footer: false })

  const [form, setForm] = useState({ keyword: '', name: '', url: '' })
  const [editingId, setEditingId] = useState(null)
  const [snipForm, setSnipForm] = useState({ name: '', content: '' })
  const [excludeDir, setExcludeDir] = useState('')
  const [pathAliases, setPathAliases] = useState({})
  const [newAlias, setNewAlias] = useState({ key: '', path: '' })

  useEffect(() => {
    pytron.get_user_shortcuts().then(setShortcuts)
    pytron.get_user_snippets().then(setSnippets)
    pytron.get_path_aliases().then(setPathAliases)
    pytron.get_settings().then(async (s) => {
      setSettings(s)
      if (s.theme_color === 'adaptive') {
        const t = await pytron.get_adaptive_theme();
        if (t?.accent) document.documentElement.style.setProperty('--accent', t.accent);
      } else {
        document.documentElement.style.setProperty('--accent', s.theme_color)
      }
    })
  }, [])

  const updateSetting = async (key, val) => {
    const newSettings = { ...settings, [key]: val }
    setSettings(newSettings)

    if (key === 'theme_color') {
      if (val === 'adaptive') {
        const t = await pytron.get_adaptive_theme();
        if (t?.accent) document.documentElement.style.setProperty('--accent', t.accent);
      } else {
        document.documentElement.style.setProperty('--accent', val)
      }
    }

    // Auto-save the updated settings to backend
    await pytron.update_settings(newSettings);
    window.dispatchEvent(new CustomEvent('settings_updated'));
  }

  const handleSave = async () => {
    await pytron.update_settings(settings)
    pytron.send_notification("Settings Saved", "Your preferences have been updated.")
    window.dispatchEvent(new CustomEvent('settings_updated'))
  }

  const handleAdd = async () => {
    if (!form.keyword || !form.url) return;
    const newShortcuts = await pytron.add_shortcut(form.keyword, form.name || form.keyword, form.url)
    setShortcuts(newShortcuts)
    setForm({ keyword: '', name: '', url: '' })
    setEditingId(null)
  }

  const handleEditInit = (s) => {
    setEditingId(s.id)
    setForm({
      keyword: s.id,
      name: s.name,
      url: s.commands ? s.commands.join('\n') : (s.url || s.path || '')
    })
    // Scroll to form
    document.querySelector('.add-shortcut-form')?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleDelete = async (id) => {
    const newShortcuts = await pytron.remove_shortcut(id)
    setShortcuts(newShortcuts)
    if (editingId === id) {
      setEditingId(null)
      setForm({ keyword: '', name: '', url: '' })
    }
  }

  const handleAddSnippet = async () => {
    if (!snipForm.name || !snipForm.content) return;
    const newSnippets = await pytron.add_snippet(snipForm.name, snipForm.content)
    setSnippets(newSnippets)
    setSnipForm({ name: '', content: '' })
  }

  const handleDeleteSnippet = async (id) => {
    const newSnippets = await pytron.remove_snippet(id)
    setSnippets(newSnippets)
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

  return (
    <div className="settings-view">
      <div className="settings-header">
        <div className="back-btn" onClick={onClose}><ArrowLeft size={18} /></div>
        <h3>Bite Settings</h3>
        <button className="action-button-primary" style={{ marginLeft: 'auto', fontSize: '12px' }} onClick={handleSave}>
          Apply Changes
        </button>
      </div>

      <div className="settings-content" style={{ flex: 1, overflowY: 'auto' }}>
        {!isResizing && (
          <>
            {/* Appearance */}
            <div className="settings-section">
              <div className="section-title">Appearance</div>
              <div className="theme-grid" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {[
                  { name: 'Wall', color: 'adaptive', icon: 'palette' },
                  { name: 'Default', color: '#5e5ce6' },
                  { name: 'Rose', color: '#ff375f' },
                  { name: 'Emerald', color: '#32d74b' },
                  { name: 'Amber', color: '#ff9f0a' },
                  { name: 'Azure', color: '#0a84ff' },
                  { name: 'Lavender', color: '#bf5af2' },
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

                      // Persist immediately with the correct value
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

            {/* General */}
            <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
              <div className="section-title">General</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <label className="st-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
                  <span style={{ fontSize: '13px' }}>Launch Bite on Startup</span>
                  <input
                    type="checkbox"
                    checked={settings.start_on_boot}
                    onChange={e => updateSetting('start_on_boot', e.target.checked)}
                    style={{ width: '18px', height: '18px', accentColor: 'var(--accent)' }}
                  />
                </label>
                <label className="st-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
                  <span style={{ fontSize: '13px' }}>Zen Mode (Hide Body)</span>
                  <input
                    type="checkbox"
                    checked={settings.hide_footer}
                    onChange={e => updateSetting('hide_footer', e.target.checked)}
                    style={{ width: '18px', height: '18px', accentColor: 'var(--accent)' }}
                  />
                </label>
              </div>
            </div>

            <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
              <div className="section-title">Custom Commands & Shortcuts</div>
              <p className="dim" style={{ fontSize: '12px', marginBottom: '8px' }}>
                Add web searches (e.g. 'yt') or shell commands (e.g. 'npm start').
              </p>
              <div className="add-shortcut-form">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', gridColumn: '1 / -1' }}>
                  <span style={{ fontSize: '11px', color: 'var(--accent)', fontWeight: 'bold', letterSpacing: '0.5px' }}>
                    {editingId ? `EDITING: ${editingId}` : 'CREATE NEW SHORTCUT'}
                  </span>
                  {editingId && (
                    <span
                      className="link-text"
                      style={{ fontSize: '11px', cursor: 'pointer', textDecoration: 'underline' }}
                      onClick={() => { setEditingId(null); setForm({ keyword: '', name: '', url: '' }); }}
                    >
                      Cancel Edit
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '8px', gridColumn: '1 / -1' }}>
                  <input
                    placeholder="Key (e.g. 'dev')"
                    value={form.keyword}
                    onChange={e => setForm({ ...form, keyword: e.target.value })}
                    className="st-input"
                    style={{ flex: 1 }}
                    disabled={!!editingId}
                  />
                  <input
                    placeholder="Name"
                    value={form.name}
                    onChange={e => setForm({ ...form, name: e.target.value })}
                    className="st-input"
                    style={{ flex: 2 }}
                  />
                </div>
                <textarea
                  placeholder="URL(s) or Command(s) - Use new line or ; for multi"
                  value={form.url}
                  onChange={e => setForm({ ...form, url: e.target.value })}
                  className="st-input full"
                  style={{ minHeight: '80px', padding: '10px', gridColumn: '1 / -1' }}
                />
                <button className="st-btn" onClick={handleAdd} style={{ gridColumn: '1 / -1' }}>
                  {editingId ? <><RefreshCw size={14} /> Update Shortcut</> : <><Plus size={14} /> Add Shortcut</>}
                </button>
              </div>

              <div className="shortcuts-list">
                {shortcuts.map(s => (
                  <div className={`shortcut-item ${editingId === s.id ? 'is-editing' : ''}`} key={s.id}>
                    <div className="sc-icon"><LinkIcon size={14} /></div>
                    <div className="sc-info">
                      <span className="sc-key">{s.id}</span>
                      <span className="sc-url">{s.commands ? `Multi-step (${s.commands.length})` : (s.url || s.path)}</span>
                    </div>
                    <div className="sc-actions" style={{ display: 'flex', gap: '8px' }}>
                      <div className="sc-edit" title="Edit" onClick={() => handleEditInit(s)} style={{ cursor: 'pointer', opacity: 0.6 }}>
                        <Edit2 size={14} />
                      </div>
                      <div className="sc-del" title="Delete" onClick={() => handleDelete(s.id)} style={{ cursor: 'pointer', opacity: 0.6, color: '#ff453a' }}>
                        <Trash2 size={14} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Index Management */}
            <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
              <div className="section-title">Index Management</div>
              <div className="index-actions" style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                <button className="st-btn secondary" style={{ flex: 1 }} onClick={() => pytron.run_item({ action: 'force_reindex' })}>
                  <RefreshCw size={14} /> Force Re-index
                </button>
              </div>

              <div className="exclude-form" style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                <input
                  className="st-input" style={{ flex: 1 }}
                  placeholder="Exclude Folder (e.g. 'Downloads')"
                  value={excludeDir}
                  onChange={e => setExcludeDir(e.target.value)}
                />
                <button className="st-btn" style={{ width: 'auto', padding: '0 16px' }} onClick={() => {
                  if (!excludeDir) return;
                  const newList = [...settings.excluded_folders, excludeDir]
                  updateSetting('excluded_folders', newList)
                  setExcludeDir('')
                }}>
                  Add
                </button>
              </div>

              <div className="tags-list" style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {settings.excluded_folders.map(dir => (
                  <div key={dir} className="tag-item" style={{
                    background: 'rgba(255,255,255,0.05)', padding: '4px 10px',
                    borderRadius: '6px', fontSize: '11px', display: 'flex',
                    alignItems: 'center', gap: '6px', border: '1px solid var(--border)'
                  }}>
                    {dir}
                    <Trash2 size={10} style={{ cursor: 'pointer', color: '#ff453a' }} onClick={() => {
                      const newList = settings.excluded_folders.filter(d => d !== dir)
                      updateSetting('excluded_folders', newList)
                    }} />
                  </div>
                ))}
              </div>
            </div>

            <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
              <div className="section-title">Snippets</div>
              <div className="add-shortcut-form">
                <input
                  placeholder="Snippet Name"
                  value={snipForm.name}
                  onChange={e => setSnipForm({ ...snipForm, name: e.target.value })}
                  className="st-input"
                />
                <textarea
                  placeholder="Content..."
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

            <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
              <div className="section-title">Path Variables</div>
              <p className="dim" style={{ fontSize: '11px', marginBottom: '8px' }}>
                Create aliases like <b>@project</b> for terminal paths.
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
                    } else if (res.error) {
                      // silent 
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

            <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
              <div className="section-title">Workflows</div>
              <p className="dim" style={{ fontSize: '12px', marginBottom: '12px' }}>
                Extend Bite using Python. Scripts in your workflows folder are indexed automatically.
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

            <UpdaterSection />
          </>
        )}
      </div>
    </div >
  )
}
