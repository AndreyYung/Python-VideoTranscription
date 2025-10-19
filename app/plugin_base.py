class PluginBase:
    name = "Unnamed Plugin"
    version = "1.0"

    def __init__(self, main_window):
        self.main_window = main_window

    def on_load(self):
        print(f"[PLUGIN] {self.name} v{self.version} загружен")

    def on_unload(self):
        print(f"[PLUGIN] {self.name} выгружен")