# Notes

## Resume:

Speed of pkgs r/w, pkgs/s (localhost):

S/A| Engine     | Write | Read
---|------------|------:|------:
 S | stdlib     |&infin;|&infin;
 A | stdlib     |   75k | 1M
 S | `queuelib` |  100k | 200k
 S | `pika`     |   250 | 2000
 A | `qiomrq`   |  2000 | 3700
 A | `aio-pika` |  1500 | 2500

- stdlib: exactly good, not persistent
- `pika`: slow write/fast read, steady, handy
- `aiomrq`: fast, steady, ~~stupid~~ simple
- `aio-pika`: slower, ~~fallable~~ works, handy

## Tests

20230330, macOS, RQ: callbacks, 1k writers @ 10 queues &times;&hellip;

### 'Low' profile:

&hellip;&times; 10 msg (10k msg total)

Type| W  | R | Note
----|---:|--:|------
QSM |  0 | 0 | stdlib
QSD |  0 | 0 | `queuelib`
QSR | 34 | 5 | `pika`
QAM |  0 | 0 | stdlib
QAR1|  6 | 4 | `qiomrq`
QAR2|  6 | 4 | `aio-pika`

### 'Mid' profile:

&hellip;&times; 100 msg (100k msg total)

Type| W   | R  | Note
----|----:|---:|---
QSM |   0 |  0 | stdlib
QSD |   1 |  1 | `queuelib`
QSR | 398 | 46 | `pika`
QAM |   2 |  0 | stdlib
QAR1|  54 | 27 | `qiomrq`
QAR2|  67 | 41 | `aio-pika`

### 'Max' profile:

&hellip;&times; 1000 msg (1M msg total)

Type| W  | R | Note
----|---:|--:|---
QSM |  0 | 0 | stdlib
QSD |  9 | 5 | `queuelib`
QAM | 13 | 1 | stdlib

### Local/Remote

*TODO*

## Linux:

*TODO*

## Memo

### RQ:
- default exchange == routing key
- routing key != queue
- connection timeout not depend on activity, &asymp;20 min

### Dependencies:

gmr/pamqp -> {~~gmr/rabbitpy~~,~~gmr/aiorabbit~~}
gmr/pamqp -> mosquito/aiormq -> mosquito/aio-pika

### QARx tests:

- 1 conn/1 chan == 1 conn/N chan == N conn/N chan (but last can fail)
- sequenced slower than bulk for 3..4 times

### Create queues

```py
import pika
conn = pika.BlockingConnection(pika.ConnectionParameters())  # ([host='<host>']))
chan = conn.channel()
[chan.queue_declare(queue=str(i), durable=True) for i in range(10)]
chan.close()
conn.close()
```
