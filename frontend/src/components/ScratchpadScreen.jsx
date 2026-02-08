import { ArrowLeft } from 'lucide-react'

export default function ScratchpadScreen({ content, onSave, onBack }) {
  return (
    <div className="settings-view">
      <div className="settings-header">
        <div className="back-btn" onClick={onBack}><ArrowLeft size={18} /></div>
        <h3>Scratchpad</h3>
        <div style={{ marginLeft: 'auto', fontSize: '10px', opacity: 0.5 }}>AUTOSAVED</div>
      </div>
      <textarea 
        className="scratch-area"
        value={content}
        onChange={(e) => onSave(e.target.value)}
        autoFocus
        placeholder="Write anything..."
      />
    </div>
  )
}
