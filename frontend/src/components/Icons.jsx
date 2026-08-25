import { useState, useEffect } from 'react'
import {
  Calculator, FileText, Terminal, Scissors, Search,
  Youtube, Github, Lock, Moon, Trash2, HelpCircle,
  Code, Globe, Gamepad2, File, Folder, Clipboard,
  LayoutGrid, Settings as SettingsIcon, Link as LinkIcon,
  Volume1, Volume2, VolumeX, Book, Bot, Cpu, Zap, Cloud, Hash, Star,
  GitBranch, Sparkles, Command, CheckSquare, Compass, Shield
} from 'lucide-react'

import { getIconForFile, getIconForFolder } from 'vscode-icons-js'
import { FileIcon, defaultStyles } from 'react-file-icon'

export const LucideIcon = ({ item, icon, size = 20 }) => {
  const safeItem = typeof item === 'object' && item !== null ? item : {};
  const iconStr = typeof item === 'string' ? item : (icon || safeItem.icon || '');
  const name = safeItem.name || '';
  const id = safeItem.id?.toLowerCase() || '';
  const cat = safeItem.cat?.toLowerCase() || '';
  const isDir = safeItem.is_dir || (iconStr && iconStr.includes('folder'));

  // Git Repositories
  if (safeItem.type === 'git_repo' || cat === 'git repositories' || id.startsWith('repo_')) {
    if (iconStr === 'github' || safeItem.github_url || id.includes('github')) {
      return <Github size={size} />;
    }
    return <GitBranch size={size} />;
  }

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
  if (id === 'gh' || iconStr === 'github') return <Github size={size} />;
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
  if (id === 'shield-check') return <Shield size={size} />;
  
  // Generic Fallbacks based on icon string
  if (iconStr === 'layers') return <LayoutGrid size={size} />;
  if (iconStr === 'globe') return <Globe size={size} />;
  if (iconStr === 'terminal') return <Terminal size={size} />;
  if (iconStr === 'zap') return <Zap size={size} />;
  if (iconStr === 'folder') return <Folder size={size} />;
  if (iconStr === 'file-text') return <FileText size={size} />;
  if (iconStr === 'scissors') return <Scissors size={size} />;
  if (iconStr === 'code') return <Code size={size} />;
  if (iconStr === 'git' || iconStr === 'git-branch') return <GitBranch size={size} />;
  
  if (cat === 'calc') return <Hash size={size} />;
  if (cat === 'clipboard') return <Clipboard size={size} />;

  // 1. High-Performance File Icons (react-file-icon)
  if ((cat === 'files' || cat === 'terminal' || safeItem.path) && !isDir) {
    const parts = name.split('.');
    const extension = parts.length > 1 ? parts.pop().toLowerCase() : '';
    
    // Check if we have a native OS icon already loaded 
    if (!safeItem.icon?.startsWith('data:image')) {
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
  if (cat === 'files' || cat === 'terminal' || safeItem.path || isDir) {
    if (safeItem.icon && safeItem.icon.startsWith('data:image')) {
      return (
        <img 
          src={safeItem.icon} 
          alt="" 
          style={{ width: size, height: size, objectFit: 'contain', display: 'block' }}
        />
      );
    }
    
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
  if (safeItem.path) return <File size={size} />;
  if (name.toLowerCase().includes('code') || name.toLowerCase().includes('visual studio')) return <Code size={size} />;
  return <LayoutGrid size={size} />;
}

export const ItemIcon = ({ item, icon, large = false }) => {
  const [error, setError] = useState(false);
  const size = large ? 32 : 20;
  const safeItem = typeof item === 'object' && item !== null ? item : { icon: icon || item };

  useEffect(() => {
    setError(false);
  }, [safeItem?.id, safeItem?.icon]);

  if (safeItem?.is_img && safeItem?.icon && !error) {
    return (
      <img 
        src={safeItem.icon} 
        alt="" 
        className={large ? "ray-icon-img-large" : "ray-icon-img"} 
        onError={() => setError(true)}
      />
    );
  }

  return <LucideIcon item={safeItem} icon={icon} size={size} />;
}
