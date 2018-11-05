#!/bin/bash
set -u

mv /rsa.xlsx /anyway/static/data/rsa/

sleep 2
! alembic upgrade head && sleep 2 && ! alembic upgrade head && sleep 2 \
&& ! alembic upgrade head && echo failed to upgrade head && exit 1

python main.py process cbs &&\
python main.py process rsa static/data/rsa/rsa.xlsx
[ "$?" != "0" ] && echo failed to import data && exit 1

exec "$@"
