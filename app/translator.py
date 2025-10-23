import time
from pathlib import Path
from queue import Queue, Empty

from PyQt6.QtCore import QThread, pyqtSignal
import srt

# Импортируем офлайн библиотеку для перевода
from translate import Translator


class TranslationTask(tuple):
    __slots__ = ()
    _fields = ('task_id', 'source_path', 'target_lang', 'use_g4f', 'g4f_model', 'source_lang')

    def __new__(cls, task_id: str, source_path: Path, target_lang: str, use_g4f: bool, g4f_model: str,
                source_lang: str = "auto"):
        return tuple.__new__(cls, (task_id, source_path, target_lang, use_g4f, g4f_model, source_lang))

    @property
    def task_id(self): return self[0]

    @property
    def source_path(self): return self[1]

    @property
    def target_lang(self): return self[2]

    @property
    def use_g4f(self): return self[3]

    @property
    def g4f_model(self): return self[4]

    @property
    def source_lang(self): return self[5]


class TranslationWorker(QThread):
    translation_completed = pyqtSignal(str, str)
    translation_failed = pyqtSignal(str, str)
    log_message = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.tasks_queue = Queue()
        self._is_running = True
        self.translator_cache = {}

    def add_task(self, task: TranslationTask):
        self.tasks_queue.put(task)

    def _get_translator(self, target_lang: str, source_lang: str = "auto"):
        """Получаем или создаем переводчик для языка"""
        lang_dict = {"en" : "EN", "de" : "DE", "fr" : "FR" , "es" : "ES","it": "IT", "uk":"UK" , "pl" : "PL"}
        source_lang = "RU"
        print(lang_dict[target_lang])
        new_lang = lang_dict[target_lang]
        target_lang = new_lang
        print("Исходный язык - ", source_lang)
        print("Язык перевода - ", target_lang)
        cache_key = f"{source_lang}|{target_lang}"
        if cache_key not in self.translator_cache:
            try:
                # Создаем переводчик для офлайн работы
                translator = Translator(
                    to_lang=target_lang,
                    from_lang=source_lang if source_lang != "auto" else None
                )
                self.translator_cache[cache_key] = translator
                self.log_message.emit("info", f"Создан переводчик: {source_lang} -> {target_lang}")
            except Exception as e:
                self.log_message.emit("error", f"Ошибка создания переводчика: {e}")
                raise
        return self.translator_cache[cache_key]

    def _batch_translate_offline(self, texts: list, target_lang: str, source_lang: str = "auto") -> list:
        """Офлайн перевод батча текстов"""
        if not texts:
            return []

        translator = self._get_translator(target_lang, source_lang)
        translated_texts = []

        for i, text in enumerate(texts):
            try:
                if not text.strip():
                    translated_texts.append("")
                    continue

                # Переводим текст
                translated = translator.translate(text)
                translated_texts.append(translated)

                # Логируем прогресс для больших батчей
                if len(texts) > 10 and i % 10 == 0:
                    self.log_message.emit("info", f"Переведено {i + 1}/{len(texts)} строк")

                # Небольшая задержка чтобы не перегружать систему
                time.sleep(0.05)

            except Exception as e:
                self.log_message.emit("warning", f"Ошибка перевода строки {i + 1}: {e}")
                # В случае ошибки возвращаем оригинальный текст
                translated_texts.append(text)

        return translated_texts

    def _translate_srt_offline(self, source_path: Path, target_lang: str, source_lang: str) -> Path:
        """Офлайн перевод SRT файла"""
        with open(source_path, 'r', encoding='utf-8') as f:
            subs = list(srt.parse(f.read()))

        contents = [s.content for s in subs]

        # Разбиваем на батчи для стабильности
        batch_size = 15
        translated = []

        for i in range(0, len(contents), batch_size):
            chunk = contents[i:i + batch_size]
            self.log_message.emit("info",
                                  f"Перевод батча {i // batch_size + 1}/{(len(contents) - 1) // batch_size + 1}")

            out = self._batch_translate_offline(chunk, target_lang, source_lang)
            translated.extend(out)

        # Обновляем субтитры переведенным текстом
        for s, t in zip(subs, translated):
            s.content = t

        output_path = source_path.with_name(f"{source_path.stem}_{target_lang}.srt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt.compose(subs))

        return output_path

    def _translate_txt_offline(self, source_path: Path, target_lang: str, source_lang: str) -> Path:
        """Офлайн перевод TXT файла"""
        with open(source_path, 'r', encoding='utf-8') as f:
            lines = [ln.strip() for ln in f.readlines() if ln.strip()]

        batch_size = 20
        translated = []

        for i in range(0, len(lines), batch_size):
            chunk = lines[i:i + batch_size]
            self.log_message.emit("info", f"Перевод батча {i // batch_size + 1}/{(len(lines) - 1) // batch_size + 1}")

            out = self._batch_translate_offline(chunk, target_lang, source_lang)
            translated.extend(out)

        output_path = source_path.with_name(f"{source_path.stem}_{target_lang}.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(translated))

        return output_path

    def _process_task(self, task: TranslationTask):
        """Обработка задачи перевода"""
        try:
            self.log_message.emit("info", f"Начало перевода {task.source_path.name} на '{task.target_lang}'")

            # Всегда используем офлайн перевод, игнорируем use_g4f и g4f_model
            if task.source_path.suffix.lower() == '.srt':
                result_path = self._translate_srt_offline(task.source_path, task.target_lang, task.source_lang)
            elif task.source_path.suffix.lower() == '.txt':
                result_path = self._translate_txt_offline(task.source_path, task.target_lang, task.source_lang)
            else:
                raise ValueError(f"Неподдерживаемый формат: {task.source_path.suffix}")

            self.log_message.emit("success", f"Перевод завершён: {Path(result_path).name}")
            self.translation_completed.emit(task.task_id, str(result_path))

        except Exception as e:
            self.log_message.emit("error", f"Ошибка перевода: {e}")
            self.translation_failed.emit(task.task_id, str(e))

    def run(self):
        """Основной цикл работы воркера"""
        while self._is_running:
            try:
                task = self.tasks_queue.get(timeout=0.1)
                self._process_task(task)
                self.tasks_queue.task_done()
            except Empty:
                self.msleep(100)

    def stop(self):
        """Остановка воркера"""
        self._is_running = False
        self.translator_cache.clear()