Postgres
========
```
psql -d template1
```

Try to run:
```
CREATE DATABASE "anyway" ENCODING "utf8";
```

If you fail because you can't create "utf8" database from template1,
Run the following commands and try again to create the database.

psql postgres
```
UPDATE pg_database SET datistemplate = FALSE WHERE datname = 'template1';
DROP DATABASE template1;
CREATE DATABASE template1 WITH TEMPLATE = template0 ENCODING = 'UTF8';
UPDATE pg_database SET datistemplate = TRUE WHERE datname = 'template1';
\c template1
VACUUM FREEZE;
```


