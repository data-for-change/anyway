#!/bin/bash

TRUNCATE_TABLES="users roles locationsubscribers users_to_roles users_to_organizations organization"

TRUNCATE_TABLES_EXCLUDE_ARGUMENTS=""
TRUNCATE_TABLES_INCLUDE_ARGUMENTS=""
for TABLE in $TRUNCATE_TABLES; do
  TRUNCATE_TABLES_EXCLUDE_ARGUMENTS="${TRUNCATE_TABLES_EXCLUDE_ARGUMENTS} -T ${TABLE}"
  TRUNCATE_TABLES_INCLUDE_ARGUMENTS="${TRUNCATE_TABLES_INCLUDE_ARGUMENTS} -t ${TABLE}"
done

export TZ=Asia/Jerusalem

( [ "${DBDUMP_AWS_ACCESS_KEY_ID}" == "" ] || [ "${DBDUMP_AWS_SECRET_ACCESS_KEY}" == "" ] ) && echo missing AWS env vars && exit 1
( [ "${DBDUMP_PASSWORD}" == "" ] || [ "${DBDUMP_HOST}" == "" ] || [ "${DBDUMP_USER}" == "" ] ) && echo missing DBDUMP env vars && exit 1

export AWS_ACCESS_KEY_ID="${DBDUMP_AWS_ACCESS_KEY_ID}"
export AWS_SECRET_ACCESS_KEY="${DBDUMP_AWS_SECRET_ACCESS_KEY}"

DBDUMP_FULL_BUCKET="${DBDUMP_FULL_BUCKET:-dfc-anyway-full-db-dumps}"
DBDUMP_PARTIAL_BUCKET="${DBDUMP_PARTIAL_BUCKET:-dfc-anyway-partial-db-dumps}"

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
       "${DBDUMP_FULL_BUCKET}" &&\
echo dumping partial db without truncated tables &&\
dumpdb "pg_dump -d anyway --no-privileges -N topology ${TRUNCATE_TABLES_EXCLUDE_ARGUMENTS}" \
       "`date +%Y-%m-%d`_${DBDUMP_S3_FILE_PREFIX}anyway_partial.pgdump" \
        "${DBDUMP_PARTIAL_BUCKET}" &&\
echo dumping partial db with truncated tables schema only &&\
dumpdb "pg_dump -d anyway --no-privileges -N topology -s ${TRUNCATE_TABLES_INCLUDE_ARGUMENTS}" \
       "`date +%Y-%m-%d`_${DBDUMP_S3_FILE_PREFIX}anyway_partial_schema.pgdump" \
        "${DBDUMP_PARTIAL_BUCKET}" &&\
echo Great Success && exit 0
echo Failed && exit 1
