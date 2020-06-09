Set parameters:
```bash
GITHUB_USER=<github_username>
PGDUMP=<path/to/anyway_public.pgdump>
```

Execute each of the following lines. Note that simply executing as a script may not work.
```bash
sudo apt update
sudo apt upgrade --yes

sudo apt install git python3-venv python3-dev libpq-dev build-essential postgresql postgis default-jdk --yes

# You might prefer using ssh authentication
git clone https://github.com/${GITHUB_USER}/anyway
cd anyway
git remote add upstream https://github.com/hasadna/anyway
git pull upstream dev

python3 -m venv venv_anyway

# execute the following line each time you start working on the project:
source venv_anyway/bin/activate

pip install -U pip
pip install wheel
pip install -r requirements.txt -r test_requirements.txt

sudo service postgresql start

sudo -u postgres createuser ${USER}
sudo -u postgres createuser anyway
sudo -u postgres createuser anyway_redash
sudo -u postgres createuser web_anon

sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'anyway'"
sudo -u postgres psql -c "ALTER USER ${USER} WITH SUPERUSER"
sudo -u postgres psql -c "ALTER USER anyway WITH SUPERUSER"

sudo -u postgres createdb anyway
# sudo -u postgres psql -d anyway -c "GRANT ALL PRIVILEGES ON SCHEMA postgis TO postgres"
sudo -u postgres psql -d anyway -c "CREATE SCHEMA topology"
sudo -u postgres psql -d anyway -c "DROP SCHEMA public"

sudo -u postgres pg_restore -Fc ${PGDUMP} -d anyway --no-owner

# Add this line to ~.bashrc
export DATABASE_URL=postgresql://postgres:anyway@localhost/anyway

# for the following line to run without failures, run
# $ nano tests/test_news_flash.py
# and add @pytest.mark.partial_db to test_extract_location()
pytest -m "not browser and not partial_db"

# Fire up server:
FLASK_APP=anyway flask run --host 0.0.0.0
```