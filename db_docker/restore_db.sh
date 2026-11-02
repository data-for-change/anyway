#!/bin/bash

set -e

( [ "${DBRESTORE_AWS_ACCESS_KEY_ID}" == "" ] || [ "${DBRESTORE_AWS_SECRET_ACCESS_KEY}" == "" ] || [ "${DBRESTORE_AWS_BUCKET}" == "" ] ) && echo missing AWS env vars && exit 1
[ "${DBRESTORE_FILE_NAME}" == "" ] && export DBRESTORE_FILE_NAME="`date +%Y-%m-%d`_anyway_partial.pgdump"

if [[ "$DBRESTORE_FILE_NAME" == *"partial.pgdump"* ]]; then
  DBRESTORE_SCHEMA_FILE_NAME="${DBRESTORE_FILE_NAME/partial.pgdump/partial_schema.pgdump}"
else
  DBRESTORE_SCHEMA_FILE_NAME=""
fi

# psql continues past SQL errors and still exits 0, so errors in the dump don't fail the restore.
# Some errors are expected (e.g. "ALTER ... OWNER TO <role>" for roles that exist only in production,
# or CREATE ROLE / CREATE DATABASE in full pg_dumpall dumps), but others may mean missing objects
# (e.g. a view using a PostGIS function that no longer exists). Collect psql's stderr and print
# a summary at the end, so errors are easy to spot in the container log.
DBRESTORE_PSQL_STDERR="`mktemp`"
dbrestore_psql() {
  psql -f "$1" 2>> "${DBRESTORE_PSQL_STDERR}"
}

export AWS_ACCESS_KEY_ID="${DBRESTORE_AWS_ACCESS_KEY_ID}"
export AWS_SECRET_ACCESS_KEY="${DBRESTORE_AWS_SECRET_ACCESS_KEY}"

# to create a dump from old anyway DB server:
# cd `mktemp -d`
# chown postgres .
# su postgres -c "pg_dumpall" > "`date +%Y-%m-%d`_anyway.pgdump"
# gzip *.pgdump
# s3cmd -c /etc/anyway-s3cfg put *.gz s3://anyway-db-dumps
# rm *.gz

TEMPDIR=`mktemp -d`
pushd $TEMPDIR
  aws s3 cp "s3://${DBRESTORE_AWS_BUCKET}/${DBRESTORE_FILE_NAME}.gz" ./ &&\
  gzip -d "${DBRESTORE_FILE_NAME}.gz" &&\
  dbrestore_psql "${DBRESTORE_FILE_NAME}" &&\
  if [ "${DBRESTORE_SCHEMA_FILE_NAME}" != "" ]; then
    echo restoring truncated tables schema &&\
    aws s3 cp "s3://${DBRESTORE_AWS_BUCKET}/${DBRESTORE_SCHEMA_FILE_NAME}.gz" ./ &&\
    gzip -d "${DBRESTORE_SCHEMA_FILE_NAME}.gz" &&\
    dbrestore_psql "${DBRESTORE_SCHEMA_FILE_NAME}"
  fi &&\
  if [ "${DBRESTORE_SET_ANYWAY_PASSWORD}" != "" ]; then
    echo setting anyway role password &&\
    echo "alter role anyway with password '${DBRESTORE_SET_ANYWAY_PASSWORD}'" | psql
  fi
  DBRESTORE_RC="$?"
  DBRESTORE_ERROR_COUNT="`grep -c 'ERROR:' "${DBRESTORE_PSQL_STDERR}" || true`"
  if [ -s "${DBRESTORE_PSQL_STDERR}" ]; then
    echo "----- psql messages during restore -----"
    cat "${DBRESTORE_PSQL_STDERR}"
    echo "----------------------------------------"
  fi
  if [ "${DBRESTORE_ERROR_COUNT}" != "0" ]; then
    echo "WARNING: database restore finished with ${DBRESTORE_ERROR_COUNT} SQL error(s), listed above."
    echo "WARNING: some may be expected (e.g. OWNER TO roles that exist only in production); check the rest."
  fi
  rm -f "${DBRESTORE_PSQL_STDERR}"
  [ "${DBRESTORE_RC}" != "0" ] && echo failed && exit 1
popd
rm -rf $TEMPDIR
