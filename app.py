from pytron import App
import pyperclip
from src.core.bite import Bite
from src.utils.icon_handler import get_icon_url


def main():
    app = App()
    bite = Bite(app)
    app.set_start_on_boot(True)
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

    @app.shortcut("Alt+B")
    def toggle_bite():
        if not bite.app.windows:
            return
        win = bite.app.windows[0]
        if win.is_visible():
            win.hide()
        else:
            win.show()

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

    app.run()


if __name__ == "__main__":
    main()
