import { useState, useEffect } from 'react';
import pytron from 'pytron-client';
import { Lock, Key, Copy, Trash2, Eye, EyeOff, Plus } from 'lucide-react';

export default function VaultSection() {
    const [credentials, setCredentials] = useState([]);
    const [newCred, setNewCred] = useState({ service: '', username: '', password: '' });
    const [showPassword, setShowPassword] = useState({});
    const [revealedPasswords, setRevealedPasswords] = useState({});

    useEffect(() => {
        loadCredentials();
    }, []);

    const loadCredentials = async () => {
        const creds = await pytron.vault_list();
        setCredentials(creds || []);
    };

    const handleSave = async () => {
        if (!newCred.service || !newCred.username || !newCred.password) return;
        await pytron.vault_save(newCred.service, newCred.username, newCred.password);
        setNewCred({ service: '', username: '', password: '' });
        loadCredentials();
        pytron.send_notification("Vault", "Credential saved securely.");
    };

    const handleDelete = async (service, username) => {
        await pytron.vault_delete(service, username);
        loadCredentials();
    };

    const handleCopy = async (service, username) => {
        const password = await pytron.vault_get(service, username);
        if (password) {
            pytron.copy_to_clipboard(password);
            pytron.send_notification("Vault", "Password copied to clipboard.");
        }
    };

    const toggleReveal = async (service, username) => {
        const key = `${service}:${username}`;
        if (showPassword[key]) {
            setShowPassword({ ...showPassword, [key]: false });
        } else {
            if (!revealedPasswords[key]) {
                const password = await pytron.vault_get(service, username);
                setRevealedPasswords({ ...revealedPasswords, [key]: password });
            }
            setShowPassword({ ...showPassword, [key]: true });
        }
    };

    return (
        <div className="settings-section" style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
            <div className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Lock size={16} /> Secure Vault
            </div>
            <p className="dim" style={{ fontSize: '12px', marginBottom: '12px' }}>
                Manage passwords securely using the OS Keychain/Credential Manager.
            </p>

            <div className="vault-add-form" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '8px', marginBottom: '16px' }}>
                <input
                    placeholder="Service (e.g. GitHub)"
                    value={newCred.service}
                    onChange={e => setNewCred({ ...newCred, service: e.target.value })}
                    className="st-input"
                />
                <input
                    placeholder="Username"
                    value={newCred.username}
                    onChange={e => setNewCred({ ...newCred, username: e.target.value })}
                    className="st-input"
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={newCred.password}
                    onChange={e => setNewCred({ ...newCred, password: e.target.value })}
                    className="st-input"
                />
                <button className="st-btn primary" onClick={handleSave}>
                    <Plus size={14} />
                </button>
            </div>

            <div className="vault-list" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {credentials.map((cred, idx) => {
                    const key = `${cred.service}:${cred.username}`;
                    const isRevealed = showPassword[key];
                    const passwordValue = revealedPasswords[key] || '••••••••';

                    return (
                        <div key={idx} className="st-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px', background: 'var(--bg-secondary)', borderRadius: '6px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <span style={{ fontWeight: '600', fontSize: '13px' }}>{cred.service}</span>
                                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{cred.username}</span>
                            </div>
                            
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                {isRevealed && <span style={{ fontFamily: 'monospace', fontSize: '12px', background: 'var(--bg)', padding: '2px 6px', borderRadius: '4px' }}>{passwordValue}</span>}
                                
                                <button className="icon-btn" onClick={() => toggleReveal(cred.service, cred.username)} title={isRevealed ? "Hide" : "Show"}>
                                    {isRevealed ? <EyeOff size={14} /> : <Eye size={14} />}
                                </button>
                                <button className="icon-btn" onClick={() => handleCopy(cred.service, cred.username)} title="Copy Password">
                                    <Copy size={14} />
                                </button>
                                <button className="icon-btn danger" onClick={() => handleDelete(cred.service, cred.username)} title="Delete">
                                    <Trash2 size={14} />
                                </button>
                            </div>
                        </div>
                    );
                })}
                {credentials.length === 0 && <div className="dim" style={{ textAlign: 'center', padding: '20px', fontSize: '13px' }}>Vault is empty.</div>}
            </div>
        </div>
    );
}

