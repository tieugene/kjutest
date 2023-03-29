#!/bin/sh
PYTHONPATH="$(realpath $(dirname $0))" python3.11 kjutest/main.py $@
