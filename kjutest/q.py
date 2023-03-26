"""Base for MQ engines."""
import asyncio
from typing import Dict, Type, Optional
from abc import ABC, abstractmethod


class QExc(RuntimeError):
    """Queue Exception."""

    def __str__(self):
        """Make string representation of exception."""
        if uplink := super().__str__():
            return f"{self.__class__.__name__}: {uplink}"
        return self.__class__.__name__


# == common ==
class Q:
    """Queue base class.
    One object per queue.
    """
    _master: 'Qc'
    _id: int

    def __init__(self, master: 'Qc', _id: int):
        self._master = master
        self._id = _id

    @property
    def _q_name(self):
        return f"{self._id:04d}"


class Qc:
    """Queue Container base class.
     Provides Qs uniqueness.
     """
    title: str = "Queue (base)"
    _child_cls: Type[Q]
    _store: Dict[int, Q]
    _count: int

    def __init__(self):
        self._store = {}
        self._count = 0


# == Sync ==
class QS(Q, ABC):
    """Queue Sync base."""

    @abstractmethod
    def open(self):
        """Open."""
        raise NotImplementedError()

    @abstractmethod
    def count(self) -> int:
        """Get messages count."""
        raise NotImplementedError()

    @abstractmethod
    def put(self, data: bytes):
        """Put message."""
        raise NotImplementedError()

    @abstractmethod
    def get(self, wait: bool = True) -> Optional[bytes]:
        """Get a message."""
        raise NotImplementedError()

    @abstractmethod
    def get_all(self):
        """Clean query."""
        raise NotImplementedError()

    @abstractmethod
    def close(self):
        raise NotImplementedError()

    def __init__(self, master: 'QSc', _id: int):
        super().__init__(master, _id)


class QSc(Qc):
    """Queue Sync Container."""
    title: str = "Queue Sync (base)"
    _child_cls: Type[QS]
    _store: Dict[int, QS]

    def __init__(self):
        super().__init__()

    def open(self, count: int):
        self._count = count

    def close(self):
        for child in self._store.values():
            child.close()
        self._store.clear()

    def q(self, i: int) -> QS:
        if i >= self._count:
            raise QExc(f"Too big num {i}")
        if i not in self._store:
            self._store[i] = self._child_cls(self, i)
            self._store[i].open()
        return self._store[i]


# == Async ==
class QA(Q, ABC):
    """Queue Async base."""
    _master: 'QAc'
    _id: int

    @abstractmethod
    async def open(self):
        raise NotImplementedError()

    @abstractmethod
    async def count(self) -> int:
        """Get messages count."""
        raise NotImplementedError()

    @abstractmethod
    async def put(self, data: bytes):
        """Put message."""
        raise NotImplementedError()

    @abstractmethod
    async def get(self, wait: bool = True) -> Optional[bytes]:
        """Get a message."""
        raise NotImplementedError()

    @abstractmethod
    async def get_all(self):
        """Get all message."""
        raise NotImplementedError()

    @abstractmethod
    async def close(self):
        raise NotImplementedError()

    def __init__(self, master: 'QAc', _id: int):
        super().__init__(master, _id)


class QAc(Qc):
    """Queue Async Container."""
    title: str = "Queue Async (base)"
    _child_cls: Type[QA]
    _store: Dict[int, QA]

    def __init__(self):
        super().__init__()

    async def open(self, count: int):
        self._count = count

    async def close(self):
        await asyncio.gather(*[child.close() for child in self._store.values()])
        self._store.clear()

    async def q(self, i: int) -> QA:
        if i >= self._count:
            raise QExc(f"Too big num {i}")
        if i not in self._store:
            self._store[i] = self._child_cls(self, i)
            await self._store[i].open()
        return self._store[i]
