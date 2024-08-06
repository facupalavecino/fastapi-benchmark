from abc import ABC, abstractmethod
from typing import Dict


class BaseLlm(ABC):
    @abstractmethod
    def get_story(self, topic: str) -> Dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def stream_story(self, topic: str):
        raise NotImplementedError
