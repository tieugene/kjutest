#!/usr/bin/env python3
"""Message queue (MQ) tests.
- Sync/async
- RabbitMQ-/disk-/memory-based.
- K(10) queues × L(10..1000) writers × M(10) readers/writers × N(1...1000) messages (128 bytes)
"""
from typing import List, Tuple
import time
import platform
import logging
import asyncio
# 2. 3rd
import psutil
# 3. local
# from . import ...  # not works for main.py
from const import Q_COUNT, W_COUNT, MSG_COUNT, R_COUNT, MSG
from q import QSc, QS, QAc, Qc
from qsm import QSMC
from qsd1 import QSD1c
from qsd2 import QSD2c
from qsr1 import QSRc
from qam import QAMc
from qar1 import QAR1c
from qar2 import QAR2c

# x. const
if platform.system() == 'Darwin':
    class Logger:
        @staticmethod
        # noinspection
        def setLevel(_: int):  # pylint: disable=C0103   # noinspection PyPep8Naming (N802)
            ...

        @staticmethod
        def info(s: str):
            print(s)


    LOGGER = Logger()
else:
    LOGGER = logging.getLogger(__name__)


def _mem_used() -> int:
    """Memory used, MB"""
    return round(psutil.Process().memory_info().rss / (1 << 20))


def _title(qc: Qc):
    LOGGER.info(f"== {qc.title} {W_COUNT} w @ {Q_COUNT} q × {MSG_COUNT} m ==")


# == Sync ==
def stest(sqc: QSc):
    """Sync."""
    _title(sqc)
    sqc.open(Q_COUNT)
    t0 = time.time()
    # 0. create writers and readers
    w_list: List[QS] = [sqc.q(i % Q_COUNT) for i in range(W_COUNT)]  # - writers
    r_list: List[QS] = [sqc.q(i % Q_COUNT) for i in range(R_COUNT)]  # - readers
    LOGGER.info(f"1: m={_mem_used()}, t={round(time.time() - t0, 2)}, Wrtrs: {len(w_list)}, Rdrs: {len(r_list)}")
    # 1. put
    for w in w_list:
        for _ in range(MSG_COUNT):
            w.put(MSG)
    m_count = [sqc.q(i).count() for i in range(Q_COUNT)]
    s_count = sum(m_count)
    LOGGER.info(f"2: m={_mem_used()}, t={round(time.time() - t0, 2)}, msgs={s_count}")
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
    LOGGER.info(f"3: m={_mem_used()}, t={round(time.time() - t0, 2)}, msgs={s_count}")
    if s_count:
        print(f"Msgs: {m_count}")
    sqc.close()


# == async ==
async def atest(aqc: QAc, bulk_tx=True, bulk_rx=True):
    """Async."""

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
    LOGGER.info(f"1: m={_mem_used()}, t={round(time.time() - t0, 2)}, Wrtrs: {len(w_list)}, Rdrs: {len(r_list)}")
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
    LOGGER.info(f"2: m={_mem_used()}, t={round(time.time() - t0, 2)}, msgs={s_count}")
    # 2. get
    await asyncio.gather(*[r.get_all() for r in r_list])
    # x. the end
    m_count = await __counters()
    s_count = sum(m_count)
    LOGGER.info(f"3: m={_mem_used()}, t={round(time.time() - t0, 2)}, msgs={s_count}")
    if s_count:
        LOGGER.info(f"Msgs: {m_count}")
    await aqc.close()


# == entry points ==
def smain():
    """Sync."""
    stest(QSMC())
    stest(QSD1c())
    stest(QSD2c())
    stest(QSRc())  # remote: 'hostname'


def amain():
    """Async entry point."""

    async def __inner():
        await atest(QAMc())
        await atest(QAR1c())  # remote: 'amqp://hostname'
        await atest(QAR2c())  # remote: as above

    asyncio.run(__inner())


if __name__ == '__main__':
    LOGGER.setLevel(logging.DEBUG)
    smain()
    amain()
