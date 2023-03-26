W_COUNT = 1000  # prod: 1000
Q_COUNT = 100   # prod: 100
MSG_COUNT = 10  # prod: 1000
R_COUNT = Q_COUNT
MSG_LEN = 128
MSG = b'\x00' * MSG_LEN
# short: 1000 writers @ 100 queues = 10 w/q x 10 msgs = 100 queues x 100 msgs = 10k msgs
# prod:  1000 writers @ 100 queues = 10 w/q x 1k msgs = 100 queues x 10k msgs = 1M msgs
