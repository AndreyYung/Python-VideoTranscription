from PyQt6.QtWidgets import QDialog, QRubberBand, QLabel
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtGui import QPixmap

class SubtitleAreaSelector(QDialog):
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        print("[SubtitleAreaSelector] Инициализация")

        self.setWindowTitle("Выделите область субтитров")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.label = QLabel(self)
        self.label.setPixmap(pixmap)
        self.label.resize(pixmap.size())
        self.resize(pixmap.size())

        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self.label)
        self.origin = QPoint()
        self.selected_rect = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()

    def mouseMoveEvent(self, event):
        self.rubber_band.setGeometry(
            QRect(self.origin, event.pos()).normalized()
        )

    def mouseReleaseEvent(self, event):
        self.selected_rect = self.rubber_band.geometry()
        print("[SubtitleAreaSelector] Выбрана область:", self.selected_rect)
        self.accept()  # ✅ корректно закрываем диалог
