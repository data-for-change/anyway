ANYWAY [![Build Status](https://travis-ci.org/hasadna/anyway.png)](https://travis-ci.org/hasadna/anyway) [![Build status](https://ci.appveyor.com/api/projects/status/pg5qvt62y16bu4k5?svg=true)](https://ci.appveyor.com/project/r-darwish/anyway)
======

[anyway.co.il](https://www.anyway.co.il/) - Crowd-sourced road hazard reporting website.<br>
Also available at [oway.org.il](https://www.oway.org.il/).

Feel free to contribute to the project.

To report bugs and feature requests, please [open an issue](https://github.com/hasadna/anyway/issues) on GitHub.

See also [our Android app](https://github.com/hasadna/anywayAndroidApp) on GitHub.

The datasets Anyway uses are documented here:
* [CBS (Central Bureau of Statistics, למ"ס)](https://github.com/hasadna/anyway/blob/dev/docs/LMS.md)
* [United Hatzalah (איחוד הצלה)](https://github.com/hasadna/anyway/blob/dev/docs/UNITED.md)

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

## Getting the code
1. [Fork](https://github.com/hasadna/anyway/fork) this repository on GitHub
1. `git clone https://github.com/*you*/anyway`
1. Add the main repository as your upstream remote: `git remote add upstream https://github.com/hasadna/anyway`

* Get updates whenever you start working: `git pull upstream dev`
* Push to your fork when you've committed your changes and tested them: `git push`, and make a pull request from your fork on GitHub

## Installing dependencies

You should be familiar with setting up Python in your computer. You can consult the [wiki](https://github.com/hasadna/anyway/wiki/Setup) for
platform specific tutorials. Developing by using a [virtual
environment](https://www.youtube.com/watch?v=N5vscPTWKOk) is highly recommended.

### Ubuntu
`sudo apt-get install python2-pip python2-dev libpq-dev`

### Fedora
1. `sudo dnf upgrade python-setuptools`
1. `sudo dnf install python-pip`

### CentOS
1. `sudo yum upgrade python-setuptools`
1. `sudo yum install python-pip`

### OS X
1. `sudo easy_install pip setuptools`
1. Install postgresql: `brew install postgresql` (after installing [brew](http://brew.sh))

### For all platforms:
1. Activate your virtualenv (in case of using one): `source *env-name*/bin/activate`
1. Run `pip install -r requirements.txt -r test_requirements.txt`

### Windows (experimental)
See the [Wiki](https://github.com/hasadna/anyway/wiki/Setting-up-a-Python-development-environment-in-Windows).

## Local first run (all platforms)
1. Define connection string (needs to be defined whenever you start working):
  * bash: `export DATABASE_URL='sqlite:///local.db'`
  * windows shell: `set DATABASE_URL=sqlite:///local.db`

1. First time, create tables: `python main.py init_db`
1. Optionally, get the [complete accidents file](https://drive.google.com/file/d/0B4yX8HDe1VaTdWdPMXV5c2gycW8/view?usp=sharing) after sending a permission request, and extract it into `/static/data/lms`. Otherwise, you'll use the [example accidents file](https://drive.google.com/file/d/0B4yX8HDe1VaTSjNMUXYyeW4yQkk/view?usp=sharing) that you already got with the code, so no need to get it again.
1. Populate the data (markers etc.): `python main.py process_data`: this will take less than an hour if you're
   using the example files (default), but if you have the complete data it may take several days. Be
   prepared.
1. Populate United Hatzalah sample data: `python main.py import_united_data --light` for the
   complete, or more recent data please contact the Anyway team.
1. Run the app: `python main.py testserver`: do this whenever you start working and want to try out your code.
1. Navigate to http://127.0.0.1:5000 in your browser.
1. If the site fails to load properly, make sure you have JDK installed on your machine
1. If you wish to share your app on the local network, you can expose flask by running `python
    main.py testserver --open` (Please note that this would expose your machine on port 5000 to all
    local nodes)

It is useful to add the following to your `~/.bashrc` (fixing for the correct path):

    alias anyway='cd *path*/anyway && workon anyway && export DATABASE_URL=sqlite:///local.db'

Then you can simply start working by running the `anyway` command.

## Testing
To run tests: `pylint -j $(nproc) anyway tests && pytest -m "not browser" ./tests`

If you also wish to run the real browser tests, replace`-m "not browser"` with `--driver Chrome` or specify the browser of your choice. To learn more, read about [pytest-selenium](http://pytest-selenium.readthedocs.io/en/latest/user_guide.html#specifying-a-browser).

## Docker
See [DOCKER](docs/DOCKER.md)

## Translation and Localization
See [TRANSLATE](docs/TRANSLATE.md)
