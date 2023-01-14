Redash access is [in the following link](https://redash.dataforchange.org.i/)

In order to grant access to a table for Redash user:

1. Execute shell on the production DB pod (Ori Hoch / Atalya Alon can do it)
3. Run `psql anyway anyway`
4. Run `GRANT SELECT ON <table name>  TO redash;`
