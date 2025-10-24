from app.plugin_base import PluginBase
from app.plugin_interface import PluginMetadata
from PyQt6.QtWidgets import QMessageBox
from pathlib import Path


class ExamplePlugin(PluginBase):
    """Пример плагина с полным описанием метаданных"""
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self._metadata = PluginMetadata(
            name="Example Plugin",
            version="2.0",
            description="Демонстрационный плагин, показывающий возможности новой системы плагинов с метаданными",
            author="Development Team",
            category="Демо",
            dependencies=["PyQt6", "pathlib"],
            guid = "333444555352"
        )

    def on_load(self) -> bool:
        """Вызывается при загрузке плагина"""
        if not super().on_load():
            return False
        
        # Пример логики плагина
        output_dir = self.main_window.config.get("output_dir")
        if not output_dir:
            self.main_window.log_message("warning", "Пример плагина: Папка для сохранения не выбрана.")
            return True  # Плагин загружен, но не может выполнить свою функцию
        
        output_path = Path(output_dir)
        if not output_path.exists():
            self.main_window.log_message("warning", f"Пример плагина: Папка {output_dir} не существует.")
            return True
        
        # Подсчитываем общее количество файлов
        total_files = len(list(output_path.iterdir()))
        
        QMessageBox.information(
            self.main_window,
            "Пример плагина",
            f"Демонстрационный плагин загружен!\n\n"
            f"Папка: {output_dir}\n"
            f"Всего файлов: {total_files}\n\n"
            f"Этот плагин показывает:\n"
            f"- Метаданные (имя, версия, описание, автор)\n"
            f"- Категоризацию плагинов\n"
            f"- Проверку зависимостей\n"
            f"- Новый интерфейс плагинов"
        )
        
        self.main_window.log_message("info", f"Пример плагина: Демонстрация завершена. Найдено {total_files} файлов в {output_dir}")
        return True

    def on_unload(self) -> bool:
        """Вызывается при выгрузке плагина"""
        self.main_window.log_message("info", "Пример плагина: Выгружается...")
        return super().on_unload()




