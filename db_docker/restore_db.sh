#!/bin/sh

set -e
set -x

if [ "$CURR_ENV" == "DEV" ]; then
    echo "******DEV Env - PostgreSQL initialisation******"
    pg_restore -Fc "$DB_DUMP_PATH" -d "$POSTGRES_DB" --no-owner
else
    echo "Not DEV environment, not restoring db"
fi

