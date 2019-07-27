Anyway Local environment
===========================

We recommended using DOCKER - see See [DOCKER](docs/DOCKER.md)
However if for some reason you do not want to use it, see the instructions below.

## Local Developement: Installing dependencies

You should be familiar with setting up Python in your computer. You can consult the [wiki](https://github.com/hasadna/anyway/wiki/Setup) for
platform specific tutorials. Developing by using a [virtual
environment](https://www.youtube.com/watch?v=N5vscPTWKOk) is highly recommended.

### Choosing a Python Version
The project is currently transitioning to Python 3. Both Python 2 and 3 are supported at the moment, and the code is tested in Travis against both versions. If you are setting a new environment, it is recommended that you choose Python 3 for future compatibility. The instructions below are relevant for Python 2.

### Ubuntu
1. `sudo apt-get install python2-pip python2-dev libpq-dev rabbitmq-server`

### Fedora
1. `sudo dnf upgrade python-setuptools`

### OS X
1. `sudo easy_install pip setuptools`

### For all platforms:
1. Activate your virtualenv (in case of using one): `source *env-name*/bin/activate`
1. Run `pip install -r requirements.txt -r test_requirements.txt`

### Windows
See the [Wiki](https://github.com/hasadna/anyway/wiki/Setting-up-a-Python-development-environment-in-Windows).

## Local Developement: Local first run (all platforms)
1. Set up a PostgreSQL server and create a database for anyway. The instructions for doing that
   depend on your operating system
1. Define connection string (needs to be defined whenever you start working):
  * bash: `export DATABASE_URL='postgresql://postgres@localhost/anyway'`
  * windows shell: `set DATABASE_URL=postgresql://postgres@localhost/anyway`
  You might need to add your password to the connection url. For more information: https://www.postgresql.org/docs/current/static/libpq-connect.html#LIBPQ-CONNSTRING

1. First time, create tables: `alembic upgrade head`
1. Optionally, get the [complete accidents file](https://drive.google.com/drive/folders/1JVBNP3oTn12zxWExPKeCf_vetNHVCcoo?usp=sharing) after sending a permission request, and extract it into `/static/data/cbs`. Otherwise, you'll use the example accidents files that you already got with the code.
1. Populate the data (markers etc.): `python main.py process cbs`: this will take a few minutes if
   you're using the example files (default), but if you have the complete data it may take several
   hours.
1. Populate United Hatzalah sample data: `python main.py process united --light` for the complete,
   or more recent data please contact the Anyway team.
1. Populate the CBS road segments data: `python main.py process road_segments`
1. Populate CBS registered vehicles in cities : `python main.py process registered_vehicles`: this will take less than an hour
1. Get the RSA file from [rsa file](https://drive.google.com/drive/folders/1oR3q-RBKy8AWXf5Z1JNBKD9cqqlEG-jC?usp=sharing) and extract the file into `/static/data/rsa`. To Populate RSA data: `python main.py process rsa <rsa_file_name>`
1. Run the app: `python main.py testserver`: do this whenever you start working and want to try out your code.
1. Navigate to http://127.0.0.1:5000 in your browser.
1. If the site fails to load properly, make sure you have JDK installed on your machine
1. If you wish to share your app on the local network, you can expose flask by running `python
    main.py testserver --open` (Please note that this would expose your machine on port 5000 to all
    local nodes)

It is useful to add the following to your `~/.bashrc` (fixing for the correct path):

    alias anyway='cd *path*/anyway && workon anyway && export DATABASE_URL=postgresql://postgres@localhost/anyway'

Then you can simply start working by running the `anyway` command.
