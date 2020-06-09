#!/bin/bash

export TZ=Asia/Jerusalem

( [ "${DBDUMP_AWS_ACCESS_KEY_ID}" == "" ] || [ "${DBDUMP_AWS_SECRET_ACCESS_KEY}" == "" ] ) && echo missing AWS env vars && exit 1
( [ "${DBDUMP_PASSWORD}" == "" ] || [ "${DBDUMP_HOST}" == "" ] || [ "${DBDUMP_USER}" == "" ] ) && echo missing DBDUMP env vars && exit 1

export AWS_ACCESS_KEY_ID="${DBDUMP_AWS_ACCESS_KEY_ID}"
export AWS_SECRET_ACCESS_KEY="${DBDUMP_AWS_SECRET_ACCESS_KEY}"

dumpdb() {
  PG_DUMP_ARGS="${1}"
  DUMP_FILE="${2}"
  BUCKET="${3}"
  TEMPDIR=`mktemp -d`
  pushd $TEMPDIR
    echo "Dumping into dump file: ${DUMP_FILE}"
    ! PGPASSWORD=$DBDUMP_PASSWORD $PG_DUMP_ARGS -h $DBDUMP_HOST -U $DBDUMP_USER > "${DUMP_FILE}" && echo failed to pg_dump && return 1
    echo "Zipping down the dump file"
    ! gzip "${DUMP_FILE}" && echo failed to gzip && return 1
    echo "Uploading to S3"
    ! aws s3 cp "${DUMP_FILE}.gz" "s3://${BUCKET}/" && echo failed to s3 cp && return 1
  popd
  rm -rf "${TEMPDIR}"
}

echo dumping full db &&\
dumpdb "pg_dumpall" \
       "`date +%Y-%m-%d`_${DBDUMP_S3_FILE_PREFIX}anyway.pgdump" \
       "anyway-full-db-dumps" &&\
 echo dumping partial db &&\
dumpdb "pg_dump -d anyway --no-privileges -N topology -T users -T roles -T roles_users -T locationsubscribers -T report_preferences -T general_preferences" \
       "`date +%Y-%m-%d`_${DBDUMP_S3_FILE_PREFIX}anyway_partial.pgdump" \
        "anyway-partial-db-dumps" &&\
echo Great Success && exit 0
echo Failed && exit 1
