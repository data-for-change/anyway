#!/bin/sh

set -e

( [ "${DBRESTORE_AWS_ACCESS_KEY_ID}" == "" ] || [ "${DBRESTORE_AWS_SECRET_ACCESS_KEY}" == "" ] || [ "${DBRESTORE_AWS_BUCKET}" == "" ] ) && echo missing AWS env vars && exit 1
[ "${DBRESTORE_FILE_NAME}" == "" ] && export DBRESTORE_FILE_NAME="`date +%Y-%m-%d`_anyway_partial.pgdump"

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
  psql -f "${DBRESTORE_FILE_NAME}" &&\
  if [ "${DBRESTORE_SET_ANYWAY_PASSWORD}" != "" ]; then
    echo setting anyway role password &&\
    echo "alter role anyway with password '${DBRESTORE_SET_ANYWAY_PASSWORD}'" | psql
  fi
  [ "$?" != "0" ] && echo failed && exit 1
popd
rm -rf $TEMPDIR
