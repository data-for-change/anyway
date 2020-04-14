RETRIES=60
export PGPASSWORD=anyway
until psql -h anyway_db_1 -U anyway -d anyway -c "select 1" > /dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
  echo "Waiting for postgres server, $((RETRIES--)) remaining attempts..."
  sleep 1
done
