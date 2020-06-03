#!/bin/sh

set -e
set -x

if [ "$RESTORE_DB" == "TRUE" ]; then
    echo "******DEV Env - PostgreSQL initialisation******"
    if [ ! -f $DB_DUMP_PATH ]
    then
        python3 /download_dump.py
    fi
    pg_restore -Fc "$DB_DUMP_PATH" -d "$POSTGRES_DB" --no-owner
else
    echo "Not DEV environment, not restoring db"
fi

