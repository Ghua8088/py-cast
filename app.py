from pytron import App
import pyperclip
from src.core.bite import Bite
from src.utils.icon_handler import get_icon_url


def main():
    app = App()
    bite = Bite(app)
    app.set_start_on_boot(True)
    app.set_window_curvature(2)
    app.set_background_material("mica")
    app.set_border_color("#00000000")  # Transparent border for better aesthetics
    app.state.clipboard = []

    @app.expose
    def search_items(query: str):
        return bite.get_results(query)

    @app.expose
    def run_item(item: dict, query: str = ""):
        return bite.execute(item, query)

    @app.expose
    def toggle_pin(item_id: str):
        return bite.toggle_pin(item_id)

    @app.expose
    def resolve_icon(path: str):
        return get_icon_url(bite, path, force=True)

    @app.expose
    def add_workflow():
        return bite.select_workflow()

    @app.expose
    def get_scratchpad():
        return bite.user_data.get("scratchpad", "")

    @app.expose
    def save_scratchpad(content):
        return bite.update_scratchpad(content)

    @app.expose
    def copy_to_clipboard(text: str):
        pyperclip.copy(text)
        return True

    @app.expose
    def get_python_scratch():
        return bite.get_python_scratch()

    @app.expose
    def save_python_scratch(code):
        return bite.save_python_scratch(code)

    @app.expose
    def run_python_scratch(code):
        return bite.run_python_scratch(code)

    @app.expose
    def promote_lab_to_workflow(name, code):
        return bite.promote_lab_to_workflow(name, code)

    @app.expose
    def send_notification(title, message):
        # Renamed from 'notify' to avoid conflicts with reserved Pytron methods
        app.system_notification(title=title, message=message)
        return True

    # Shortcut API
    @app.expose
    def add_shortcut(k, n, u):
        return bite.add_shortcut(k, n, u)

    @app.expose
    def remove_shortcut(k):
        return bite.remove_shortcut(k)

    @app.expose
    def get_user_shortcuts():
        return bite.get_user_shortcuts()

    # Snippets API
    @app.expose
    def add_snippet(n, c):
        return bite.add_snippet(n, c)

    @app.expose
    def remove_snippet(sid):
        return bite.remove_snippet(sid)

    @app.expose
    def get_user_snippets():
        return bite.get_user_snippets()

    # Path Alias API
    @app.expose
    def add_path_alias(k, p):
        return bite.add_path_alias(k, p)

    @app.expose
    def remove_path_alias(k):
        return bite.remove_path_alias(k)

    @app.expose
    def select_folder_for_alias():
        return bite.select_folder_for_alias()

    @app.expose
    def get_path_aliases():
        return bite.user_data.get("path_aliases", {})

    # Project Roots API (for GitManager)
    @app.expose
    def add_project_root(p):
        return bite.add_project_root(p)

    @app.expose
    def remove_project_root(p):
        return bite.remove_project_root(p)

    @app.expose
    def get_project_roots():
        return bite.get_project_roots()

    @app.expose
    def select_project_root():
        return bite.select_project_root()

    @app.expose
    def select_ide_path():
        return bite.select_ide_path()

    # Vault API
    @app.expose
    def vault_list():
        return bite.vault.list_credentials()

    @app.expose
    def vault_save(service, username, password):
        return bite.vault.save_credential(service, username, password)

    @app.expose
    def vault_get(service, username):
        return bite.vault.get_credential(service, username)

    @app.expose
    def vault_delete(service, username):
        return bite.vault.delete_credential(service, username)

    # --- Updater Integration ---
    from pytron.updater import Updater

    UPDATE_URL = "https://raw.githubusercontent.com/Ghua8088/Bite/main/update.json"
    updater = Updater()

    @app.expose
    def check_update():
        return updater.check(UPDATE_URL)

    @app.expose
    def install_update(info):
        def on_progress(p):
            app.emit("update_progress", p)

        return updater.download_and_install(info, on_progress)

    initial_hotkey = bite.user_data.get("settings", {}).get("global_hotkey", "Alt+B") or "Alt+B"
    current_hotkey = [initial_hotkey]

    def toggle_bite():
        if not app.windows:
            return
        win = app.windows[0]
        if win.is_visible():
            win.hide()
        else:
            win.show()

    try:
        app.shortcut_manager.register(initial_hotkey, toggle_bite)
    except Exception as e:
        print(f"Error registering global shortcut {initial_hotkey}: {e}")

    @app.expose
    def set_global_hotkey(new_combo: str):
        if not new_combo or not new_combo.strip():
            return {"success": False, "error": "Hotkey cannot be empty"}
        combo = new_combo.strip()
        try:
            if current_hotkey[0]:
                try:
                    app.shortcut_manager.unregister(current_hotkey[0])
                except Exception:
                    pass

            app.shortcut_manager.register(combo, toggle_bite)
            current_hotkey[0] = combo

            settings = bite.get_settings()
            settings["global_hotkey"] = combo
            bite.update_settings(settings)
            return {"success": True, "hotkey": combo}
        except Exception as e:
            try:
                if current_hotkey[0]:
                    app.shortcut_manager.register(current_hotkey[0], toggle_bite)
            except Exception:
                pass
            return {"success": False, "error": str(e)}

    @app.on_exit
    def shutdown():
        print("Bite Shutting Down...")

    @app.expose
    def set_window_size(w, h):
        if app.windows:
            app.windows[0].set_size(w, h)
        return True

    @app.expose
    def create_workflow(n):
        return bite.create_workflow(n)

    # Custom Tray Setup
    tray = app.setup_tray()
    tray.add_item("Toggle Bite", toggle_bite)
    tray.add_item("Settings", lambda: app.emit("show_view", "settings"))
    tray.add_separator()
    tray.add_item(
        "Documentation",
        lambda: bite._cross_platform_open("https://pytron-kit.github.io/bite"),
    )
    tray.add_item("Quit", app.quit)

    @app.expose
    def get_settings():
        return bite.get_settings()

    @app.expose
    def update_settings(s):
        return bite.update_settings(s)

    @app.expose
    def get_adaptive_theme():
        return bite.get_adaptive_theme()

    @app.expose
    def hide():
        if app.windows:
            app.windows[0].hide()
        return True

    @app.expose
    def show():
        if app.windows:
            app.windows[0].show()
        return True
    
    app.run()


if __name__ == "__main__":
    main()
