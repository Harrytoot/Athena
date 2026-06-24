from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PluginMeta:
    name: str
    version: str
    description: str = ""


class PluginBase(ABC):
    meta: PluginMeta

    @abstractmethod
    async def initialize(self):
        ...

    @abstractmethod
    async def shutdown(self):
        ...
