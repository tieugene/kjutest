"""Queue Sync RabbitMQ.
Powered by [pika](https://pika.readthedocs.io/en/stable/index.html)
"""
# 1. std
from typing import Optional
# 2. 3rd
import pika
# 3. local
from q import QS, QSc


# == Sync ==
class _QSR(QS):
    """Queue Sync (RabbitMQ (pika))."""
    _master: 'QSRc'  # to avoid editor inspection warning

    def __init__(self, master: 'QSRc', __id: int):
        super().__init__(master, __id)

    def open(self):
        ...

    def count(self) -> int:
        return self._master.chan.queue_declare(queue=self._q_name, passive=True).method.message_count

    def put(self, data: bytes):
        self._master.chan.basic_publish(
            exchange='',
            routing_key=self._q_name,
            body=data,
            properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
        )

    def get(self, _: bool = True) -> Optional[bytes]:
        """wait not used.
        :note: method: Optional[Basic.GetOk] has usual `.message_count`
        """
        # method, properties, body
        method, _, body = self._master.chan.basic_get(self._q_name, auto_ack=True)
        if method:  # not None?
            return body

    def get_all(self):
        while self.get():
            ...

    def close(self):
        ...

    '''
    def __get_all_freeze(self):
        """Bsd implementation (requires strict counter)"""
        count = self.count()
        # method, properties, body
        for _, __, ___ in self._master.chan.consume(self._q_name, auto_ack=True):
            count -= 1
            if not count:
                self._master.chan.cancel()
    '''


class QSRc(QSc):
    """Queue Sync RabbitMQ Container."""
    title: str = "Queue Sync (RabbitMQ (pika))"
    _child_cls = _QSR
    __host: str
    __conn: pika.BlockingConnection
    chan: pika.adapters.blocking_connection.BlockingChannel

    def __init__(self, host: str = ''):  # '' == 'localhost'
        super().__init__()
        self.__host = host

    def open(self, count: int):
        super().open(count)
        self.__conn = pika.BlockingConnection(pika.ConnectionParameters(host=self.__host))
        self.chan = self.__conn.channel()
        self.chan.confirm_delivery()  # publish confirm
        self.chan.basic_qos(prefetch_count=1)  # get by 1

    def close(self):
        self.chan.close()
        self.__conn.close()
