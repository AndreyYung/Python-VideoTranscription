from .plugin_interface import PluginInterface, PluginMetadata


class PluginBase(PluginInterface):
    """Базовый класс для всех плагинов приложения"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self._metadata = PluginMetadata(
            name="Unnamed Plugin",
            version="1.0",
            description="Базовый плагин без описания",
            author="Unknown",
            category="Общие"
        )

    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata

    def on_load(self) -> bool:
        """Базовая реализация загрузки плагина"""
        try:
            print(f"[PLUGIN] {self.metadata.name} v{self.metadata.version} загружен")
            return True
        except Exception as e:
            print(f"[PLUGIN ERROR] Ошибка загрузки {self.metadata.name}: {e}")
            return False

    def on_unload(self) -> bool:
        """Базовая реализация выгрузки плагина"""
        try:
            print(f"[PLUGIN] {self.metadata.name} выгружен")
            return True
        except Exception as e:
            print(f"[PLUGIN ERROR] Ошибка выгрузки {self.metadata.name}: {e}")
            return False