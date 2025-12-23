from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from typing import List, Dict, Any
from .styles import AppTheme


class PluginListWidget(QWidget):
    """Виджет для отображения списка загруженных плагинов"""
    plugin_unload_requested = pyqtSignal(str)  # plugin_id
    plugin_run_requested = pyqtSignal(str)  # plugin_id для запуска

    plugin_unload_requested = pyqtSignal(str)  # plugin_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Заголовок
        header_layout = QHBoxLayout()
        header_label = QLabel("Загруженные плагины")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Кнопка обновления
        refresh_btn = QPushButton("🔄")
        refresh_btn.setStyleSheet(AppTheme.SECONDARY_BUTTON_STYLE)
        refresh_btn.setToolTip("Обновить список")
        refresh_btn.setFixedSize(30, 30)
        refresh_btn.clicked.connect(self.refresh_requested)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Прокручиваемая область для плагинов
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {AppTheme.PANELS};
                border: 1px solid {AppTheme.BORDER};
                border-radius: 8px;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}
        """)
        
        # Контейнер для плагинов
        self.plugins_container = QWidget()
        self.plugins_layout = QVBoxLayout(self.plugins_container)
        self.plugins_layout.setSpacing(8)
        self.plugins_layout.setContentsMargins(10, 10, 10, 10)
        
        self.scroll_area.setWidget(self.plugins_container)
        layout.addWidget(self.scroll_area)
        
        # Сообщение о пустом списке
        self.empty_label = QLabel("Нет загруженных плагинов")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"""
            color: {AppTheme.TEXT_SECONDARY};
            font-size: 14px;
            padding: 20px;
        """)
        self.empty_label.hide()
        layout.addWidget(self.empty_label)
    
    def update_plugin_list(self, plugins: List[Dict[str, Any]]):
        """Обновляет список плагинов"""
        # Очищаем текущий список
        self.clear_plugin_list()
        
        if not plugins:
            self.empty_label.show()
            return
        
        self.empty_label.hide()
        
        # Группируем плагины по категориям
        categories = {}
        for plugin in plugins:
            category = plugin.get("category", "Общие")
            if category not in categories:
                categories[category] = []
            categories[category].append(plugin)
        
        # Добавляем плагины по категориям
        for category, category_plugins in categories.items():
            self.add_category_section(category, category_plugins)
    
    def add_category_section(self, category: str, plugins: List[Dict[str, Any]]):
        """Добавляет секцию категории с плагинами"""
        # Заголовок категории
        category_label = QLabel(category)
        category_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {AppTheme.ACCENT};
            padding: 5px 0px;
            margin-top: 10px;
        """)
        self.plugins_layout.addWidget(category_label)
        
        # Плагины в категории
        for plugin in plugins:
            plugin_widget = self.create_plugin_widget(plugin)
            self.plugins_layout.addWidget(plugin_widget)

    def create_plugin_widget(self, plugin_info: Dict[str, Any]) -> QWidget:
        """Создает виджет для отображения информации о плагине"""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {AppTheme.BACKGROUND};
                border: 1px solid {AppTheme.BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
            QWidget:hover {{
                border-color: {AppTheme.ACCENT};
            }}
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Заголовок с именем и версией
        header_layout = QHBoxLayout()

        name_label = QLabel(plugin_info["name"])
        name_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: bold;
            color: {AppTheme.TEXT_PRIMARY};
        """)
        header_layout.addWidget(name_label)

        version_label = QLabel(f"v{plugin_info['version']}")
        version_label.setStyleSheet(f"""
            font-size: 11px;
            color: {AppTheme.TEXT_SECONDARY};
            background-color: {AppTheme.PANELS};
            padding: 2px 6px;
            border-radius: 3px;
        """)
        header_layout.addWidget(version_label)

        header_layout.addStretch()

        # Кнопка запуска плагина
        run_btn = QPushButton("▶️")
        run_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppTheme.ACCENT};
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                padding: 2px 6px;
                min-width: 20px;
                max-width: 20px;
            }}
            QPushButton:hover {{
                background-color: #3399ff;
            }}
        """)
        run_btn.setToolTip("Запустить плагин")
        plugin_id = plugin_info["id"]
        run_btn.clicked.connect(lambda _, pid=plugin_id: self.plugin_run_requested.emit(pid))
        header_layout.addWidget(run_btn)

        # Кнопка выгрузки
        unload_btn = QPushButton("✕")
        unload_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppTheme.ERROR};
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                padding: 2px 6px;
                min-width: 20px;
                max-width: 20px;
            }}
            QPushButton:hover {{
                background-color: #d32f2f;
            }}
        """)
        unload_btn.setToolTip("Выгрузить плагин")
        unload_btn.clicked.connect(lambda: self.plugin_unload_requested.emit(plugin_info["id"]))
        header_layout.addWidget(unload_btn)

        layout.addLayout(header_layout)

        # Описание
        if plugin_info.get("description"):
            desc_label = QLabel(plugin_info["description"])
            desc_label.setStyleSheet(f"""
                font-size: 11px;
                color: {AppTheme.TEXT_SECONDARY};
                margin-top: 2px;
            """)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # Автор
        if plugin_info.get("author"):
            author_label = QLabel(f"Автор: {plugin_info['author']}")
            author_label.setStyleSheet(f"""
                font-size: 10px;
                color: {AppTheme.TEXT_SECONDARY};
                font-style: italic;
            """)
            layout.addWidget(author_label)

        # Зависимости
        if plugin_info.get("dependencies"):
            deps_text = ", ".join(plugin_info["dependencies"])
            deps_label = QLabel(f"Зависимости: {deps_text}")
            deps_label.setStyleSheet(f"""
                font-size: 10px;
                color: {AppTheme.WARNING};
            """)
            deps_label.setWordWrap(True)
            layout.addWidget(deps_label)

        return widget

    def clear_plugin_list(self):
        """Очищает список плагинов"""
        while self.plugins_layout.count():
            child = self.plugins_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def refresh_requested(self):
        """Сигнал для обновления списка плагинов"""
        # Этот сигнал будет подключен к методу обновления в главном окне
        pass
