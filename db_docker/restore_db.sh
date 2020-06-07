#!/bin/sh

set -e

if ! [ -z "${S3_RESTORE_ACCESS}" ] && ! [ -z "${S3_RESTORE_SECRET}" ] && ! [ -z "${S3_RESTORE_FILENAMES}" ]; then
  # to create the dump - from old anyway DB server:
  # cd `mktemp -d`
  # chown postgres .
  # su postgres -c "pg_dumpall --roles-only" > "`date +%Y-%m-%d_%H-%M-%S`_anyway_roles.pgdump"
  # su postgres -c "pg_dumpall --schema-only" > "`date +%Y-%m-%d_%H-%M-%S`_anyway_schema.pgdump"
  # su postgres -c "pg_dumpall --data-only" > "`date +%Y-%m-%d_%H-%M-%S`_anyway_data.pgdump"
  # gzip *.pgdump
  # s3cmd -c /etc/anyway-s3cfg put *.gz s3://anyway-db-dumps
  # rm *.gz
  echo restoring from S3
  TEMPDIR=`mktemp -d`
  echo "
[default]
# Object Storage Region NL-AMS
host_base = s3.nl-ams.scw.cloud
host_bucket = %(bucket)s.s3.nl-ams.scw.cloud
bucket_location = nl-ams
use_https = True

# Login credentials
access_key = ${S3_RESTORE_ACCESS}
secret_key = ${S3_RESTORE_SECRET}
" > $TEMPDIR/anyway-s3cfg
  for FILENAME in $S3_RESTORE_FILENAMES; do
    s3cmd -c $TEMPDIR/anyway-s3cfg get "s3://anyway-db-dumps/${FILENAME}.pgdump.gz" "${TEMPDIR}/"
    gzip -d "${TEMPDIR}/${FILENAME}.pgdump.gz"
    chown postgres ${TEMPDIR}/${FILENAME}.pgdump
    psql -f ${TEMPDIR}/${FILENAME}.pgdump
  done
  echo "alter role anyway with password '${S3_RESTORE_ANYWAY_PASSWORD}'" | psql
elif ! [ -z "${GDRIVE_FILE_ID}" ]; then
  echo restoring from GDRIVE
  export DB_DUMP_PATH=`mktemp`.pgdump
  GDRIVE_URL="https://drive.google.com/uc?id=" python3 /download_dump.py
  pg_restore -Fc "$DB_DUMP_PATH" -d "$POSTGRES_DB" --no-owner
else
  echo missing GDRIVE_FILE_ID env var for DB restore
  exit 1
fi
