import { ArrowLeft, Play, Save, PlusCircle } from 'lucide-react'
import { useState, useEffect } from 'react'
import pytron from 'pytron-client'

export default function PythonLabScreen({ onBack }) {
    const [code, setCode] = useState('');
    const [status, setStatus] = useState('idle'); // idle, running, success, error

    useEffect(() => {
        pytron.get_python_scratch().then(setCode);
    }, []);

    const handleRun = async () => {
        setStatus('running');
        const res = await pytron.run_python_scratch(code);
        if (res.success) {
            setStatus('success');
            pytron.notify("Python Lab", "Script executed successfully", "success");
        } else {
            setStatus('error');
            pytron.notify("Error", res.error || "Execution failed", "error");
        }
        setTimeout(() => setStatus('idle'), 2000);
    };

    const handleSave = () => {
        pytron.save_python_scratch(code);
        pytron.notify("Saved", "Python scratchpad updated", "success");
    };

    const handlePromote = async () => {
        const name = prompt("Enter a name for this workflow:");
        if (!name) return;

        const res = await pytron.promote_lab_to_workflow(name, code);
        if (res.success) {
            pytron.notify("Success", `Workflow '${name}' created!`, "success");
        } else {
            pytron.notify("Error", res.error || "Failed to create workflow", "error");
        }
    };

    return (
        <div className="settings-view python-lab">
            <div className="settings-header">
                <div className="back-btn" onClick={onBack}><ArrowLeft size={18} /></div>
                <h3>Python Lab</h3>
                <div className="lab-actions" style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
                    <button className="action-button-secondary" onClick={handleSave} title="Save to scratchpad">
                        <Save size={14} /> Save
                    </button>
                    <button className="action-button-secondary" onClick={handlePromote} title="Install as a Bite Workflow">
                        <PlusCircle size={14} /> Save as Workflow
                    </button>
                    <button className="action-button-primary" onClick={handleRun} disabled={status === 'running'}>
                        <Play size={14} fill="currentColor" /> {status === 'running' ? 'Running...' : 'Run Code'}
                    </button>
                </div>
            </div>
            <div className="code-editor-container" style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#09090b' }}>
                <textarea
                    className="scratch-area lab-editor"
                    style={{
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: '14px',
                        color: '#38bdf8',
                        background: 'transparent',
                        border: 'none',
                        padding: '24px'
                    }}
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    autoFocus
                    spellCheck="false"
                    placeholder="# Type Python here..."
                />
            </div>
            <div className="lab-footer" style={{ padding: '8px 16px', fontSize: '10px', color: 'var(--text-dim)', borderTop: '1px solid var(--border)', background: 'rgba(0,0,0,0.2)' }}>
                Tip: Code runs in a fresh terminal window. Use <code>print()</code> to see output.
            </div>
        </div>
    )
}
