"""Queue Sync RabbitMQ.
Powered by [pika](https://pika.readthedocs.io/en/stable/index.html)
"""
import logging
# 1. std
from typing import Optional
# 2. 3rd
import pika
# 3. local
from kjutest.ngin.base import QS, QSc


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

    def close(self):
        ...

    def _get_all_v1(self, count: int = 0) -> int:
        """Get all messages.
        v.1: Simple (non-blocking).
        """
        __counter: int = 0
        while self.get() and (count == 0 or (__counter+1) < count):
            __counter += 1
        return __counter

    def __consume(self, cnt_now: int, cnt_max: int, msg: pika.spec.Basic.Deliver):
        if cnt_now < cnt_max:  # continue
            self._master.chan.basic_ack(delivery_tag=msg.delivery_tag)
        elif cnt_now == cnt_max:  # enough
            self._master.chan.stop_consuming()  # TODO: add consuming_Tag
            self._master.chan.basic_ack(delivery_tag=msg.delivery_tag)
        else:  # extra
            self._master.chan.basic_reject(delivery_tag=msg.delivery_tag)
            logging.warning(f"Queue {self._q_name}: extra pkg #{cnt_now}")

    def get_all(self, count: int = 0) -> int:
        """Get all messages.
        v.2: Reference consuming (blocking).
        """
        def __consumer(
                _: pika.adapters.blocking_connection.BlockingChannel,  # channel
                meth: pika.spec.Basic.Deliver,  # method
                __: pika.spec.BasicProperties,  # properties
                ___: bytes  # body
        ):
            nonlocal count, __counter
            __counter += 1
            self.__consume(__counter, count, meth)
        if count > (__real_count := self.count()) or not count:
            count = __real_count
        if count:
            __counter: int = 0
            # note: auto_asc=True purges queue anyway
            self._master.chan.basic_consume(self._q_name, __consumer, auto_ack=False)  # -> ctag:str
            self._master.chan.start_consuming()  # wait until __consumer ends
        return count

    def _get_all_v3(self, count: int = 0) -> int:
        """Get all messages.
        v.3: Reference iteration consuming (blocking)
        """
        if count > (__real_count := self.count()) or not count:
            count = __real_count  # hack against forever __consumer; plan b: timeout
        if count:
            __counter: int = 0
            # method, properties, body
            for meth, _, ___ in self._master.chan.consume(self._q_name, auto_ack=False):
                __counter += 1
                self.__consume(__counter, count, meth)
        return count


class QSRc(QSc):
    """Queue Sync RabbitMQ Container."""
    a: bool = False
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
        # logging.getLogger("pika").setLevel(logging.WARNING)
        logging.getLogger("pika").propagate = False
        self.__conn = pika.BlockingConnection(pika.ConnectionParameters(host=self.__host))
        self.chan = self.__conn.channel()
        self.chan.confirm_delivery()  # publish confirm
        self.chan.basic_qos(prefetch_count=1)  # get by 1

    def close(self):
        self.chan.close()
        self.__conn.close()
