# Bite: Full Feature List

Bite isn't just a simple application launcher. Built heavily upon the idea of native OS integration through Python via Pytron-Kit, it serves as an all-in-one productivity hub. 

Here is an exhaustive list of features built into Bite:

## ⚡ Core Engine
* **Ultra-Fast Spotlight UI:** A fully transparent/glassmorphic quick-entry search bar that seamlessly toggles over your existing active windows without disruption.
* **Smart Debounced Engine:** Intelligent asynchronous updates and rendering limit keyboard latency so typing *always* feels instant.
* **Multi-Platform Support:** Works beautifully natively on Windows, macOS, and Linux out-of-the-box using the same unified Python code.
* **Auto Update Mechanism:** Built-in seamless OTA updating feature pulling directly from a remote JSON manifest to provide the latest features efficiently.

## 🔍 Native Search & Navigation
* **Application Search:** Instantly locates and opens installed native apps (`.exe`, `.app`, `.desktop`), gracefully skipping system-hidden utilities.
* **Intelligent File Indexer:** Bite doesn't rely on the clunky and slow Windows OS Indexer. It uses a custom **SQLite WAL DB with FTS5** (Full Text Search). It asynchronously indexes your local storage while meticulously excluding developer garbage folders (e.g. `node_modules`, `__pycache__`, `.Trash`).
* **Path Browsing / Autofill:** Type a raw path (e.g., `C:\Users\`) or use a command and `Tab` your way through the local file hierarchy directly within the search bar.

## 🛠️ Productivity Tools
* **Live Clipboard History:** A background listener quietly records up to 20 of your most recent clipboard copies. Type `clip` or scroll to retrieve and repaste them instantly. 
* **Multi-line Scratchpad:** An isolated note-taking space reachable via a keystroke. Notes auto-save immediately. You never have to leave the launcher's UI wrapper.
* **Custom Text Snippets:** Store massive code blocks or repeated email replies inside Settings and paste them anywhere instantly.
* **Calculator & Unit Converter:** Real-time equation resolver right inside the search input. Can gracefully handle math syntax matching `(10 * 5) / 2` and conversions like `10 miles to km` or `32 fahrenheit in celsius`.

## 🧑‍💻 Developer Experience
* **Python Lab IDE:** A built-in code editor for small script testing. Run python natively inside a spawn window right from your launcher.
* **Python Workflows Ecosystem:** Bite uses pure Python for plugins. Write any valid Python script, drop it into Bite's internal `workflows` folder, and Bite will autodetect, assign it an icon, and let you run it. You can even promote scripts from the Python Lab IDE into full permanent workflows with a single hotkey!
* **Terminal Command Sub-engine:** By typing `t: ` you trigger Terminal mode. Send bash or PowerShell commands straight to your system instantly. Auto-fills local paths natively if needed.
* **Developer toolkit:** Type `hash [text]` for instant MD5/SHA256 copying. Type `uuid` to generate random UUID v4 strings instantly. Type `b64 [text]` to safely encode or decode Base64 directly against memory.
* **"Kill All Python":** A single life-saving shortcut to wipe zombie python execution threads off your RAM.

## ⚙️ System Commands & Utilities
* **Live Process Manager:** Type `kill [name]`. Bite natively reads your RAM and local processes, showing accurate PIDs and Memory Usage inline. Hitting enter terminates the task.
* **Network Port Manager:** Type `port [number]` (e.g. `port 8080`). Bite reads your live socket activity, maps the ghost service hogging the port, and kills it instantly over standard root commands without opening `netstat`.
* **Volume/Media Control:** Increase, decrease, or permanently mute system audio directly.
* **Power Controls:** Sleep, Lock PC, and restart system File Explorers directly from shortcuts.
* **Network Inspector:** One click fetching of your network's External IP out over a safe ping request. Can instantly copy back to keyboard.
* **Empty Trash Bin:** One click action to clear the local garbage without touching the mouse.

## 🌐 Extensible Routing & Links
* **Direct AI Integrations:** Dedicated prompt openers to dive directly into ChatGPT, Claude, Gemini, Grok, and Perplexity right from launch.
* **Custom Bangs / User Shortcuts:** Configure custom web URLs with variables to act as quick-search portals natively mapped to your most used websites (Google, GitHub, etc).
* **Native OS Share Hooking:** Pass contents directly from Bite's panel onto standard OS Share dialogs contextually via `navigator.share`.

## 🎨 Aesthetic & UX Options
* **Glassmorphic Render & Transitions:** Dynamic CSS micro-animations on interaction.
* **Accent Theming:** Fully map your launcher to a custom Hex string via Settings.
* **Zen Toolbar / Footer Hiding:** Option to fully strip UI cruft, focusing explicitly on the core input query until items render.
* **Pro-Class Keyboard Navitation:** Full keyboard supremacy. Tab mapping, Ctrl+C raw bypass paths, Alt-hotkeys and Action Menus explicitly structured round minimizing active mouse lifting. 
