from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import RawItem


class BaseCollector(ABC):
    @abstractmethod
    def fetch(self, limit: int) -> list[RawItem]:
        raise NotImplementedError

