#!/bin/bash -xe

echo "******DEV Env - PostgreSQL initialisation******"

eval $(scripts/parse_url.py ${DATABASE_URL})

if [ "${X_PORT}" == "None" ]
then
    export X_PORT=5432
fi
export X_DB=${X_PATH:1}

python3 scripts/download_dump.py
chmod +rwx "${DB_DUMP_PATH}"

echo "${X_HOSTNAME}:${X_PORT}:${X_DB}:${X_USERNAME}:${X_PASSWORD}" >> "${HOME}/.pgpass"
chmod u=rw,go= "${HOME}/.pgpass"
cat ${HOME}/.pgpass
pg_restore \
    --format=custom \
    --host="${X_HOSTNAME}" \
    --port="${X_PORT}" \
    --dbname="${X_DB}" \
    --user="${X_USERNAME}" \
    --no-owner \
    --no-password \
    "${DB_DUMP_PATH}"

rm -f "${DB_DUMP_PATH}"