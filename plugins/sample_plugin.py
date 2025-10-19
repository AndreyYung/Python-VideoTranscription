from app.plugin_base import PluginBase
from PyQt6.QtWidgets import QMessageBox
from pathlib import Path
import os

class SamplePlugin(PluginBase):
    name = "Cleanup Plugin"
    version = "1.0"

    def on_load(self):
        super().on_load()

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

    def on_unload(self):
        super().on_unload()
