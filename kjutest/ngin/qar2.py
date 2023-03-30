"""Queue Async RabbitMQ #2.
Powered by [aio-pika](https://github.com/mosquito/aio-pika)
"""
import asyncio
import logging
from typing import Optional
# 2. 3rd
import aio_pika
import aio_pika.abc
# 3. local
from kjutest.ngin.base import QA, QAc
# x. const
GET_TIMEOUT = 1


class _QAR2(QA):
    """Queue Async RabbitMQ (aio_pika)."""
    _master: 'QAR2c'  # to avoid editor inspection warning
    __q: aio_pika.abc.AbstractQueue

    def __init__(self, master: 'QAR2c', __id: int):
        super().__init__(master, __id)

    async def open(self):
        self.__q = await self._master.chan.get_queue(self._q_name)

    async def count(self) -> int:
        q = await self._master.chan.get_queue(self._q_name)
        return q.declaration_result.message_count

    async def put(self, data: bytes):
        # pamqp.commands.Basic.Ack
        await self._master.chan.default_exchange.publish(
            message=aio_pika.Message(
                body=data,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=self._q_name
        )

    async def get(self, wait: bool = True) -> Optional[bytes]:
        msg: aio_pika.abc.AbstractIncomingMessage = await self.__q.get(no_ack=True, fail=False, timeout=1)
        if msg:
            return msg.body

    async def close(self):
        ...

    async def _get_all_v1(self, count: int = 0) -> int:
        """Get all packages.
        v.1: Simple (non-blocking).
        """
        __counter: int = 0
        while (await self.get()) and (count == 0 or (__counter+1) < count):
            __counter += 1
        return __counter

    async def get_all(self, count: int = 0) -> int:
        """Get all messages.
        v.2: Reference consuming (blocking)
        """
        async def __consumer(msg: aio_pika.abc.AbstractIncomingMessage):
            nonlocal count, __counter, count, __lock, __ready
            async with __lock:
                __counter += 1
                async with msg.process(ignore_processed=True):
                    if __counter < count:  # continue
                        await msg.ack()
                    elif __counter == count:  # enought
                        await self.__q.cancel(msg.consumer_tag)
                        await msg.ack()
                        __ready.set()
                    else:  # extra packages
                        await msg.reject()
                        logging.warning(f"Queue {self._q_name}: extra pkg #{__counter}")
        if count > (__real_count := await self.count()) or not count:
            count = __real_count
        if count:
            __counter: int = 0
            __lock: asyncio.Lock = asyncio.Lock()
            __ready: asyncio.Event = asyncio.Event()
            await self.__q.consume(__consumer, no_ack=False)  # -> ctag:str
            await __ready.wait()
        return count

    async def __get_all_v3_dont_use_it(self, count: int = 0) -> int:
        """Get all messages.
        v.3: Reference iteration consuming (blocking _forever_)
        Resume: феерчиеская хрень. Freeze forever
        """
        if count > (__real_count := await self.count()) or not count:
            count = __real_count
        if count:
            __counter: int = 0
            async with self.__q.iterator() as q_iter:
                async for msg in q_iter:
                    __counter += 1
                    async with msg.process(ignore_processed=True):
                        if __counter < count:  # continue
                            await msg.ack()
                        elif __counter == count:
                            await self.__q.cancel(msg.consumer_tag)
                            await msg.ack()
                        else:
                            await msg.reject()
        return count


class QAR2c(QAc):
    """RabbitMQ Async Queue Container."""
    a: bool = True
    title: str = "Queue Async (RabbitMQ (aio-pika))"
    _child_cls = _QAR2
    __host: str
    __conn: aio_pika.abc.AbstractConnection
    chan: aio_pika.abc.AbstractChannel

    def __init__(self, host: str = 'amqp://localhost'):
        super().__init__()
        self.__host = host

    async def open(self, count: int):
        await super().open(count)
        self.__conn = await aio_pika.connect(self.__host)
        self.chan = await self.__conn.channel()
        self.chan.publisher_confirms = True
        await self.chan.set_qos(prefetch_count=1)

    async def close(self):
        await self.chan.close()
        await self.__conn.close()
