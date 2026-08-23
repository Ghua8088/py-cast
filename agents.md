# Agent Guide
This project is built with **Pytron-kit**, a multi-engine desktop framework.
## Optimizations
- **Packaging Efficiency:** Use granular imports to minimize bundle size (crucial for `pytron package`).
  - `from numpy import *` (Bad - bloats binary)
  - `import numpy as np` (Okay, but full lib)
  - `from numpy import array` (Good - targeted inclusion)
- **Lazy Loading:** Import heavy libraries *inside* exposed functions if they aren't needed at startup. This keeps the initial launch under 1s.
- **Async & Threading:** Exposed functions are powered by `asyncio`. For CPU-intensive tasks, use `run_in_thread=True` (default) to keep the UI responsive.
- **IPC Batching:** To avoid latency, batch multiple backend updates into one `dispatch()` call rather than emitting many small events.
- **State Management:** Pytron's reactive state is optimized; direct updates to `app.state` only trigger re-renders for the specific affected components.
    
## API Documentation (Flat API)
Access these via `app` in Python or `pytron` in JS.

### 1. App Lifecycle & Windows
- `run()`: Starts the application.
- `quit()`: Terminates the application.
- - `create_window(**kwargs)`: Creates a new window. Not required for single-window apps.
- `show()` / `hide()`: Toggle visibility of all windows.

### 2. IPC & Event Bus
- **Calls:** `pytron.method_name(args)` in JS calls `@app.expose` in Python.
- **Python -> JS Events:** Use `app.dispatch(event, data)`. 
  - Handle in JS: `pytron.on('event', (data) => { ... })`
- **JS -> Python Events:** Use `pytron.emit(event, data)`. 
  - Handle in Python: `@app.listen('event') def my_handler(data): ...`

### 3. Native UI & Dialogs
- `dialog_open_file(title, path, types)`: Native file picker.
- `dialog_save_file(title, path, name, types)`: Native save picker.
- `dialog_open_folder(title, path)`: Native folder picker.
- `message_box(title, msg, style)`: Native OS alert.
- `notify(title, msg)`: System notifications.

### 4. Aesthetics (Windows 11)
- `set_window_curvature(pref)`: 2 for Rounded, 1 for Square.
- `set_background_material(mat)`: 'mica', 'acrylic', 'tabbed', 'none'.
- `set_border_color(hex)`: Set window border color (e.g., "#333333").

### 5. OS & Integration
- `shortcut(combo, func)`: Register global hotkeys.
- `on_exit(func)`: Cleanup hook on app close.
- `on_file_drop(func)`: Hook for drag-and-drop onto window.
- `open_external(url)`: Open link in default browser.
- `copy_to_clipboard(text)` / `get_clipboard_text()`.
- `store_set(key, val)` / `store_get(key)`: Persistent storage.

## CLI Reference
Run these from the project root.
- `pytron help`: Shows this help message.
- `pytron run`: Starts the app. Use `--dev` for hot-reload.
- `pytron install`: Installs Python and Frontend dependencies.
- `pytron install <package>`: Install a specific Python package (important for packaging).
- `pytron frontend <cmd>`: Run JS commands (e.g., `run build`).
- `pytron build-frontend frontend`: Manually triggers the JS build.
- `pytron package`: Bundles the app into a standalone executable.
- `pytron doctor`: Checks for missing system dependencies.
- `pytron plugin [install|list|create]`: Manages Pytron plugins.

## Agent Strategy
- Use the `pytron-client` npm package for the bridge.
- All JS calls are `async`. Always `await pytron.method_name()`.
- Use `app.state.variable_name` in Python for reactive state; automatically updates frontend.
- Use `pytron.state.variable_name` in JS to access/observe these variables.
- Use the `pytron-ui` npm package for high-quality UI elements.
- Check `settings.json` for engine/window defaults.