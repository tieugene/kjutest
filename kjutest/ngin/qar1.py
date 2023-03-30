"""Queue Async RabbitMQ #1.
Powered by [aiormq](https://github.com/mosquito/aiormq)
"""
import asyncio
import logging
from typing import Optional
# 2. 3rd
import aiormq
import aiormq.abc
# 3. local
from kjutest.ngin.base import QA, QAc


class _QAR1(QA):
    """Queue Async RabbitMQ (aiormq)."""
    _master: 'QAR1c'  # to avoid editor inspection warning

    def __init__(self, master: 'QAR1c', __id: int):
        super().__init__(master, __id)

    async def open(self):
        ...

    async def count(self) -> int:
        ret = await self._master.chan.queue_declare(queue=self._q_name, passive=True)
        return ret.message_count

    async def put(self, data: bytes):
        """:note: unknown sending result."""
        # pamqp.commands.Basic.Ack[.delivery_tage==1 always]
        await self._master.chan.basic_publish(
            body=data,
            routing_key=self._q_name,
            properties=aiormq.spec.Basic.Properties(delivery_mode=2)  # 2=persistent
        )

    async def get(self, _: bool = True) -> Optional[bytes]:
        """:note: wait not used."""
        if rsp := await self._master.chan.basic_get(self._q_name, no_ack=True):
            return rsp.body

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
        """Get all packages.
        v.2: Reference consiming (blocking).
        """
        async def __consumer(msg: aiormq.abc.DeliveredMessage):
            """Notes:
            - msg.routing_key == self.__q_name
            - msg.consumer_tag == basic_consume(consumer_tag=)
            - msg.message_count == None
            - msg.delivery_tag incrementing through _all_ of queues
            """
            nonlocal count, __counter, count, __lock, __ready
            async with __lock:
                __counter += 1
                if __counter < count:  # continue
                    await self._master.chan.basic_ack(delivery_tag=msg.delivery.delivery_tag)
                elif __counter == count:  # enought
                    await self._master.chan.basic_cancel(consumer_tag=msg.consumer_tag)
                    await self._master.chan.basic_ack(delivery_tag=msg.delivery.delivery_tag)
                    __ready.set()
                else:  # extra packages
                    await self._master.chan.basic_reject(delivery_tag=msg.delivery.delivery_tag)
                    logging.warning(f"Queue {self._q_name}: extra pkg #{__counter}")
        if count > (__real_count := await self.count()) or not count:
            count = __real_count
        if count:
            __counter: int = 0
            __lock: asyncio.Lock = asyncio.Lock()
            __ready: asyncio.Event = asyncio.Event()
            # defaults: no_ack=False, consumer_tag=<auto>
            await self._master.chan.basic_consume(queue=self._q_name, consumer_callback=__consumer)
            # -> pamqp.commands.Basic.ConsumeOk
            await __ready.wait()
        return count


class QAR1c(QAc):
    """Queue Async RabbitMQ (aiormq) Container."""
    a: bool = True
    title: str = "Queue Async (RabbitMQ (aiormq))"
    _child_cls = _QAR1
    __host: str
    __conn: aiormq.abc.AbstractConnection
    chan: aiormq.abc.AbstractChannel

    def __init__(self, host: str = 'amqp://localhost'):
        super().__init__()
        self.__host = host

    async def open(self, count: int):
        await super().open(count)
        self.__conn = await aiormq.connect(self.__host)
        self.chan = await self.__conn.channel()
        await self.chan.confirm_delivery()  # publish confirm?
        await self.chan.basic_qos(prefetch_count=1)  # get by 1

    async def close(self):
        await self.chan.close()
        await self.__conn.close()
