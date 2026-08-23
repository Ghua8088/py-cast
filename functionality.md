# Bite — Complete Functionality & Feature Reference

**Bite** is an ultra-fast, cross-platform extensible system launcher and productivity workstation built with **Pytron Kit** (Python backend + React/Vite frontend). It combines low-level OS access with modern web UI capabilities.

---

## Table of Contents
1. [Core Architecture & System Engine](#1-core-architecture--system-engine)
2. [Search & Intent Engine](#2-search--intent-engine)
3. [Intelligent File Indexer & Semantic Tagging](#3-intelligent-file-indexer--semantic-tagging)
4. [Developer & Engineering Tools](#4-developer--engineering-tools)
5. [System Management, Network & Power](#5-system-management-network--power)
6. [Security & OS Keychain Vault](#6-security--os-keychain-vault)
7. [Productivity & Everyday Utilities](#7-productivity--everyday-utilities)
8. [UI, Theming & User Experience](#8-ui-theming--user-experience)
9. [Summary of Triggers, Prefixes & Hotkeys](#9-summary-of-triggers-prefixes--hotkeys)

---

## 1. Core Architecture & System Engine

* **Pytron IPC Bridge**: High-performance, bi-directional asynchronous RPC bridge between the Python kernel (`app.py`, `src/core/`) and the React frontend (`frontend/src/`).
* **Multi-Platform Native Support**: Seamless execution across Windows, macOS (Darwin), and Linux with OS-specific fallbacks for process execution, shell commands, file reveal, and audio control.
* **Mica & Glassmorphism Windowing**: Configured with native Windows 11 Mica material, transparent borders (`#00000000`), custom curvature, and dynamic window resizing (from a 62px Zen pill up to 550px for editors/settings).
* **System Tray Integration**:
  * `Toggle Bite`: Show / Hide launcher.
  * `Settings`: Direct shortcut to user preferences.
  * `Documentation`: Web manual opener.
  * `Quit`: Clean shutdown of background threads and IPC.
* **Over-The-Air (OTA) Auto-Updater**:
  * Background remote manifest checks (`update.json`).
  * Live download progress tracking with animated UI progress bars.
  * Automatic update package installation and relaunch.
* **Auto-Start on Boot**: Native startup registry integration to launch on system boot.

---

## 2. Search & Intent Engine

* **Multi-Tiered Scoring & Category Weighting**: Intelligent rank sorting combining Pinned items, Recents, Aliases, Workflows, Files, Apps, Calculators, Dev Tools, and Web Fallbacks.
* **Bite Brain (Stream Perceptron Neural Activation)**:
  * Collects real-time environmental signals (active foreground window/process name, time of day: *morning / afternoon / evening / night*, global bias).
  * Continuously updates mathematical weight vectors with habit decay (entropy) without storing sensitive raw logs.
  * **Ghost Intent / Proactive Empty State**: When opening Bite with an empty query, the Brain predicts your most likely action and surfaces top suggestions before you even type.
* **Quicksilver-Style Mnemonic Learning**: Learns your query-to-selection habits over time, permanently boosting frequently picked results for specific queries.
* **Semantic Intent Mapping**: Natural language matching for system commands (e.g., typing `"garbage"` or `"clean"` triggers *Empty Trash*; typing `"stfu"` or `"quiet"` triggers *Mute*; typing `"louder"` triggers *Volume Up*; typing `"nap"` triggers *Sleep*).
* **AI Intelligence Previews (`ai:` / `ask:`)**: Lightweight instant search engine snippet summaries streamed into the UI without heavy binary bloat.
* **Universal Alias & Path Expansion**: Expand custom user tokens (e.g., `@work`, `@proj`) anywhere within queries, paths, or terminal commands.

---

## 3. Intelligent File Indexer & Semantic Tagging

* **SQLite WAL DB with FTS5**: Custom multi-threaded Full-Text Search database storing filesystem metadata, mtime, directory flags, and tags with automatic schema migrations.
* **Background Crawler with 24-Hour Throttle**: Indexes user roots (Desktop, Documents, Downloads, Pictures, Videos) and system drives, automatically skipping junk directories (`node_modules`, `.git`, `AppData`, `$Recycle.Bin`, `venv`, `build`, `dist`, etc.).
* **Image Dominant Color Classification (Semantic Media Search)**:
  * Inspects images (`.png`, `.jpg`, `.webp`) using Pillow and HSV color space analysis during indexing.
  * Automatically assigns color tags (`red`, `orange`, `yellow`, `green`, `blue`, `purple`, `dark`, `white`, `neutral`).
  * Searching for `"green"` or `"red"` surfaces matching images with a boosted *Semantic Search* badge.
* **Path Browsing & Tab Autocomplete**:
  * Typing a drive or path (e.g., `C:\Users\` or `/var/`) switches into instant directory browsing via `os.scandir`.
  * Pressing `Tab` autocompletes highlighted folders and files.

---

## 4. Developer & Engineering Tools

* **Terminal Command Mode (`t: <command>`)**:
  * Execute shell commands in a new terminal session with user home working directory.
  * Interactive path autofill when typing directory paths after `t:`.
* **Python Lab IDE**:
  * Built-in code editor for drafting and running Python code right inside the launcher.
  * **Save Scratchpad**: Keeps quick code snippets handy.
  * **Promote to Workflow**: Turn a Python Lab script into a permanent, autodetected Bite Workflow with a single click.
* **Python Workflows Ecosystem**:
  * Auto-discovers any `.py` script and paired `.png` icon inside `~/.config/Bite/workflows` or `%APPDATA%/Bite/workflows`.
  * Browse all workflows with `wf:` or `workflow:`.
* **Cryptographic Hash Generator (`hash <text>`)**: Instant SHA-256 and MD5 hash generation with one-click clipboard copying.
* **UUID Generator (`uuid`)**: Generates fresh UUID v4 strings.
* **Base64 Tool (`b64 <text>`)**: Auto-detects Base64 input to decode or encode strings on the fly.
* **Color Previewer (`#hex` / `rgb(...)`)**: Live visual color preview swatch with instant HEX copying.
* **Kill All Python (`clean`)**: Emergency single-click cleanup for zombie Python execution threads.

---

## 5. System Management, Network & Power

* **Live Process Manager (`kill <name>`)**:
  * Inspects running OS processes with real-time RAM usage and PID display.
  * Terminate stubborn tasks directly from the search bar.
* **Network Port Manager (`port [number]`)**:
  * Type `port 3000` or `port 8080` to find the exact PID and process name holding a socket, and kill it with `Enter`.
  * Type `port` with no number for a complete audit of all listening ports.
* **External IP Inspector (`ip`)**: One-click lookup of your public IP address with auto-copy to clipboard.
* **Restart Windows Explorer (`restart_explorer`)**: Restarts `explorer.exe` to resolve taskbar/UI glitches.
* **Audio & Volume Control (`vol_up`, `vol_down`, `mute`)**: Increment, decrement, or toggle mute directly using native OS key events.
* **Power Operations (`lock`, `sleep`)**: Quick workstation lock or system sleep without touching the mouse.
* **Empty Trash / Recycle Bin (`empty_trash`)**: System recycle bin purging via native Win32/macOS Finder API.

---

## 6. Security & OS Keychain Vault

* **OS Keychain Integration (`VaultManager`)**:
  * Stores sensitive credentials directly inside Windows Credential Manager, macOS Keychain, or Linux Secret Service via `keyring`.
  * Master PIN protection with SHA-256 hashing.
* **Secure Vault Quick Access (`env: <service>`)**:
  * Type `env:` to search credentials and copy passwords to clipboard without exposing them in plain text.
* **Vault Manager UI in Settings**:
  * Add new services, usernames, and passwords.
  * Reveal/hide passwords inline.
  * Instant copy and delete credentials.

---

## 7. Productivity & Everyday Utilities

* **Live Clipboard History Monitor**:
  * Background daemon captures text copies into history.
  * Search clipboard history via `clip <query>` or general search.
* **Multi-line Scratchpad (`scratch`)**:
  * Persistent quick-notes area that auto-saves immediately on edit.
* **Custom Text Snippets**:
  * Manage boilerplate code, email templates, and standard replies in Settings; paste them anywhere instantly.
* **Advanced Calculator & Math Engine**:
  * Arithmetic, power (`^` or `**`), percentages, trig (`sin`, `cos`, `tan`), logarithmic (`log`, `log10`), square roots (`sqrt`), and constants (`pi`, `e`).
* **Unit Converter**:
  * Length: `km`, `m`, `cm`, `mm`, `mi`, `ft`, `in`, `yd`.
  * Weight: `kg`, `g`, `mg`, `lb`, `oz`.
  * Speed: `km/h`, `mph`.
  * Temperature: `100 f in c`, `37 c in f`.
* **Live Currency Converter**:
  * Real-time exchange rate cache synced in the background (`usd`, `eur`, `gbp`, etc.) for queries like `50 eur to usd`.
* **Countdown Timers (`timer: 5m`, `t: 30s`)**:
  * Triggers an in-launcher live timer with a visual countdown badge and desktop notification upon completion.

---

## 8. UI, Theming & User Experience

* **Wallpaper Adaptive Theming (`refresh_theme`)**:
  * Extracts dominant accent colors from your active desktop wallpaper and syncs `--accent` CSS variables dynamically.
* **Zen Mode & Dynamic Resizing**:
  * Option to hide UI chrome and collapse search bar into a compact 62px floating pill until you start typing.
* **Live System Stats Pill Bar**:
  * Header displays live **BAT%**, **CPU%**, **RAM%**, and **Time** refreshed via background polling.
* **Raycast-Style Action Menu (`Tab` or `Ctrl+K`)**:
  * Contextual actions for selected items:
    * **Enter**: Execute / Open / Paste.
    * **Tab**: Pin / Unpin or autocomplete path.
    * **Ctrl + R**: Reveal in File Explorer.
    * **Ctrl + T**: Open Terminal at path.
    * **Ctrl + .**: Open folder/file in VS Code.
    * **Ctrl + C**: Copy path or content.
* **Rich Details Panel**:
  * Dynamic sidebar displaying hero icon, metadata tags, path, target URL, and text/content previews.
  * **Web Share API**: Native OS share dialog integration (`navigator.share`) or clipboard fallback.

---

## 9. Summary of Triggers, Prefixes & Hotkeys

### Global Keybindings
| Shortcut | Action |
| :--- | :--- |
| **`Alt + B`** | Toggle Bite launcher visibility |
| **`Esc`** | Close Bite / Back to Search |
| **`Enter`** | Execute selected action / Open path / Open URL |
| **`Tab`** | Autocomplete path alias or toggle Action Menu |
| **`↑ / ↓`** | Navigate search results or action menu rows |

### Search Prefixes & Commands
| Query / Prefix | Description | Example |
| :--- | :--- | :--- |
| `t: <cmd>` | Execute shell command or browse paths | `t: dir` or `t: C:\` |
| `kill <name>` | Find and terminate running process | `kill node` |
| `port <num>` | Inspect and free occupied network port | `port 3000` |
| `wf:` / `workflow:` | Browse and launch custom Python workflows | `wf: backup` |
| `env: <key>` | Query and copy passwords from Secure Vault | `env: github` |
| `clip <query>` | Search clipboard history | `clip meeting` |
| `hash <text>` | Generate SHA-256 and MD5 hashes | `hash secret123` |
| `b64 <text>` | Encode or decode Base64 strings | `b64 hello` |
| `uuid` | Generate a fresh UUID v4 | `uuid` |
| `#hex` / `rgb()` | Color preview & copy | `#38bdf8` |
| `timer: <time>` | Start a countdown timer | `timer: 25m` or `t: 45s` |
| `ai: <query>` | Ask Bite Intelligence / DuckDuckGo AI | `ai: what is rust ownership` |
| `@<alias>` | Smart folder path shortcut | `@proj\src` |
| `<math / unit>` | Instant calculation or unit/currency conversion | `(50 * 4) + 12` or `100 usd to eur` |
