#!/bin/sh

set -e
set -x

if [ "$RESTORE_DB" == "TRUE" ]; then
    echo "******DEV Env - PostgreSQL initialisation******"
    pg_restore -Fc "$DB_DUMP_PATH" -d "$POSTGRES_DB" --no-owner
else
    echo "Not DEV environment, not restoring db"
fi

