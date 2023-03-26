"""Queue Async RabbitMQ #1.
Powered by [aiormq](https://github.com/mosquito/aiormq)
"""
from typing import Optional
# 2. 3rd
import aiormq
import aiormq.abc
# 3. local
from q import QA, QAc


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
        await self._master.chan.basic_publish(
            body=data,
            routing_key=self._q_name,
            properties=aiormq.spec.Basic.Properties(delivery_mode=2)  # 2=persistent
        )

    async def get(self, _: bool = True) -> Optional[bytes]:
        """:note: wait not used."""
        if rsp := await self._master.chan.basic_get(self._q_name, no_ack=True):
            return rsp.body

    async def get_all(self):
        while await self.get():
            ...

    async def close(self):
        ...


class QAR1c(QAc):
    """Queue Async RabbitMQ (aiormq) Container."""
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
