# Руководство по разработке плагинов

## Обзор

Система плагинов VideoTranscription позволяет создавать расширения для приложения с полной поддержкой метаданных, категоризации и управления жизненным циклом.

## Структура плагина

### Базовый класс

Все плагины должны наследоваться от `PluginBase` и реализовывать интерфейс `PluginInterface`.

```python
from app.plugin_base import PluginBase
from app.plugin_interface import PluginMetadata

class MyPlugin(PluginBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        self._metadata = PluginMetadata(
            name="Мой плагин",
            version="1.0",
            description="Описание функциональности плагина",
            author="Ваше имя",
            category="Категория",
            dependencies=["module1", "module2"],  # опционально
            icon_path="path/to/icon.png"  # опционально
        )

    def on_load(self) -> bool:
        if not super().on_load():
            return False
        
        # Ваша логика здесь
        return True

    def on_unload(self) -> bool:
        # Очистка ресурсов
        return super().on_unload()
```

### Метаданные плагина

#### PluginMetadata

- **name** (str): Название плагина
- **version** (str): Версия плагина
- **description** (str): Подробное описание функциональности
- **author** (str): Автор плагина
- **category** (str): Категория плагина (по умолчанию "Общие")
- **dependencies** (list[str]): Список зависимостей (опционально)
- **icon_path** (str): Путь к иконке плагина (опционально)

#### Категории плагинов

Рекомендуемые категории:
- **Общие**: Универсальные плагины
- **Анализ**: Плагины для анализа данных
- **Перевод**: Плагины для работы с переводами
- **Утилиты**: Вспомогательные инструменты
- **Экспорт**: Плагины для экспорта данных
- **Демо**: Демонстрационные плагины

### Жизненный цикл плагина

1. **Загрузка** (`on_load()`):
   - Вызывается при загрузке плагина
   - Должен возвращать `True` при успешной загрузке
   - Инициализация ресурсов, подключение к API и т.д.

2. **Выгрузка** (`on_unload()`):
   - Вызывается при выгрузке плагина
   - Должен возвращать `True` при успешной выгрузке
   - Очистка ресурсов, отключение от API и т.д.

### Доступ к основному приложению

Плагин имеет доступ к `main_window` через `self.main_window`:

```python
# Логирование
self.main_window.log_message("info", "Сообщение")

# Доступ к конфигурации
config_value = self.main_window.config.get("setting_name")

# Доступ к виджетам UI
self.main_window.translate_lang_combo.currentText()

# Доступ к воркерам
self.main_window.worker.add_task(task)
```

### Проверка зависимостей

Система автоматически проверяет зависимости плагина при загрузке:

```python
def validate_dependencies(self) -> bool:
    # Автоматическая проверка модулей из metadata.dependencies
    # Можно переопределить для кастомной логики
    return super().validate_dependencies()
```

## Примеры плагинов

### Простой плагин

```python
from app.plugin_base import PluginBase
from app.plugin_interface import PluginMetadata
from PyQt6.QtWidgets import QMessageBox

class SimplePlugin(PluginBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        self._metadata = PluginMetadata(
            name="Простой плагин",
            version="1.0",
            description="Показывает информационное сообщение",
            author="Developer",
            category="Демо"
        )

    def on_load(self) -> bool:
        if not super().on_load():
            return False
        
        QMessageBox.information(
            self.main_window,
            "Плагин загружен",
            "Простой плагин успешно загружен!"
        )
        return True

    def on_unload(self) -> bool:
        return super().on_unload()
```

### Плагин с зависимостями

```python
from app.plugin_base import PluginBase
from app.plugin_interface import PluginMetadata
import requests  # Внешняя зависимость

class WebPlugin(PluginBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        self._metadata = PluginMetadata(
            name="Web плагин",
            version="1.0",
            description="Плагин для работы с веб-API",
            author="Developer",
            category="Сеть",
            dependencies=["requests"]
        )

    def on_load(self) -> bool:
        if not super().on_load():
            return False
        
        try:
            # Проверяем доступность API
            response = requests.get("https://api.example.com/status", timeout=5)
            if response.status_code == 200:
                self.main_window.log_message("info", "Web плагин: API доступен")
            else:
                self.main_window.log_message("warning", "Web плагин: API недоступен")
        except Exception as e:
            self.main_window.log_message("error", f"Web плагин: Ошибка подключения - {e}")
        
        return True

    def on_unload(self) -> bool:
        return super().on_unload()
```

## Управление плагинами

### Загрузка плагинов

1. Через UI: кнопка "Загрузить плагин" в главном окне
2. Программно: `plugin_manager.load_plugin(path_to_plugin.py)`

### Просмотр загруженных плагинов

1. Кнопка "Список плагинов" в главном окне
2. Отображается информация о всех загруженных плагинах:
   - Название и версия
   - Описание
   - Автор
   - Категория
   - Зависимости

### Выгрузка плагинов

1. Через UI: кнопка "✕" рядом с плагином в списке
2. Программно: `plugin_manager.unload_plugin(plugin_id)`

## Рекомендации

### Хорошие практики

1. **Обработка ошибок**: Всегда используйте try-catch блоки
2. **Логирование**: Используйте `self.main_window.log_message()` для информирования пользователя
3. **Валидация**: Проверяйте наличие необходимых данных перед выполнением операций
4. **Очистка ресурсов**: Освобождайте ресурсы в `on_unload()`
5. **Версионирование**: Используйте семантическое версионирование (1.0.0)

### Что избегать

1. **Блокирующие операции**: Не выполняйте долгие операции в `on_load()`
2. **Прямое изменение UI**: Используйте сигналы и слоты для взаимодействия с UI
3. **Игнорирование зависимостей**: Всегда указывайте необходимые зависимости
4. **Неинформативные сообщения**: Используйте понятные описания и сообщения об ошибках

## Отладка

### Логи

Все сообщения плагинов записываются в журнал событий приложения:
- `info`: Информационные сообщения
- `warning`: Предупреждения
- `error`: Ошибки
- `success`: Успешные операции

### Проверка загрузки

1. Проверьте консоль на наличие ошибок загрузки
2. Убедитесь, что все зависимости установлены
3. Проверьте синтаксис Python файла

## Заключение

Система плагинов предоставляет мощный и гибкий способ расширения функциональности VideoTranscription. Следуйте этому руководству для создания качественных и надежных плагинов.
