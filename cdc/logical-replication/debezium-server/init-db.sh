#!/bin/bash
set -e

/home/yugabyte/bin/yugabyted start

until /home/yugabyte/bin/ysqlsh -h $(hostname) -c '\l'; do
  echo "Waiting for YSQL..."
  sleep 2
done

/home/yugabyte/bin/ysqlsh --host $(hostname) --file=/usr/local/share/init.sql

tail -f /dev/null