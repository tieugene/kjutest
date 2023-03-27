"""Queue Sync Disk-based #2.
Powered by [persistqueue](https://github.com/peter-wangxu/persist-queue).
:note: slow
"""
from typing import Iterator
# 2. 3rd
import persistqueue
# 3. local
from q import QS, QSc


class _QSD2(QS):
    """Disk-based #2 Sync Queue."""
    __q: persistqueue.Queue

    def __init__(self, master: 'QSD2c', __id: int):
        super().__init__(master, __id)
        self.__q = persistqueue.Queue(f"_d2sd/{__id:04d}")  # FIXME: use .task_done()

    def open(self):
        ...

    def count(self) -> int:
        return self.__q.qsize()

    def put(self, data: bytes):
        return self.__q.put(data)

    def get(self, wait: bool = True, save=True) -> bytes:
        item = self.__q.get(wait)
        if save:
            self.__q.task_done()
        return item

    def get_all(self):
        try:
            while self.__q.get(False):
                ...
        except persistqueue.exceptions.Empty:
            self.__q.task_done()

    def __iter__(self) -> Iterator:
        return self

    def __next__(self) -> bytes:
        if self.__q.empty():
            self.__q.task_done()
            raise StopIteration
        return self.__q.get()

    def close(self):
        ...


class QSD2c(QSc):
    """Disk-based #2 Sync Queue Container."""
    title: str = "Queue Sync (Disk (persistqueue))"
    _child_cls = _QSD2
