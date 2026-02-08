import { useState, useEffect } from 'react'
import {
  Calculator, FileText, Terminal, Scissors, Search,
  Youtube, Github, Lock, Moon, Trash2, HelpCircle,
  Code, Globe, Gamepad2, File, Folder, Clipboard,
  LayoutGrid, Settings as SettingsIcon, Link as LinkIcon,
  Volume1, Volume2, VolumeX, Book, Bot, Cpu, Zap, Cloud, Hash, Star
} from 'lucide-react'

export const LucideIcon = ({ item, size = 20 }) => {
  const id = item.id?.toLowerCase() || '';
  const name = item.name?.toLowerCase() || '';
  const cat = item.cat?.toLowerCase() || '';

  if (id === 'calc' || id === 'calc_res') return <Calculator size={size} />;
  if (id === 'note') return <FileText size={size} />;
  if (id === 'term') return <Terminal size={size} />;
  if (id === 'snip' || cat === 'snippets') return <Scissors size={size} />;
  if (cat === 'Workflows') return <Zap size={size} />;
  if (id === 'google' || id === 'trans' || id === 'gemini') return <Globe size={size} />;
  if (id === 'yt') return <Youtube size={size} />;
  if (id === 'gh') return <Github size={size} />;
  if (id === 'lock') return <Lock size={size} />;
  if (id === 'sleep') return <Moon size={size} />;
  if (id === 'clean' || id === 'claude') return <Zap size={size} />;
  if (id === 'empty_trash') return <Trash2 size={size} />;
  if (id === 'help') return <HelpCircle size={size} />;
  if (id === 'settings') return <SettingsIcon size={size} />;
  if (id === 'web_search') return <Search size={size} />;
  if (id === 'weather') return <Cloud size={size} />;
  if (id === 'dict') return <Book size={size} />;
  if (id === 'vol_up') return <Volume2 size={size} />;
  if (id === 'vol_down') return <Volume1 size={size} />;
  if (id === 'mute') return <VolumeX size={size} />;
  if (id === 'chatgpt') return <Bot size={size} />;
  if (id === 'grok' || id === 'perplexity') return <Cpu size={size} />;

  if (cat === 'calc') return <Hash size={size} />;
  if (cat === 'clipboard') return <Clipboard size={size} />;
  if (cat === 'custom' || cat === 'web') return <LinkIcon size={size} />;
  if (cat === 'files') {
    return (item.icon && item.icon.includes('folder')) ? <Folder size={size} /> : <File size={size} />;
  }

  if (name.includes('code') || name.includes('visual studio')) return <Code size={size} />;
  if (name.includes('game')) return <Gamepad2 size={size} />;
  
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
