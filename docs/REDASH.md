Redash access is [in the following link](https://redash.hasadna.org.il/)

In order to grant access to a table for Redash user:

1. Login to the Rancher instance (Ori Hoch / Atalya Alon can grant access)
2. Go to the execute shell of the DB
3. Run `psql anyway anyway`
4. Run `GRANT SELECT ON <table name>  TO anyway_redash;`
