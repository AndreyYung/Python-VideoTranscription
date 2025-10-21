from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PluginMetadata:
    """Метаданные плагина"""
    name: str
    version: str
    description: str
    author: str
    category: str = "Общие"
    dependencies: list[str] = None
    icon_path: Optional[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class PluginInterface(ABC):
    """Базовый интерфейс для всех плагинов"""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Возвращает метаданные плагина"""
        pass
    
    @abstractmethod
    def on_load(self) -> bool:
        """
        Вызывается при загрузке плагина
        Возвращает True если плагин успешно загружен, False иначе
        """
        pass
    
    @abstractmethod
    def on_unload(self) -> bool:
        """
        Вызывается при выгрузке плагина
        Возвращает True если плагин успешно выгружен, False иначе
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Возвращает информацию о плагине в виде словаря"""
        meta = self.metadata
        return {
            "name": meta.name,
            "version": meta.version,
            "description": meta.description,
            "author": meta.author,
            "category": meta.category,
            "dependencies": meta.dependencies,
            "icon_path": meta.icon_path
        }
    
    def validate_dependencies(self) -> bool:
        """Проверяет наличие зависимостей плагина"""
        if not self.metadata.dependencies:
            return True
        
        import importlib
        for dependency in self.metadata.dependencies:
            try:
                importlib.import_module(dependency)
            except ImportError:
                return False
        return True
