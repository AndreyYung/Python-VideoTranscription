from app.plugin_base import PluginBase
from PyQt6.QtWidgets import QMessageBox
from pathlib import Path

class CountVideoFilesPlugin(PluginBase):
    name = "Count Video Files"
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

        video_extensions = [".mp4", ".mkv", ".avi", ".mov"]
        video_files = [f for f in output_path.iterdir() if f.suffix.lower() in video_extensions]

        QMessageBox.information(
            self.main_window,
            "Видео файлы",
            f"В папке '{output_dir}' найдено {len(video_files)} видео файлов."
        )
        self.main_window.log_message("info", f"Плагин: Найдено {len(video_files)} видео файлов.")

    def on_unload(self):
        super().on_unload()
