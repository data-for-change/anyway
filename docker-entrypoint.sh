#!/bin/bash

RETRIES=60

until psql $DATABASE_URL -c "select 1" > /dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
  echo "Waiting for postgres server, $((RETRIES--)) remaining attempts..."
  sleep 10
done

! alembic upgrade head && echo failed to upgrade head && sleep 10 && exit 1

exec "$@"
