from app.plugin_base import PluginBase
from app.plugin_interface import PluginMetadata
from PyQt6.QtWidgets import QMessageBox
from pathlib import Path
import os

class SamplePlugin(PluginBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        self._metadata = PluginMetadata(
            name="Cleanup Plugin",
            version="1.0",
            description="Плагин для очистки .txt файлов в папке сохранения",
            author="VideoTranscription Team",
            category="Утилиты",
            guid="550e8400-e29b-41d4-a716-446655440001"
        )

    def on_load(self) -> bool:
        if not super().on_load():
            return False

        output_dir = self.main_window.config.get("output_dir")
        if not output_dir:
            self.main_window.log_message("warning", "Плагин: Папка для сохранения не выбрана.")
            return

        output_path = Path(output_dir)
        if not output_path.exists():
            self.main_window.log_message("warning", f"Плагин: Папка {output_dir} не существует.")
            return

        # Диалоговое окно для подтверждения удаления
        reply = QMessageBox.question(
            self.main_window,
            "Удаление файлов",
            "Удалить все .txt файлы в папке для сохранения?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            deleted_files = 0
            for file in output_path.glob("*.txt"):
                try:
                    file.unlink()
                    deleted_files += 1
                except Exception as e:
                    self.main_window.log_message("error", f"Ошибка удаления {file.name}: {e}")

            self.main_window.log_message("info", f"Плагин: Удалено {deleted_files} .txt файлов из {output_dir}.")
        else:
            self.main_window.log_message("info", "Плагин: Удаление файлов отменено пользователем.")
        
        return True

    def on_unload(self) -> bool:
        return super().on_unload()
