import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any
from .plugin_base import PluginBase
from .plugin_interface import PluginInterface, PluginMetadata


guid_list = []


class PluginManager:
    """Менеджер плагинов для управления загрузкой и списком плагинов"""
    
    def __init__(self, main_window, plugin_dir="plugins"):
        self.main_window = main_window
        self.plugin_dir = Path(plugin_dir)
        self.loaded_plugins: Dict[str, PluginInterface] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        
        if not self.plugin_dir.exists():
            self.plugin_dir.mkdir(parents=True)

    def load_plugin(self, plugin_path: str) -> bool:
        """Загружает плагин (.py файл) во время работы"""
        try:
            plugin_path = Path(plugin_path)
            spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_path.stem] = module
            spec.loader.exec_module(module)

            # Ищем класс, унаследованный от PluginBase
            for attr in dir(module):
                obj = getattr(module, attr)
                if (isinstance(obj, type) and 
                    issubclass(obj, PluginBase) and 
                    obj is not PluginBase):
                    
                    plugin_instance = obj(self.main_window)
                    guid = str(plugin_instance.metadata.guid)
                    if guid in guid_list:
                        print("Такой плагин уже есть")
                        return False
                    # Проверяем зависимости
                    if not plugin_instance.validate_dependencies():
                        print(f"[PLUGIN ERROR] Не выполнены зависимости для {plugin_instance.metadata.name}")
                        return False
                    
                    # Загружаем плагин
                    if plugin_instance.on_load():
                        plugin_id = f"{plugin_instance.metadata.name}_{plugin_instance.metadata.version}"
                        guid = str(plugin_instance.metadata.guid)
                        if guid in guid_list:
                            print("Такой плагин уже есть")
                            return False
                        guid_list.append(guid)
                        self.loaded_plugins[plugin_id] = plugin_instance
                        self.plugin_metadata[plugin_id] = plugin_instance.metadata
                        print(f"[PLUGIN] {plugin_instance.metadata.name} v{plugin_instance.metadata.version} загружен успешно.")


                        return True
                    else:
                        print(f"[PLUGIN ERROR] Ошибка загрузки {plugin_instance.metadata.name}")
                        return False

            print(f"[PLUGIN] Не найден класс-наследник PluginBase в {plugin_path.name}")
            return False
        except Exception as e:
            print(f"[PLUGIN ERROR] {e}")
            return False

    def unload_plugin(self, plugin_id: str) -> bool:
        """Выгружает плагин по ID"""
        if plugin_id not in self.loaded_plugins:
            return False
        
        plugin = self.loaded_plugins[plugin_id]
        if plugin.on_unload():
            del self.loaded_plugins[plugin_id]
            del self.plugin_metadata[plugin_id]
            print(f"[PLUGIN] {plugin.metadata.name} выгружен.")
            return True
        return False

    def get_plugin_list(self) -> List[Dict[str, Any]]:
        """Возвращает список всех загруженных плагинов с их метаданными"""
        plugins_info = []
        for plugin_id, metadata in self.plugin_metadata.items():
            plugins_info.append({
                "id": plugin_id,
                "name": metadata.name,
                "version": metadata.version,
                "description": metadata.description,
                "author": metadata.author,
                "category": metadata.category,
                "dependencies": metadata.dependencies,
                "icon_path": metadata.icon_path,
                "guid": metadata.guid,
            })
        return plugins_info

    def get_plugins_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Возвращает список плагинов по категории"""
        return [plugin for plugin in self.get_plugin_list() if plugin["category"] == category]

    def get_categories(self) -> List[str]:
        """Возвращает список всех категорий плагинов"""
        categories = set()
        for metadata in self.plugin_metadata.values():
            categories.add(metadata.category)
        return sorted(list(categories))

    def is_plugin_loaded(self, plugin_name: str, version: str = None) -> bool:
        """Проверяет, загружен ли плагин"""
        if version:
            plugin_id = f"{plugin_name}_{version}"
            return plugin_id in self.loaded_plugins
        else:
            return any(name == plugin_name for name, _ in self.plugin_metadata.items())

    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о конкретном плагине"""
        if plugin_id in self.plugin_metadata:
            metadata = self.plugin_metadata[plugin_id]
            return {
                "id": plugin_id,
                "name": metadata.name,
                "version": metadata.version,
                "description": metadata.description,
                "author": metadata.author,
                "category": metadata.category,
                "dependencies": metadata.dependencies,
                "icon_path": metadata.icon_path
            }
        return None

    def unload_all_plugins(self):
        """Выгружает все плагины"""
        for plugin_id in list(self.loaded_plugins.keys()):
            self.unload_plugin(plugin_id)

    def run_plugin(self, plugin_id: str):
        """Запуск плагина вручную"""
        plugin = self.loaded_plugins.get(plugin_id)
        try:
            plugin.run()
            print(f"[PLUGIN] {plugin.metadata.name} запущен.")
            self.main_window.log_message("success", f"Плагин '{plugin.metadata.name}' успешно запущен.")
        except Exception as e:
            print(f"[PLUGIN ERROR] Ошибка при запуске плагина {plugin.metadata.name}: {e}")
            self.main_window.log_message("error", f"Ошибка при запуске плагина '{plugin.metadata.name}': {e}")


    def reload_plugin(self, plugin_path: str) -> bool:
        """Перезагружает плагин"""
        # Сначала находим и выгружаем старую версию, если она есть
        plugin_name = Path(plugin_path).stem
        for plugin_id in list(self.loaded_plugins.keys()):
            if plugin_id.startswith(plugin_name):
                self.unload_plugin(plugin_id)
                break
        
        # Загружаем новую версию
        return self.load_plugin(plugin_path)
