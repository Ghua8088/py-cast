import os
import sys
import importlib.util
from pathlib import Path
from typing import List, Dict

class PluginManager:
    def __init__(self, bite_instance):
        self.bite = bite_instance
        self.plugins = {}
        self.plugin_dir = self.bite.config_dir / "plugins"
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
    def load_plugins(self):
        """Loads all .py plugins from the plugin directory."""
        if not self.plugin_dir.exists():
            return

        for entry in self.plugin_dir.iterdir():
            if entry.is_dir() and (entry / "main.py").exists():
                self._load_plugin_module(entry.name, entry / "main.py")
            elif entry.suffix == ".py":
                self._load_plugin_module(entry.stem, entry)

    def _load_plugin_module(self, name, path):
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check if it has a 'register' function or 'Plugin' class
            if hasattr(module, "BitePlugin"):
                instance = module.BitePlugin(self.bite)
                self.plugins[name] = instance
                print(f"Loaded plugin: {name}")
        except Exception as e:
            print(f"Failed to load plugin {name}: {e}")

    def get_plugin_results(self, query: str) -> List[Dict]:
        all_results = []
        for name, plugin in self.plugins.items():
            try:
                if hasattr(plugin, "search"):
                    res = plugin.search(query)
                    if res:
                        for r in res:
                            r["plugin_source"] = name
                            r["cat"] = r.get("cat", "Plugins")
                        all_results.extend(res)
            except Exception as e:
                print(f"Plugin {name} search failed: {e}")
        return all_results
