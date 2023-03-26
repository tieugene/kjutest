#!/usr/bin/env
"""Create RabbitMQ queue."""
import sys

# import aiormq
import pika


def __mk_queue(name: str) -> bool:
    conn: pika.adapters.blocking_connection.BlockingConnection = pika.BlockingConnection(pika.ConnectionParameters())
    chan: pika.adapters.blocking_connection.BlockingChannel = conn.channel()
    # meth: pika.frame.Method
    meth = chan.queue_declare(queue=name, durable=True)
    retvalue = meth.method == pika.spec.Queue.DeclareOk
    # bulk ([False]):
    # ... = [chan.queue_declare(queue=f"{i:04d}", durable=True).method == pika.spec.Queue.DeclareOk for i in range(100)]
    chan.close()
    conn.close()
    return retvalue


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[9]} <queue_name>")
        return 0
    __mk_queue(sys.argv[1])
    return 0


if __name__ == '__main__':
    sys.exit(main())

'''
# == Sync ==
conn = pika.BlockingConnection(pika.ConnectionParameters(''))
chan = conn.channel()
q = '0000'
# tx
d_mode = pika.spec.PERSISTENT_DELIVERY_MODE
chan.basic_publish(exchange='', routing_key=q, properties=pika.BasicProperties(delivery_mode=d_mode), body='\x00')
# rx
meth: tuple = chan.basic_get(q, auto_ack=True)  # pika.spec.Basic.GetOk, pika.spec.BasicProperties, bytes
'''
