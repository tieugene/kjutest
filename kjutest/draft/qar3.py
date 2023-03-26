"""Queue Async RabbitMQ #2.
Powered by [aiorabbit](https://github.com/gmr/aiorabbit).
:note: not works
"""
'''
# 1. std
from typing import Optional, Union
# 2. 3rd
import aiorabbit
# 3. local
from q import QA, QAc
# x. const


class _QAR3(QA):
    """RabbitMQ Async Queue."""
    _master: 'QAR3c'  # to avoid editor inspection warning
    __q_name: str

    def __init__(self, master: 'QAR3c', __id: int):
        super().__init__(master, __id)
        self.__q_name = f"{__id:04d}"

    async def open(self):
        ...

    async def count(self) -> int:
        q = await self._master.client.queue_declare(self.__q_name, passive=True)
        return q[0]

    async def put(self, data: Union[str, bytes]):
        await self._master.client.publish(
            routing_key=self.__q_name,
            message_body=data,
            mandatory=True,
            delivery_mode=2,  # 2=persistemt
        )
        # TODO: return True if published ok

    async def get(self, wait: bool = True) -> Optional[bytes]:
        # aio_pika.abc.AbstractIncomingMessage
        msg: aiorabbit.message.Message = await self._master.client.basic_get(queue=self.__q_name, no_ack=True)
        if msg:
            return msg.body

    async def get_all(self):
        while await self.get():
            ...

    async def close(self):
        ...


class QAR3c(QAc):
    """RabbitMQ Async Queue Container."""
    title: str = "Queue Async (RabbitMQ (aiorabbit))"
    _child_cls = _QAR3
    host: str
    client: aiorabbit.client.Client

    def __init__(self, host: str = 'amqp://localhost'):
        super().__init__()
        self.host = host

    async def open(self, count: int):
        await super().open(count)
        self.client = aiorabbit.client.Client()
        await self.client.connect()
        await self.client.qos_prefetch(count=1, per_consumer=False)
        await self.client.confirm_select()

    async def close(self):
        await self.client.close()
'''
raise NotImplementedError("This module not works yet.")
