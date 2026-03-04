export const getFileIcon = (fileName, isDir) => {
  if (isDir) return 'folder';
  const ext = fileName.toLowerCase().split('.').pop();
  const icons = {
    // Programming
    py: 'python',
    pyw: 'python',
    js: 'javascript',
    jsx: 'react',
    ts: 'typescript',
    tsx: 'react',
    html: 'html',
    css: 'css',
    json: 'file-json',
    md: 'file-text',
    sql: 'database',
    sh: 'terminal',
    bat: 'terminal',
    ps1: 'terminal',

    // Media
    png: 'image',
    jpg: 'image',
    jpeg: 'image',
    gif: 'image',
    webp: 'image',
    svg: 'image',
    mp4: 'video',
    mov: 'video',
    mkv: 'video',
    avi: 'video',
    mp3: 'music',
    wav: 'music',
    flac: 'music',

    // Documents
    pdf: 'file-digit',
    doc: 'file-text',
    docx: 'file-text',
    txt: 'file-text',
    csv: 'table',
    xlsx: 'table',
    zip: 'archive',
    rar: 'archive',
    '7z': 'archive',
    exe: 'binary',
    app: 'binary',
    dmg: 'binary'
  };

  return icons[ext] || 'file';
};
