#!/usr/bin/env python3
"""Message queue (MQ) tests.
- Sync/async
- RabbitMQ-/disk-/memory-based.
- K(10) queues × L(10..1000) writers × M(10) readers/writers × N(1...1000) messages (128 bytes)
"""
import sys
from typing import List, Tuple, Union, Dict
import time
import logging
import asyncio
# 2. 3rd
import psutil
# 3. local
# from . import ...  # not works for main.py
from const import Q_COUNT, W_COUNT, MSG_COUNT, R_COUNT, MSG
from kjutest.cli import mk_args_parser
from kjutest.ngin.q import QSc, QS, QAc, Qc
from kjutest.ngin.qsm import QSMc
from kjutest.ngin.qsd import QSDc
from kjutest.ngin.qsr1 import QSRc
from kjutest.ngin.qam import QAMc
from kjutest.ngin.qar1 import QAR1c
from kjutest.ngin.qar2 import QAR2c
# x. const
NGINS: Dict[str, Union[Qc, Tuple]] = {
    'sm': QSMc,
    'am': QAMc,
    'sd': QSDc,
    'sr': QSRc,
    'ar1': QAR1c,
    'ar2': QAR2c,
    'm': (QSMc, QAMc),  # memory
    'r': (QSRc, QAR1c, QAR2c),  # rebbit
    's': (QSMc, QSDc, QSRc),  # sync
    'a': (QAMc, QAR1c, QAR2c),  # async
    '*': (QSMc, QSDc, QSRc, QAMc, QAR1c, QAR2c)  # all
    # TODO: m, d, r
}


def _mem_used() -> int:
    """Memory used, MB"""
    return round(psutil.Process().memory_info().rss / (1 << 20))


def _title(qc: Qc):
    logging.info(f"== {qc.title} {W_COUNT} w @ {Q_COUNT} q × {MSG_COUNT} m ==")


# == Sync ==
def stest(sqc: QSc):
    """Sync test of the engine."""
    _title(sqc)
    sqc.open(Q_COUNT)
    t0 = time.time()
    # 0. create writers and readers
    w_list: List[QS] = [sqc.q(i % Q_COUNT) for i in range(W_COUNT)]  # - writers
    r_list: List[QS] = [sqc.q(i % Q_COUNT) for i in range(R_COUNT)]  # - readers
    logging.info(f"1: m={_mem_used()}, t={round(time.time() - t0, 2)}, Wrtrs: {len(w_list)}, Rdrs: {len(r_list)}")
    # 1. put
    for w in w_list:
        for _ in range(MSG_COUNT):
            w.put(MSG)
    m_count = [sqc.q(i).count() for i in range(Q_COUNT)]
    s_count = sum(m_count)
    logging.info(f"2: m={_mem_used()}, t={round(time.time() - t0, 2)}, msgs={s_count}")
    # if s_count:
    #    print("Msgs: {m_count}")
    # 2. get
    for r in r_list:
        r.get_all()
        # for _ in r:
        #    ...
    # x. the end
    m_count = [sqc.q(i).count() for i in range(Q_COUNT)]
    s_count = sum(m_count)
    logging.info(f"3: m={_mem_used()}, t={round(time.time() - t0, 2)}, msgs={s_count}")
    if s_count:
        print(f"Msgs: {m_count}")
    sqc.close()


# == async ==
async def atest(aqc: QAc, bulk_tx=True):
    """Async.
    :todo: bulk_rx=True
    """

    async def __counters() -> Tuple[int]:
        __qs = await asyncio.gather(*[aqc.q(i) for i in range(Q_COUNT)])
        __count = await asyncio.gather(*[__q.count() for __q in __qs])
        return tuple(map(int, __count))

    _title(aqc)
    await aqc.open(Q_COUNT)
    t0 = time.time()
    # 0. create writers and readers
    w_list = await asyncio.gather(*[aqc.q(i % Q_COUNT) for i in range(W_COUNT)])  # - writers
    r_list = await asyncio.gather(*[aqc.q(i % Q_COUNT) for i in range(R_COUNT)])  # - readers
    logging.info(f"1: m={_mem_used()}, t={round(time.time() - t0, 2)}, Wrtrs: {len(w_list)}, Rdrs: {len(r_list)}")
    # 1. put (MSG_COUNT times all the writers)
    for _ in range(MSG_COUNT):
        if bulk_tx:
            await asyncio.gather(*[w.put(MSG) for w in w_list])
        else:
            for w in w_list:
                await w.put(MSG)
    # RAW err
    m_count = await __counters()
    s_count = sum(m_count)
    logging.info(f"2: m={_mem_used()}, t={round(time.time() - t0, 2)}, msgs={s_count}")
    # 2. get
    await asyncio.gather(*[r.get_all() for r in r_list])
    # x. the end
    m_count = await __counters()
    s_count = sum(m_count)
    logging.info(f"3: m={_mem_used()}, t={round(time.time() - t0, 2)}, msgs={s_count}")
    if s_count:
        logging.info(f"Msgs: {m_count}")
    await aqc.close()


# == entry points ==
def smain():
    """Sync."""
    stest(QSMc())
    stest(QSDc())
    stest(QSRc())  # remote: 'hostname'


async def amain():
    """Async entry point."""
    await atest(QAMc())
    await atest(QAR1c())  # remote: 'amqp://hostname'
    await atest(QAR2c())  # remote: as above


def main():
    args = mk_args_parser(tuple(NGINS.keys())).parse_args(sys.argv[1:])
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, stream=sys.stdout)
    # TODO: uniq q list
    q_list: List[Qc] = []
    for key in args.ngin:
        value = NGINS[key]
        if not isinstance(value, tuple):
            value = (value,)
        for q in value:
            if q not in q_list:
                q_list.append(q)
    # Go
    loop = asyncio.get_event_loop()
    for q in q_list:
        if q.a:
            loop.run_until_complete(atest(q()))
        else:
            stest(q())
    loop.close()
    # smain()
    # asyncio.run(amain())


if __name__ == '__main__':
    main()
