#!/usr/bin/env bash
# remote: 2'50"
HOST="-n rabbit@stage"
for i in $(seq 0 99); do
  /usr/local/opt/rabbitmq/sbin/rabbitmqctl $HOST --quiet purge_queue $(printf "%04d" $i)
done
