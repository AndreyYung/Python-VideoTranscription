from app.plugin_base import PluginBase
from app.plugin_interface import PluginMetadata
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from pathlib import Path


class OCRSubtitleExtractorPlugin(PluginBase):
    """Плагин для автоматического извлечения субтитров из видео с помощью OCR"""
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self._metadata = PluginMetadata(
            name="OCR Subtitle Extractor",
            version="1.0",
            description="Автоматически переключает в OCR режим и извлекает субтитры из видео",
            author="VideoTranscription Team",
            category="OCR",
            dependencies=["opencv-python", "pytesseract"],
            icon_path=None,
            guid = "123456789012"
        )

    def on_load(self) -> bool:
        if not super().on_load():
            return False
        
        # Проверяем наличие OCR зависимостей
        try:
            import cv2
            import pytesseract
        except ImportError as e:
            QMessageBox.warning(
                self.main_window,
                "OCR зависимости не установлены",
                f"Для работы этого плагина необходимо установить:\n\n"
                f"pip install opencv-python pytesseract\n\n"
                f"Также установите Tesseract OCR движок с официального сайта."
            )
            return False
        
        # Показываем информацию о плагине
        reply = QMessageBox.question(
            self.main_window,
            "OCR Subtitle Extractor",
            "Этот плагин автоматически:\n\n"
            "1. Переключит приложение в OCR режим\n"
            "2. Настроит оптимальные параметры OCR\n"
            "3. Запустит извлечение субтитров из видео\n\n"
            "Продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return False
        
        # Переключаем в OCR режим
        self.main_window.ocr_mode_radio.setChecked(True)
        self.main_window.on_processing_mode_changed()
        
        # Настраиваем оптимальные параметры
        self.main_window.ocr_engine_combo.setCurrentText("tesseract")
        self.main_window.ocr_lang_combo.setCurrentText("eng")
        
        # Пытаемся автоматически определить область субтитров
        if self.main_window.tasks:
            try:
                self.main_window.auto_detect_subtitle_region()
                self.main_window.log_message("info", "OCR плагин: Область субтитров автоматически определена")
            except Exception as e:
                self.main_window.log_message("warning", f"OCR плагин: Не удалось автоматически определить область субтитров: {e}")
        
        # Сохраняем настройки
        self.main_window.save_settings()
        
        self.main_window.log_message("info", "OCR плагин: Режим OCR активирован и настроен")
        
        return True

    def on_unload(self) -> bool:
        self.main_window.log_message("info", "OCR плагин: Выгружается...")
        return super().on_unload()
