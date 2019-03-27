#!/bin/bash



  ! alembic upgrade head && echo failed to upgrade head && exit 1


#ls -lah /rsa.xlsx

#python main.py process cbs &&\
#python main.py process rsa /rsa.xlsx
#[ "$?" != "0" ] && echo failed to import data && exit 1

exec "$@"
