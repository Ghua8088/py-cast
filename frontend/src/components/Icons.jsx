import { useState, useEffect } from 'react'
import {
  Calculator, FileText, Terminal, Scissors, Search,
  Youtube, Github, Lock, Moon, Trash2, HelpCircle,
  Code, Globe, Gamepad2, File, Folder, Clipboard,
  LayoutGrid, Settings as SettingsIcon, Link as LinkIcon,
  Volume1, Volume2, VolumeX, Book, Bot, Cpu, Zap, Cloud, Hash, Star
} from 'lucide-react'

import { getIconForFile, getIconForFolder } from 'vscode-icons-js'
import { FileIcon, defaultStyles } from 'react-file-icon'

export const LucideIcon = ({ item, size = 20 }) => {
  const name = item.name || '';
  const id = item.id?.toLowerCase() || '';
  const cat = item.cat?.toLowerCase() || '';
  const isDir = item.is_dir || (item.icon && item.icon.includes('folder'));

  // Static App Icons
  if (id === 'calc' || id === 'calc_res') return <Calculator size={size} />;
  if (id === 'note') return <FileText size={size} />;
  if (id === 'term') return <Terminal size={size} />;
  if (id === 'snip' || cat === 'snippets') return <Scissors size={size} />;
  if (cat === 'workflows') return <Zap size={size} />;
  if (id === 'settings') return <SettingsIcon size={size} />;
  if (id === 'lock') return <Lock size={size} />;
  if (id === 'sleep') return <Moon size={size} />;
  if (id === 'google' || id === 'trans' || id === 'gemini') return <Globe size={size} />;
  if (id === 'yt') return <Youtube size={size} />;
  if (id === 'gh') return <Github size={size} />;
  if (id === 'chatgpt' || id === 'bot') return <Bot size={size} />;
  if (id === 'clean' || id === 'claude') return <Zap size={size} />;
  if (id === 'empty_trash') return <Trash2 size={size} />;
  if (id === 'help') return <HelpCircle size={size} />;
  if (id === 'web_search') return <Search size={size} />;
  if (id === 'weather') return <Cloud size={size} />;
  if (id === 'dict') return <Book size={size} />;
  if (id === 'vol_up') return <Volume2 size={size} />;
  if (id === 'vol_down') return <Volume1 size={size} />;
  if (id === 'mute') return <VolumeX size={size} />;
  if (id === 'grok' || id === 'perplexity') return <Cpu size={size} />;
  if (id === 'shield-check') return <Star size={size} />; // For secure vault check
  
  if (cat === 'calc') return <Hash size={size} />;
  if (cat === 'clipboard') return <Clipboard size={size} />;

  // 1. High-Performance File Icons (react-file-icon)
  if ((cat === 'files' || cat === 'terminal' || item.path) && !isDir) {
    const parts = name.split('.');
    const extension = parts.length > 1 ? parts.pop().toLowerCase() : '';
    
    // Check if we have a native OS icon already loaded 
    if (!item.icon?.startsWith('data:image')) {
      const styles = defaultStyles[extension] || defaultStyles.txt || {};
      return (
        <div style={{ width: size, height: size, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <FileIcon 
            extension={extension} 
            color={styles.color || '#fff'}
            labelColor={styles.labelColor || styles.color || '#333'}
            glyphColor={styles.glyphColor || 'rgba(0,0,0,0.5)'}
            {...styles} 
          />
        </div>
      );
    }
  }

  // 2. Professional OS-Native Icons (Fallback/Override for EXEs/Folders)
  if (cat === 'files' || cat === 'terminal' || item.path || isDir) {
    // If we have a native icon from the backend, use it!
    if (item.icon && item.icon.startsWith('data:image')) {
      return (
        <img 
          src={item.icon} 
          alt="" 
          style={{ width: size, height: size, objectFit: 'contain', display: 'block' }}
        />
      );
    }
    
    // Fallback: Professional VSCode library logic (if native extraction didn't run)
    const iconName = isDir ? getIconForFolder(name) : getIconForFile(name);
    if (iconName) {
      const iconUrl = `https://raw.githubusercontent.com/vscode-icons/vscode-icons/master/icons/${iconName}`;
      return (
        <img 
          src={iconUrl} 
          alt="" 
          style={{ width: size, height: size, objectFit: 'contain', display: 'block' }}
          onError={(e) => {
            e.target.style.display = 'none';
          }}
        />
      );
    }
  }

  // Final Fallbacks
  if (isDir) return <Folder size={size} />;
  if (item.path) return <File size={size} />;
  if (name.toLowerCase().includes('code') || name.toLowerCase().includes('visual studio')) return <Code size={size} />;
  return <LayoutGrid size={size} />;
}

export const ItemIcon = ({ item, large = false }) => {
  const [error, setError] = useState(false);
  const size = large ? 32 : 20;

  useEffect(() => {
    setError(false);
  }, [item.id, item.icon]);

  if (item.is_img && item.icon && !error) {
    return (
      <img 
        src={item.icon} 
        alt="" 
        className={large ? "ray-icon-img-large" : "ray-icon-img"} 
        onError={() => setError(true)}
      />
    );
  }

  return <LucideIcon item={item} size={size} />;
}
