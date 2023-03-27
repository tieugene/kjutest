"""CLI handling.
-v[:int] Verbosity
-t:bool=False Tx (put)
-r:bool=False Rx (get)
-q:int=1 queues (1..100)
-w:int=q writers (1..1000)
-p:int=1 Package number (0..1000; 0 for read only = all) ???
-s:int=64 package Size (1..256)
-e:StrEnum engine (sm, am, sd, sr, ar1, ar2)
[-r readers == q]
[-h:str - host of RabbitMQ
[-f:int - string format of int, "%0<f>d"]
"""
from typing import Tuple
import argparse

# x. const
DEFAULT_Q: int = 1
DEFAULT_S: int = 64


def mk_args_parser(ngin_keys: Tuple[str]) -> argparse.ArgumentParser:
    """TODO: [RTFM](https://habr.com/ru/post/466999/)."""
    parser = argparse.ArgumentParser(
        prog="kjutest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Tool to test queries",
        epilog='epilog')
    parser.add_argument('-v', '--verbose', action='store_true', help="Extended logging")
    parser.add_argument('-t', '--tx', action='store_true', help="Test package sending (put())")
    parser.add_argument('-r', '--rx', action='store_true', help="Test package receiving (get())")
    parser.add_argument('-q', '--queues', type=int, default=DEFAULT_Q, help="Queues number")
    parser.add_argument('-w', '--writers', type=int, default=0, help="Writers number (0=queues)")
    parser.add_argument('-p', '--packages', type=int, default=0, help="Packages number (0=all)")
    parser.add_argument('-s', '--size', type=int, default=DEFAULT_S, help="Packages size (1..256)")
    parser.add_argument('ngin', choices=ngin_keys, nargs='+', help="Engins to use")  # metavar='ngin',
    # parser.add_argument('host', type=str, help="POS to connect")
    # parser.add_argument('arg', nargs='?', help="Argument of some commands")
    return parser
