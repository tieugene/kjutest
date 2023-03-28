"""Queue Sync in-Memory.
Powered by [stdlib](https://docs.python.org/3/library/queue.html)
"""
from typing import Optional, Iterator
import queue

from kjutest.ngin.base import QS, QSc


class _QSM(QS):
    """Memory Sync Queue.

    """
    __q: queue.SimpleQueue

    def __init__(self, master: 'QSMc', __id: int):
        super().__init__(master, __id)
        self.__q = queue.SimpleQueue()

    def open(self):
        ...

    def count(self) -> int:
        return self.__q.qsize()

    def put(self, data: bytes):
        self.__q.put(data)

    def get(self, wait: bool = True) -> Optional[bytes]:
        try:
            return self.__q.get(block=wait, timeout=None)
        except queue.Empty:
            return None

    def get_all(self, count: int = 0) -> int:
        __counter: int = 0
        try:
            while self.__q.get(block=False):
                __counter += 1
                if count and __counter == count:
                    break
            return __counter
        except queue.Empty:
            return __counter

    def __iter__(self) -> Iterator:
        return self

    def __next__(self) -> bytes:
        if self.__q.empty():  # not guaranied
            raise StopIteration
        return self.__q.get()

    def close(self):
        ...


class QSMc(QSc):
    """Memory Sync Queue Container."""
    a: bool = False
    title: str = "Queue Sync (Memory)"
    _child_cls = _QSM
