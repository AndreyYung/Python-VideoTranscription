from app.plugin_base import PluginBase
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox
from app.translator import TranslationTask

class TranslateAllLanguagesPlugin(PluginBase):
    name = "Translate All Languages"
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

        # Получаем список доступных языков для перевода
        languages = [self.main_window.translate_lang_combo.itemText(i)
                     for i in range(self.main_window.translate_lang_combo.count())]

        # Получаем все видео-файлы
        video_extensions = [".mp4", ".mkv", ".avi", ".mov"]
        video_files = [f for f in output_path.iterdir() if f.suffix.lower() in video_extensions]

        if not video_files:
            self.main_window.log_message("info", "Плагин: Видео-файлы в папке не найдены.")
            return

        reply = QMessageBox.question(
            self.main_window,
            "Перевод видео",
            f"Сделать перевод {len(video_files)} видео на {len(languages)} языков?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            self.main_window.log_message("info", "Плагин: Перевод отменён пользователем.")
            return

        # Создаём задачи перевода
        total_tasks = 0
        for video_file in video_files:
            # Проверяем есть ли уже задача для этого видео
            task = next((t for t in self.main_window.tasks.values()
                         if t.video_path.name == video_file.name), None)
            if not task:
                # Если задача ещё не существует, создаём её
                self.main_window.log_message("warning", f"Плагин: Видео {video_file.name} ещё не обработано.")
                continue

            for lang in languages:
                if task.language == lang:
                    continue  # Не переводим на исходный язык
                translation_task = TranslationTask(
                    task_id=task.task_id,
                    source_path=task.result_path,
                    target_lang=lang,
                    use_g4f=bool(self.main_window.config.get("use_g4f_translation")),
                    g4f_model=self.main_window.config.get("g4f_model"),
                    source_lang=self.main_window.config.get("language")
                )
                self.main_window.translator.add_task(translation_task)
                total_tasks += 1

        self.main_window.log_message("info", f"Плагин: Создано {total_tasks} задач перевода.")

    def on_unload(self):
        super().on_unload()
