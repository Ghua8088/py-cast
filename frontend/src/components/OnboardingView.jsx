import { useState, useEffect } from 'react'
import pytron from 'pytron-client'
import {
  Zap, ArrowRight, ArrowLeft, Check, Code, Shield, FolderGit2,
  Terminal, Sparkles, FolderPlus, Eye, Lock, Globe, Cpu, Palette
} from 'lucide-react'

export default function OnboardingView({ onComplete, isResizing }) {
  const [step, setStep] = useState(1);
  const totalSteps = 5;

  const [themeColor, setThemeColor] = useState('#6366f1');
  const [startOnBoot, setStartOnBoot] = useState(false);
  const [optInClipboard, setOptInClipboard] = useState(true);
  const [optInAi, setOptInAi] = useState(true);
  const [optInFavicons, setOptInFavicons] = useState(true);
  const [showStats, setShowStats] = useState(true);
  const [preferredIde, setPreferredIde] = useState('cursor');
  const [customIdePath, setCustomIdePath] = useState('');
  const [projectRoots, setProjectRoots] = useState([]);

  useEffect(() => {
    // Load initial system roots or settings if available
    if (pytron.get_project_roots) {
      pytron.get_project_roots().then(roots => setProjectRoots(roots || []));
    }
  }, []);

  const handleAddProjectRoot = async () => {
    if (!pytron.select_project_root) return;
    const res = await pytron.select_project_root();
    if (res && res.path && !projectRoots.includes(res.path)) {
      const updated = await pytron.add_project_root(res.path);
      setProjectRoots(updated || [...projectRoots, res.path]);
    }
  };

  const handleFinish = async () => {
    const finalIde = preferredIde === 'custom' ? customIdePath : preferredIde;
    const newSettings = {
      theme_color: themeColor,
      start_on_boot: startOnBoot,
      opt_in_clipboard: optInClipboard,
      opt_in_ai: optInAi,
      opt_in_favicons: optInFavicons,
      show_system_stats: showStats,
      preferred_ide: finalIde,
      onboarding_completed: true
    };

    await pytron.update_settings(newSettings);
    if (themeColor === 'adaptive') {
      pytron.run_item({ action: 'refresh_theme' });
    }
    window.dispatchEvent(new CustomEvent('settings_updated'));
    pytron.send_notification("Welcome to Bite!", "Dev environment setup complete.");
    onComplete(newSettings);
  };

  const themes = [
    { name: 'Iris', color: '#6366f1' },
    { name: 'Sky', color: '#0ea5e9' },
    { name: 'Emerald', color: '#10b981' },
    { name: 'Rose', color: '#f43f5e' },
    { name: 'Amber', color: '#f59e0b' },
    { name: 'Adaptive', color: 'adaptive' }
  ];

  const editors = [
    { id: 'cursor', name: 'Cursor', desc: 'AI-first Code Editor' },
    { id: 'code', name: 'VS Code', desc: 'Visual Studio Code' },
    { id: 'codium', name: 'VSCodium', desc: 'Open Source Binaries' },
    { id: 'nvim', name: 'Neovim', desc: 'Hyperextensible Vim' },
    { id: 'pycharm', name: 'PyCharm', desc: 'Python IDE' },
    { id: 'custom', name: 'Custom Path', desc: 'Browse .exe / command' }
  ];

  return (
    <div className="onboarding-container" style={{ '--accent': themeColor === 'adaptive' ? '#6366f1' : themeColor }}>
      {/* Header & Step Indicator */}
      <div className="onboarding-header">
        <div className="onboarding-brand">
          <div className="brand-dot" />
          <span className="brand-title">Bite Setup</span>
        </div>
        <div className="onboarding-step-tracker">
          {Array.from({ length: totalSteps }).map((_, i) => (
            <div
              key={i}
              className={`step-dot ${step === i + 1 ? 'active' : ''} ${step > i + 1 ? 'completed' : ''}`}
              onClick={() => setStep(i + 1)}
            />
          ))}
        </div>
        <div className="step-label">Step {step} of {totalSteps}</div>
      </div>

      {/* Step Content */}
      <div className="onboarding-body">
        {/* STEP 1: WELCOME & THEME */}
        {step === 1 && (
          <div className="onboarding-step-content">
            <div className="step-hero">
              <div className="step-icon-squircle">
                <Sparkles size={24} color="var(--accent)" />
              </div>
              <h2 className="step-title">Welcome to Bite</h2>
              <p className="step-subtitle">
                The lightning-fast, developer-first command launcher and workflow engine.
              </p>
            </div>

            <div className="onboarding-card">
              <div className="card-label">Choose your Accent Color</div>
              <div className="theme-picker-grid">
                {themes.map(t => (
                  <button
                    key={t.color}
                    className={`theme-pill-btn ${themeColor === t.color ? 'selected' : ''}`}
                    onClick={() => {
                      setThemeColor(t.color);
                      if (t.color !== 'adaptive') {
                        document.documentElement.style.setProperty('--accent', t.color);
                      }
                    }}
                  >
                    <span
                      className="swatch-circle"
                      style={{
                        background: t.color === 'adaptive'
                          ? 'linear-gradient(135deg, #ff007a, #00f0ff)'
                          : t.color
                      }}
                    />
                    <span>{t.name}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="onboarding-card">
              <label className="toggle-row">
                <div>
                  <div className="toggle-title">Launch on System Startup</div>
                  <div className="toggle-desc">Keep Bite instantly accessible in your background tray</div>
                </div>
                <input
                  type="checkbox"
                  className="st-checkbox"
                  checked={startOnBoot}
                  onChange={e => setStartOnBoot(e.target.checked)}
                />
              </label>
            </div>
          </div>
        )}

        {/* STEP 2: PRIVACY & INTELLIGENCE */}
        {step === 2 && (
          <div className="onboarding-step-content">
            <div className="step-hero">
              <div className="step-icon-squircle">
                <Shield size={24} color="var(--accent)" />
              </div>
              <h2 className="step-title">Privacy & Local Intelligence</h2>
              <p className="step-subtitle">
                All heuristics and caches run 100% offline and locally on your machine.
              </p>
            </div>

            <div className="onboarding-card">
              <label className="toggle-row">
                <div>
                  <div className="toggle-title">Local Clipboard History</div>
                  <div className="toggle-desc">Store recent copied texts securely for instant multi-paste</div>
                </div>
                <input
                  type="checkbox"
                  className="st-checkbox"
                  checked={optInClipboard}
                  onChange={e => setOptInClipboard(e.target.checked)}
                />
              </label>
            </div>

            <div className="onboarding-card">
              <label className="toggle-row">
                <div>
                  <div className="toggle-title">Smart Learning & Top Hits</div>
                  <div className="toggle-desc">Rank frequently executed commands and projects dynamically</div>
                </div>
                <input
                  type="checkbox"
                  className="st-checkbox"
                  checked={optInAi}
                  onChange={e => setOptInAi(e.target.checked)}
                />
              </label>
            </div>

            <div className="onboarding-card">
              <label className="toggle-row">
                <div>
                  <div className="toggle-title">System Status in Search Bar</div>
                  <div className="toggle-desc">Display subtle Battery, CPU, RAM & Time HUD in the top bar</div>
                </div>
                <input
                  type="checkbox"
                  className="st-checkbox"
                  checked={showStats}
                  onChange={e => setShowStats(e.target.checked)}
                />
              </label>
            </div>
          </div>
        )}

        {/* STEP 3: PREFERRED CODE EDITOR */}
        {step === 3 && (
          <div className="onboarding-step-content">
            <div className="step-hero">
              <div className="step-icon-squircle">
                <Code size={24} color="var(--accent)" />
              </div>
              <h2 className="step-title">Preferred Code Editor</h2>
              <p className="step-subtitle">
                Bite opens Git repositories, projects, and scripts directly in your favorite IDE.
              </p>
            </div>

            <div className="editor-grid">
              {editors.map(ed => (
                <div
                  key={ed.id}
                  className={`editor-card ${preferredIde === ed.id ? 'active' : ''}`}
                  onClick={() => setPreferredIde(ed.id)}
                >
                  <div className="editor-card-header">
                    <span className="editor-name">{ed.name}</span>
                    {preferredIde === ed.id && <Check size={14} className="editor-check" />}
                  </div>
                  <div className="editor-desc">{ed.desc}</div>
                </div>
              ))}
            </div>

            {preferredIde === 'custom' && (
              <div className="onboarding-card" style={{ marginTop: '12px' }}>
                <div className="card-label">Custom Executable Path or Command</div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    className="st-input"
                    style={{ flex: 1 }}
                    placeholder="e.g. C:\Users\...\AppData\Local\Programs\...\editor.exe"
                    value={customIdePath}
                    onChange={e => setCustomIdePath(e.target.value)}
                  />
                  <button
                    className="st-btn secondary"
                    onClick={async () => {
                      if (pytron.select_ide_path) {
                        const res = await pytron.select_ide_path();
                        if (res && res.path) setCustomIdePath(res.path);
                      }
                    }}
                  >
                    Browse
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* STEP 4: GIT WORKSPACES & ROOTS */}
        {step === 4 && (
          <div className="onboarding-step-content">
            <div className="step-hero">
              <div className="step-icon-squircle">
                <FolderGit2 size={24} color="var(--accent)" />
              </div>
              <h2 className="step-title">Git Workspaces & Repositories</h2>
              <p className="step-subtitle">
                Type <code>repo:</code> to search and jump to any repository on your disk instantly.
              </p>
            </div>

            <div className="onboarding-card">
              <div className="card-header-flex">
                <div className="card-label">Configured Search Roots</div>
                <button className="action-pill primary mini" onClick={handleAddProjectRoot}>
                  <FolderPlus size={12} />
                  <span>Add Folder</span>
                </button>
              </div>

              <div className="roots-list">
                <div className="root-pill auto">
                  <span>Universal Home Dev Folders (~/projects, ~/repos, ~/source, ~/dev)</span>
                  <span className="badge-tag">Auto</span>
                </div>
                {projectRoots.map((r, i) => (
                  <div key={i} className="root-pill">
                    <span className="truncate">{r}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="tip-box">
              <Terminal size={14} color="var(--accent)" />
              <span>Git branches, modified dirty states, and origin URLs are parsed with zero lag.</span>
            </div>
          </div>
        )}

        {/* STEP 5: READY & CHEATSHEET */}
        {step === 5 && (
          <div className="onboarding-step-content">
            <div className="step-hero">
              <div className="step-icon-squircle success">
                <Check size={24} color="#10b981" />
              </div>
              <h2 className="step-title">You're All Set!</h2>
              <p className="step-subtitle">
                Here are your essential superpowers to get moving fast:
              </p>
            </div>

            <div className="cheatsheet-grid">
              <div className="cheat-card">
                <div className="cheat-prefix">repo:</div>
                <div className="cheat-info">
                  <div className="cheat-title">Git Repositories</div>
                  <div className="cheat-desc">Search local repos & open in {preferredIde.toUpperCase()}</div>
                </div>
              </div>
              <div className="cheat-card">
                <div className="cheat-prefix">t:</div>
                <div className="cheat-info">
                  <div className="cheat-title">Quick Terminal</div>
                  <div className="cheat-desc">Execute shell commands or scripts directly</div>
                </div>
              </div>
              <div className="cheat-card">
                <div className="cheat-prefix">@</div>
                <div className="cheat-info">
                  <div className="cheat-title">Path Aliases</div>
                  <div className="cheat-desc">Instant file system navigation (@downloads, @desktop)</div>
                </div>
              </div>
              <div className="cheat-card">
                <div className="cheat-prefix">Ctrl+K</div>
                <div className="cheat-info">
                  <div className="cheat-title">Action Menu</div>
                  <div className="cheat-desc">Copy paths, reveal in Explorer, pin items & share</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Navigation */}
      <div className="onboarding-footer">
        {step > 1 ? (
          <button className="nav-btn secondary" onClick={() => setStep(s => s - 1)}>
            <ArrowLeft size={14} />
            <span>Back</span>
          </button>
        ) : (
          <div />
        )}

        {step < totalSteps ? (
          <button className="nav-btn primary" onClick={() => setStep(s => s + 1)}>
            <span>Continue</span>
            <ArrowRight size={14} />
          </button>
        ) : (
          <button className="nav-btn primary finish" onClick={handleFinish}>
            <Zap size={14} />
            <span>Launch Bite</span>
          </button>
        )}
      </div>
    </div>
  );
}
