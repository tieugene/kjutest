# Notes

## Resume:
- stdlib: exactly good, but not persistent
- ~~`persistqueue`: slow write, buggy~~, handy
- `pika`: slow write/fast read, steady, handy
- `aiomrq`: fast, steady, ~~stupid~~ simple
- ~~`aio-pika`: slow read, fallable, handy~~

## RQ memo:
- default exchange == routing key
- routing key != queue
- connection timeout not depend on activity, &asymp;20 min
- Resume:

## Dependencies:

gmr/pamqp -> {gmr/rabbitpy,gmr/aiorabbit}
gmr/pamqp -> mosquito/aiormq -> mosquito/aio-pika

## QARx tests:

- 1 conn/1 chan == 1 conn/N chan == N conn/N chan (but last can fail)
- sequenced slower than bulk for 3..4 times

## Tests

20230325, macOS, 1k writers @ 100 queues &times;&hellip;

### 'Low' profile:

&hellip;&times; 10 msg (10k msg total)

Type| Time | Note
----|-----:|------
QSM |    0 | stdlib
QSD |    0 | `queuelib`
QSD2|  5…5 | `persistqueue`, bulk read
QSR |33…36 | `pika`
QAM |    0 | stdlib
QAR1| 6…14 | `qiomrq`
QAR2| 7…21 | `aio-pika`

### 'Mid' profile:

&hellip;&times; 100 msg (100k msg total)

Type| Time,s| Note
----|------:|------
QSM |     0 | stdlib
QSD |   1…1 | `queuelib`
QSD2| 51…51 | `persistqueue`, bulk read
QSR |408…450| `pika`
QAM |   2…2 | stdlib
QAR1|80…255 | `qiomrq`
QAR2|116…t/o[^t]| `aio-pika`

### 'High' profile:

&hellip;&times; 1000 msg (1000k msg total)

Type| Time,s  | Note
----|--------:|------
QSM |       0 | stdlib
QSD |    8…13 | `queuelib`
QSD2|  630…640| `persistqueue`, bulk read
QSR |4489…4957| `pika`
QAM |   17…18 | stdlib
QAR1|1101…2234| `qiomrq`
QAR2|1265…t/o| `aio-pika`

### Local/Remote

(Short, s)

Type| Local | Remote
----|------:|--------:
QSR | 33…40 | 781…1147
QAR1|  8…20 |   11…402
QAR2|  8…27 |  14…fail

## Linux:

(Mid)

note: `Default tempdir '/tmp/tmpv4p3vdhy' is not on the same filesystem with queue path '_d2sd/0000',defaulting to '_d2sd/0000'.`
note: something strange w/ rabbit if not in `/var/lib`:
`/usr/sbin/rabbitmqctl: строка 47: cd: /var/lib/rabbitmq: Отказано в доступе`

Type| Time,s  | Note
----|--------:|------
QSM |       0 | stdlib
QSD |       0 | `queuelib`
QSD2|   45…45 | `persistqueue`, bulk read
QSR | &infin; | `pika`
QAM |     1…1 | stdlib
QAR1| 352…394 | `qiomrq`
QAR2| 360…418 | `aio-pika`

## Create queues

```py
import pika
conn = pika.BlockingConnection(pika.ConnectionParameters(host='<host>'))
chan = conn.channel()
[chan.queue_declare(queue=f"{i:04d}", durable=True) for i in range(100)]
chan.close()
conn.close()
```

[^t]: `exceptions.TimeoutError()`
