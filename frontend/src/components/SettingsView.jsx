import { useState, useEffect } from 'react'
import pytron from 'pytron-client'
import { Plus, Trash2, ArrowLeft, Link as LinkIcon, Scissors, RefreshCw, Download, Zap } from 'lucide-react'

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

export default function SettingsView({ onClose }) {
  const [shortcuts, setShortcuts] = useState([])
  const [snippets, setSnippets] = useState([])
  const [settings, setSettings] = useState({ theme_color: '#5e5ce6', start_on_boot: false, excluded_folders: [] })

  const [form, setForm] = useState({ keyword: '', name: '', url: '' })
  const [snipForm, setSnipForm] = useState({ name: '', content: '' })
  const [excludeDir, setExcludeDir] = useState('')

  useEffect(() => {
    pytron.get_user_shortcuts().then(setShortcuts)
    pytron.get_user_snippets().then(setSnippets)
    pytron.get_settings().then(s => {
      setSettings(s)
      document.documentElement.style.setProperty('--accent', s.theme_color)
    })
  }, [])

  const updateSetting = (key, val) => {
    const newSettings = { ...settings, [key]: val }
    setSettings(newSettings)
    if (key === 'theme_color') {
      document.documentElement.style.setProperty('--accent', val)
    }
  }

  const handleSave = async () => {
    await pytron.update_settings(settings)
    pytron.notify("Settings Saved", "Your preferences have been updated.", "success")
    window.dispatchEvent(new CustomEvent('settings_updated'))
  }

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
        {/* Appearance */}
        <div className="settings-section">
          <div className="section-title">Appearance</div>
          <div className="theme-grid" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
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
                style={{
                  width: '32px', height: '32px', borderRadius: '50%',
                  background: t.color, cursor: 'pointer',
                  border: settings.theme_color === t.color ? '2px solid white' : 'none',
                  boxShadow: settings.theme_color === t.color ? `0 0 10px ${t.color}` : 'none'
                }}
                onClick={() => updateSetting('theme_color', t.color)}
              />
            ))}
          </div>
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
            <input
              placeholder="Key (e.g. 'dev')"
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
              placeholder="URL or Command"
              value={form.url}
              onChange={e => setForm({ ...form, url: e.target.value })}
              className="st-input full"
            />
            <button className="st-btn" onClick={handleAdd}>
              <Plus size={14} /> Add
            </button>
          </div>

          <div className="shortcuts-list">
            {shortcuts.map(s => (
              <div className="shortcut-item" key={s.id}>
                <div className="sc-icon"><LinkIcon size={14} /></div>
                <div className="sc-info">
                  <span className="sc-key">{s.id}</span>
                  <span className="sc-url">{s.url || s.path}</span>
                </div>
                <div className="sc-del" onClick={() => handleDelete(s.id)}>
                  <Trash2 size={14} />
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
                  pytron.notify("Workflow Created", `Created ${name} successfully`, "success");
                  pytron.open_file(res.path);
                } else {
                  pytron.notify("Error", res.error || "Failed", "error");
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
      </div>
    </div>
  )
}
