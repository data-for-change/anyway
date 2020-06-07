#!/bin/sh

set -e
set -x

if [ -z "${GDRIVE_FILE_ID}" ]; then
    echo missing GDRIVE_FILE_ID env var for DB restore
    exit 1
fi
export DB_DUMP_PATH=`mktemp`.pgdump
export GDRIVE_URL="https://drive.google.com/uc?id="
python3 /download_dump.py
pg_restore -Fc "$DB_DUMP_PATH" -d "$POSTGRES_DB" --no-owner
