#!/usr/bin/env python3
"""Message queue (MQ) tests.
- Sync/async
- RabbitMQ-/disk-/memory-based.
- K(10) queues × L(10..1000) writers × M(10) readers/writers × N(1...1000) messages (128 bytes)
"""
import argparse
import sys
from dataclasses import dataclass
from typing import List, Tuple, Union, Dict
import time
import logging
import asyncio
# 2. 3rd
import psutil
# 3. local
# from . import ...  # not works for main.py
from kjutest.cli import mk_args_parser
from kjutest.ngin.base import QS, Qc, QSc, QAc
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
    'all': (QSMc, QSDc, QSRc, QAMc, QAR1c, QAR2c)  # all
}


def _mem_used() -> int:
    """Memory used, MB"""
    return round(psutil.Process().memory_info().rss / (1 << 20))


def _title(qc: Qc, args: argparse.Namespace):
    logging.info(f"== {qc.title} {args.writers or args.queues} w @ {args.queues} q × {args.packages} m ==")


# == Sync ==
def stest(sqc: QSc, args: argparse.Namespace):
    """Sync test of the engine."""
    def __sub_title(__no: int):
        __m_count = [sqc.q(__i).count() for __i in range(args.queues)]
        __s_count = sum(__m_count)
        logging.info(f"{__no}: m={_mem_used()}, t={round(time.time() - t0, 1)}, msgs={__s_count}")

    _title(sqc, args)
    msg_sample = b'\x00' * args.size
    sqc.open(args.queues)
    t0 = time.time()
    __sub_title(0)
    if args.tx:  # 1. put
        w_list: List[QS] = [sqc.q(i % args.queues) for i in range(args.writers or args.queues)]  # - writers
        # 1. put
        for w in w_list:
            for _ in range(args.packages or 1):
                w.put(msg_sample)
        __sub_title(1)
        t0 = time.time()  # reset timer
    if args.rx:  # 2. get
        r_list: List[QS] = [sqc.q(i) for i in range(args.queues)]  # - readers
        for r in r_list:
            r.get_all(0 if args.tx else args.packages)
        __sub_title(2)
    # x. the end
    sqc.close()


# == async ==
async def atest(aqc: QAc, args: argparse.Namespace, bulk_tx=True):
    """Async.
    :todo: bulk_rx=True
    """

    async def __counters() -> Tuple[int]:
        __qs = await asyncio.gather(*[aqc.q(i) for i in range(args.queues)])
        __count = await asyncio.gather(*[__q.count() for __q in __qs])
        return tuple(map(int, __count))

    async def __sub_title(__no: int):
        __m_count = await __counters()
        __s_count = sum(__m_count)
        logging.info(f"{__no}: m={_mem_used()}, t={round(time.time() - t0, 1)}, msgs={__s_count}")

    _title(aqc, args)
    msg_sample = b'\x00' * args.size
    await aqc.open(args.queues)
    t0 = time.time()
    await __sub_title(0)
    if args.tx:  # 1. put (MSG_COUNT times all the writers)
        w_list = await asyncio.gather(*[aqc.q(i % args.queues) for i in range(args.writers or args.queues)])
        for _ in range(args.packages or 1):
            if bulk_tx:
                await asyncio.gather(*[w.put(msg_sample) for w in w_list])
            else:
                for w in w_list:
                    await w.put(msg_sample)
        await __sub_title(1)
        t0 = time.time()  # reset timer
    if args.rx:  # 2. get
        r_list = await asyncio.gather(*[aqc.q(i) for i in range(args.queues)])  # - readers
        await asyncio.gather(*[r.get_all(0 if args.tx else args.packages) for r in r_list])
        await __sub_title(2)
    # x. the end
    await aqc.close()


# == entry point ==
def main():
    async def __a_stub(__q_list: List):
        for __q in __q_list:
            await atest(__q(), args)
    parser = mk_args_parser(tuple(NGINS.keys()))
    args = parser.parse_args(sys.argv[1:])
    if not (args.tx or args.rx):
        parser.error("No tx nor rx")
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
    [stest(q(), args) for q in q_list if not q.a]
    asyncio.run(__a_stub([q for q in q_list if q.a]))


if __name__ == '__main__':
    main()
