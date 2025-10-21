import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from queue import Queue, Empty
from datetime import timedelta

from PyQt6.QtCore import QThread, pyqtSignal
import srt
from moviepy.editor import VideoFileClip

from .models import TranscriptionTask

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


class VideoOCRWorker(QThread):
    """Воркер для извлечения субтитров из видео с использованием OCR"""
    
    progress_updated = pyqtSignal(str, int)
    task_completed = pyqtSignal(str, str)
    task_failed = pyqtSignal(str, str)
    log_message = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.tasks_queue = Queue()
        self._is_running = True
        self._is_processing_paused = False
        self.easyocr_reader = None
        
    def add_task(self, task: TranscriptionTask):
        self.tasks_queue.put(task)
        
    def stop_processing(self):
        self._is_processing_paused = True
        self.clear_queue()
        
    def resume_processing(self):
        self._is_processing_paused = False
        
    def clear_queue(self):
        with self.tasks_queue.mutex:
            self.tasks_queue.queue.clear()
    
    def _detect_subtitle_region(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Автоматическое обнаружение области субтитров"""
        height, width = frame.shape[:2]
        
        # Обычно субтитры находятся в нижней части экрана
        # Берем нижние 20% кадра
        roi_height = int(height * 0.2)
        roi = frame[height - roi_height:, :]
        
        # Конвертируем в grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Применяем пороговую обработку для выделения текста
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Находим контуры
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
            
        # Находим наибольший контур (скорее всего это субтитры)
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Добавляем отступы
        padding = 10
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(width - x, w + 2 * padding)
        h = min(roi_height - y, h + 2 * padding)
        
        # Возвращаем координаты относительно всего кадра
        return (x, height - roi_height + y, w, h)
    
    def _preprocess_frame(self, frame: np.ndarray, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """Предобработка кадра для улучшения OCR"""
        if region:
            x, y, w, h = region
            frame = frame[y:y+h, x:x+w]
        
        # Конвертируем в grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Увеличиваем контрастность
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Применяем фильтр для уменьшения шума
        denoised = cv2.medianBlur(enhanced, 3)
        
        # Бинаризация
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Морфологические операции для очистки
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def _extract_text_tesseract(self, frame: np.ndarray, language: str) -> str:
        """Извлечение текста с помощью Tesseract"""
        if not TESSERACT_AVAILABLE:
            raise ImportError("Tesseract не установлен. Установите: pip install pytesseract")
        
        # Конфигурация Tesseract для лучшего распознавания субтитров
        config = '--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;:()[]{}"\'- '
        
        text = pytesseract.image_to_string(frame, lang=language, config=config)
        return text.strip()
    
    def _extract_text_easyocr(self, frame: np.ndarray, language: str) -> str:
        """Извлечение текста с помощью EasyOCR"""
        if not EASYOCR_AVAILABLE:
            raise ImportError("EasyOCR не установлен. Установите: pip install easyocr")
        
        # Инициализируем reader если нужно
        if self.easyocr_reader is None:
            # Маппинг языков
            lang_map = {
                'eng': 'en',
                'rus': 'ru',
                'deu': 'de',
                'fra': 'fr',
                'spa': 'es',
                'ita': 'it'
            }
            ocr_lang = lang_map.get(language, 'en')
            self.easyocr_reader = easyocr.Reader([ocr_lang], gpu=False)
        
        results = self.easyocr_reader.readtext(frame)
        
        # Объединяем все найденные тексты
        texts = [result[1] for result in results if result[2] > 0.5]  # threshold 0.5
        return ' '.join(texts).strip()
    
    def _extract_subtitles_from_video(self, task: TranscriptionTask) -> List[Dict]:
        """Извлечение субтитров из видео"""
        video_path = task.video_path
        self.log_message.emit("info", f"Начало OCR обработки: {video_path.name}")
        
        # Открываем видео
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Не удалось открыть видео: {video_path}")
        
        # Получаем информацию о видео
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        self.log_message.emit("info", f"Видео: {total_frames} кадров, {fps:.2f} FPS, {duration:.2f} сек")
        
        # Определяем область субтитров
        subtitle_region = task.subtitle_region
        if not subtitle_region:
            # Пытаемся автоматически обнаружить область субтитров
            ret, frame = cap.read()
            if ret:
                subtitle_region = self._detect_subtitle_region(frame)
                if subtitle_region:
                    self.log_message.emit("info", f"Автоматически обнаружена область субтитров: {subtitle_region}")
                else:
                    self.log_message.emit("warning", "Не удалось автоматически обнаружить область субтитров, используем весь кадр")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Возвращаемся к началу
        
        # Извлекаем текст из кадров
        subtitles = []
        frame_interval = max(1, int(fps / 2))  # Обрабатываем каждый второй кадр (или реже)
        last_text = ""
        current_start = 0.0
        
        for frame_num in range(0, total_frames, frame_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Предобработка кадра
            processed_frame = self._preprocess_frame(frame, subtitle_region)
            
            # Извлечение текста
            try:
                if task.ocr_engine == "tesseract":
                    text = self._extract_text_tesseract(processed_frame, task.ocr_language)
                elif task.ocr_engine == "easyocr":
                    text = self._extract_text_easyocr(processed_frame, task.ocr_language)
                else:
                    raise ValueError(f"Неподдерживаемый OCR движок: {task.ocr_engine}")
                
                # Если текст изменился, создаем новый субтитр
                if text and text != last_text and len(text) > 2:
                    if last_text:  # Завершаем предыдущий субтитр
                        subtitles.append({
                            'start': current_start,
                            'end': frame_num / fps,
                            'text': last_text
                        })
                    
                    current_start = frame_num / fps
                    last_text = text
                    
            except Exception as e:
                self.log_message.emit("warning", f"Ошибка OCR на кадре {frame_num}: {e}")
                continue
            
            # Обновляем прогресс
            progress = int((frame_num / total_frames) * 80)  # 80% для извлечения
            self.progress_updated.emit(task.task_id, progress)
        
        # Добавляем последний субтитр
        if last_text:
            subtitles.append({
                'start': current_start,
                'end': duration,
                'text': last_text
            })
        
        cap.release()
        self.log_message.emit("info", f"Извлечено {len(subtitles)} субтитров")
        return subtitles
    
    def _save_as_srt(self, segments: List[Dict], output_path: Path):
        """Сохранение субтитров в формате SRT"""
        srt_segments = [
            srt.Subtitle(
                index=i,
                start=timedelta(seconds=seg['start']),
                end=timedelta(seconds=seg['end']),
                content=seg['text'].strip()
            )
            for i, seg in enumerate(segments, 1)
        ]
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt.compose(srt_segments))
    
    def _save_as_txt(self, segments: List[Dict], output_path: Path):
        """Сохранение субтитров в формате TXT"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for segment in segments:
                f.write(segment['text'].strip() + '\n')
    
    def _process_task(self, task: TranscriptionTask):
        """Обработка задачи OCR"""
        try:
            self.log_message.emit("info", f"Начало OCR задачи для: {task.video_path.name}")
            self.progress_updated.emit(task.task_id, 5)
            
            # Проверяем доступность OCR движка
            if task.ocr_engine == "tesseract" and not TESSERACT_AVAILABLE:
                raise ImportError("Tesseract не установлен. Установите: pip install pytesseract")
            elif task.ocr_engine == "easyocr" and not EASYOCR_AVAILABLE:
                raise ImportError("EasyOCR не установлен. Установите: pip install easyocr")
            
            self.progress_updated.emit(task.task_id, 10)
            
            # Извлекаем субтитры
            subtitles = self._extract_subtitles_from_video(task)
            
            self.progress_updated.emit(task.task_id, 85)
            
            # Сохраняем результат
            output_name = task.video_path.stem
            output_path = task.output_dir / f"{output_name}_ocr.{task.output_format}"
            
            if task.output_format == "srt":
                self._save_as_srt(subtitles, output_path)
            else:
                self._save_as_txt(subtitles, output_path)
            
            self.progress_updated.emit(task.task_id, 100)
            self.task_completed.emit(task.task_id, str(output_path))
            self.log_message.emit("success", f"OCR задача завершена для: {task.video_path.name}")
            
        except Exception as e:
            self.task_failed.emit(task.task_id, str(e))
            self.log_message.emit("error", f"Ошибка OCR задачи для {task.video_path.name}: {e}")
    
    def run(self):
        """Основной цикл воркера"""
        while self._is_running:
            if not self._is_processing_paused:
                try:
                    task = self.tasks_queue.get(timeout=0.1)
                    self._process_task(task)
                    self.tasks_queue.task_done()
                except Empty:
                    self.msleep(100)
            else:
                self.msleep(200)
    
    def stop(self):
        """Остановка воркера"""
        self._is_running = False
        self.clear_queue()


