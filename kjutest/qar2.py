"""Queue Async RabbitMQ #2.
Powered by [aio-pika](https://github.com/mosquito/aio-pika)
"""
from typing import Optional
# 2. 3rd
import aio_pika
import aio_pika.abc
# 3. local
from q import QA, QAc
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

    async def get_all(self):
        while await self.get():
            ...

    async def close(self):
        ...

    '''
    async def __get_all_freeze(self):
        async with self.__q.iterator() as q_iter:
            # FIXME: Cancel consuming after __aexit__
            async for msg in q_iter:
                async with msg.process():
                    print(f"Msg of {self._q_name}")
                    # if msg.count == 0: break
    '''


class QAR2c(QAc):
    """RabbitMQ Async Queue Container."""
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
