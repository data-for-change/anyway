#!/bin/bash


if [ "${INITIALIZE}" == "no" ]; then
  sleep 2
  ! alembic upgrade head && sleep 2 && ! alembic upgrade head && sleep 2 \
  && ! alembic upgrade head && echo failed to upgrade head && exit 1
fi  

#ls -lah /rsa.xlsx

#python main.py process cbs &&\
#python main.py process rsa /rsa.xlsx
#[ "$?" != "0" ] && echo failed to import data && exit 1

exec "$@"
