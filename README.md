ANYWAY [![Build Status](https://travis-ci.org/hasadna/anyway.png)](https://travis-ci.org/hasadna/anyway) [![Build status](https://ci.appveyor.com/api/projects/status/pg5qvt62y16bu4k5?svg=true)](https://ci.appveyor.com/project/r-darwish/anyway)
======

[anyway.co.il](https://www.anyway.co.il/) - Crowd-sourced road hazard reporting website.<br>
Also available at [oway.org.il](https://www.oway.org.il/).

Feel free to contribute to the project.

To report bugs and feature requests, please [open an issue](https://github.com/hasadna/anyway/issues) on GitHub.

See also [our Android app](https://github.com/samuelregev/anywayAndroidApp/) on GitHub.

The datasets Anyway uses are documented here:
* [CBS (Central Bureau of Statistics, למ"ס)](https://github.com/hasadna/anyway/blob/dev/docs/CBS.md)
* [United Hatzalah (איחוד הצלה)](https://github.com/hasadna/anyway/blob/dev/docs/UNITED.md) - Currently not in use

See [Code Directory Tree Structure](docs/CODE.md).

About
-----------------------
Anyway's main goal is raising awareness of road accidents and act to avoid them, by showing road accidents with casualties over map.<br>
The shown data based on reports supplied by the Israeli Central Bureau of Statistics (CBS) and real time reports from United Hatzalah of Israel.<br>
Anyway is an open source project, sponsored by The Public Knowledge Workshop (“Hasadna”).

Contributing
-----------------------
* We try to follow the process of other Hasadna projects, e.g. [Open-Knesset](https://oknesset-devel.readthedocs.org/en/latest/).
* Please take a moment to read our ["Contributing to ANYWAY" manifest](docs/CONTRIBUTING.md).
* To see our GitHub issues in a nicer interface, take a look at [HuBoard](https://huboard.com/hasadna/anyway). Check out the Ready list to find a task to work on. The Backlog list there contains issues that are still not ready to be started. The Working list contains issues already started by developers (make sure to move your issue there once you start working on it), and the Done list contains completed issues that are waiting to be confirmed done and closed.

## Getting the code and Adding CI to your forked repository
1. [Fork](https://github.com/hasadna/anyway/fork) this repository on GitHub
1. Add Travis CI to your forked repository - in your github forked repository: Settings -> Integrations & services -> Add service -> Travis CI
1. Add AppVeyor to your forked repository - [Login with your GitHub account](https://ci.appveyor.com/login) -> New Project -> GitHub -> anyway
1. `git clone https://github.com/*you*/anyway`
1. Add the main repository as your upstream remote: `git remote add upstream https://github.com/hasadna/anyway`

* Get updates whenever you start working: `git pull upstream dev`
* Push to your fork when you've committed your changes and tested them: `git push`. Now make sure CI tests are passing (Travis CI and AppVeyor) and make a pull request from your fork on GitHub

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
1. Optionally, get the [complete accidents file](https://drive.google.com/file/d/19S2hUSzfPLBrhsf1zS8IHaypGN9WgSMc/view?usp=sharing) after sending a permission request, and extract it into `/static/data/cbs`. Otherwise, you'll use the example accidents files that you already got with the code.
1. Populate the data (markers etc.): `python main.py process cbs`: this will take a few minutes if
   you're using the example files (default), but if you have the complete data it may take several
   hours.
1. Populate United Hatzalah sample data: `python main.py process united --light` for the complete,
   or more recent data please contact the Anyway team.
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

## Testing
To run tests: `pylint -j $(nproc) anyway tests && pytest -m "not browser" ./tests`

If you also wish to run the real browser tests, replace`-m "not browser"` with `--driver Chrome` or specify the browser of your choice. To learn more, read about [pytest-selenium](http://pytest-selenium.readthedocs.io/en/latest/user_guide.html#specifying-a-browser).

## Altering the database schema
When creating a patch that alters the database schema, you should use generate the appropriate
[Alembic](http://alembic.zzzcomputing.com/en/latest/index.html) revision by running:

``` shell
alembic revision --autogenerate -m "Description of the change"
```

Make sure to commit your revision together with the code.

## Docker
See [DOCKER](docs/DOCKER.md)

## Translation and Localization
See [TRANSLATE](docs/TRANSLATE.md)
