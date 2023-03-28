"""Queue Async in-Memory.
Powered by [stdlib](https://docs.python.org/3/library/asyncio-queue.html)
"""
# 1. std
from typing import Optional
import asyncio
# 3. local
from kjutest.ngin.base import QAc, QA
# x. const
GET_TIMEOUT = 1  # sec


# == Async ==
class _QAM(QA):
    """Memory Async Queue."""
    __q: asyncio.Queue

    def __init__(self, master: 'QAMc', __id: int):
        super().__init__(master, __id)
        self.__q = asyncio.Queue()

    async def open(self):
        ...

    async def count(self) -> int:
        return self.__q.qsize()

    async def put(self, data: bytes):
        await self.__q.put(data)

    async def get(self, wait: bool = True) -> Optional[bytes]:
        if wait:
            return await self.__q.get()
        else:
            try:
                return self.__q.get_nowait()
            except asyncio.QueueEmpty:
                return None

    async def get_all(self, count: int = 0) -> int:
        __counter: int = 0
        while await self.get(False):
            __counter += 1
            if count and __counter == count:
                break
        return __counter

    async def close(self):
        ...


class QAMc(QAc):
    """Memory Async Queue Container."""
    a: bool = True
    title: str = "Queue Async (memory)"
    _child_cls = _QAM
