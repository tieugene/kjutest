"""Queue Sync Disk-based #1.
Powered by [queuelib](https://github.com/scrapy/queuelib)
"""

from typing import Iterator

import queuelib

from q import QS, QSc


class _QSD(QS):
    """Queue Sync Disk-based ."""
    __q: queuelib.FifoDiskQueue

    def __init__(self, master: 'QSDc', __id: int):
        super().__init__(master, __id)
        self.__q = queuelib.FifoDiskQueue(f"_d1sd/{__id:04d}")

    def open(self):
        ...

    def count(self) -> int:
        return len(self.__q)

    def put(self, data: bytes):
        return self.__q.push(data)

    def get(self, wait: bool = True) -> bytes:
        return self.__q.pop()

    def get_all(self):
        while self.__q.pop():
            ...

    def __iter__(self) -> Iterator:
        return self

    def __next__(self) -> bytes:
        if item := self.__q.pop() is None:
            raise StopIteration
        return item

    def close(self):
        self.__q.close()


class QSDc(QSc):
    """Queue Sync Disk-based Container."""
    title: str = "Queue Sync (Disk (queuelib))"
    _child_cls = _QSD
