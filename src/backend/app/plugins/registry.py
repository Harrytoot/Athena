import importlib
import pkgutil
from typing import Dict, List

from app.plugins.base import PluginBase


class PluginRegistry:
    def __init__(self):
        self._plugins: Dict[str, PluginBase] = {}

    @property
    def plugins(self) -> Dict[str, PluginBase]:
        return self._plugins

    async def discover_and_load(self, package: str = "app.plugins"):
        for _, name, is_pkg in pkgutil.iter_modules([package.replace(".", "/")]):
            if is_pkg:
                continue
            module = importlib.import_module(f"{package}.{name}")
            for attr in dir(module):
                cls = getattr(module, attr)
                if isinstance(cls, type) and issubclass(cls, PluginBase) and cls is not PluginBase:
                    instance = cls()
                    await instance.initialize()
                    self._plugins[instance.meta.name] = instance

    async def shutdown_all(self):
        for plugin in self._plugins.values():
            await plugin.shutdown()
        self._plugins.clear()

    def get(self, name: str) -> PluginBase | None:
        return self._plugins.get(name)
