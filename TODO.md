# Kju.ToDo

- [ ] FIXME: RQ: no put() response (Solution: exchange, bind)
- [ ] Chk pkgs sent (B2n put() and get())
- [ ] Mem usage on-the-fly (stderr); timer/event
- [ ] queues maintain (CRUDL)

## RxQ:
- [ ] reconnect (or heartbeat? (`pika`, `aiormq`))
- [ ] test callbacks
- [ ] Try:
  + [ ] [python3-amqp](https://github.com/celery/py-amqp): Client library for AMQP (sync)
  + [ ] [python3-kombu](https://github.com/celery/kombu): An AMQP Messaging Framework for Python
  + [ ] [python3-uamqp](https://github.com/Azure/azure-uamqp-python): AMQP 1.0 client library for Python
  + [x] ~~python3-pamqp: AMQP 0-9-1 library~~

## Future
- [ ] automation:
  - [ ] iterator (`__iter__`/`__next__`)
  - [ ] context (`__enter__`/`__exit__`)
- [ ] QAD[c]
