Anyway
======

www.anyway.co.il - Crowd-sourced road hazard reporting website.

Feel free to contribute to the project. It is currently hosted on Heroku:
http://anyway.herokuapp.com

To report bugs and feature requests, please [open an issue](https://github.com/hasadna/anyway/issues) on GitHub.

Contributing
-----------------------
* We try to follow the process of other Hasadna projects, e.g. [Open-Knesset](https://oknesset-devel.readthedocs.org/en/latest/)

## Development Environment Setup Notes 

## Getting the code
1. [Fork](https://github.com/hasadna/anyway/fork) this repository on GitHub
2. `git clone https://github.com/*you*/anyway`
3. Add the main repository as your upstream remote: `git remote add upstream https://github.com/hasadna/anyway`
4. Get updates whenever you start working: `git pull upstream master`
5. Push to your fork when you've committed your changes and tested them: `git push`, and make a pull request from your fork on GitHub

## Installing dependencies

### Ubuntu
1. `sudo apt-get install pip libpq-dev`

### OS X
1. `sudo easy_install pip setuptools`
2. Install postgresql: `brew install postgresql` (after installing [brew](http://brew.sh))

### virtualenv setup (both Ubuntu and OS X)
1. `sudo pip install virtualenvwrapper`
2. Add to your `~/.bash_profile` or `./bashrc`: `source /usr/local/bin/virtualenvwrapper.sh`
3. `mkvirtualenv anyway`
4. `cd anyway`
5. `pip install -r requirements.txt`
6. `workon anyway` (each time you start working)

### Windows
1. Install [Python 2.7](http://www.python.org/getit)
2. Install [setuptools](http://www.lfd.uci.edu/~gohlke/pythonlibs/#setuptools) & [pip](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pip)(package manager) and update PATH to python and python/scripts directories (e.g. `PATH=%PATH%;C:\Python27\Scripts`)
3. Install [VC2008 Express](http://download.microsoft.com/download/A/5/4/A54BADB6-9C3F-478D-8657-93B3FC9FE62D/vcsetup.exe) (alt: mingw)
4. Install [GitHub for windows](http://windows.github.com/) and get the code
5. `cd` to the anyway directory
7. `pip install -r requirements.txt`
8. If any package fails to install, download it from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs) and install it using `pip install <package>`. If this fails, you might have to download the `win32` package, even if you are on a 64-bit platform.

## Local First Run
1. Define connection string:
  * bash: `export DATABASE_URL='sqlite:///local.db'`
  * windows shell: `set DATABASE_URL="sqlite:///local.db"`
2. First time, create tables: `python models.py`
3. Extract the [example accidents file](https://drive.google.com/file/d/0B4yX8HDe1VaTSjNMUXYyeW4yQkk/view?usp=sharing) into `/static/data/lms` (or ask permission and get the [complete accidents file](https://drive.google.com/file/d/0B4yX8HDe1VaTdWdPMXV5c2gycW8/view?usp=sharing)).
4. Populate the data (markers etc.): `python process.py`
5. Run app: `python main.py` (or: `foreman start` if you installed the [Heroku toolbelt](https://toolbelt.heroku.com))
6. Browse to http://127.0.0.1:5000

## IDE
Most of us use [PyCharm](https://www.jetbrains.com/pycharm) for development.


Heroku deployment
-----------------
1. Create an account on [Heroku](http://heroku.com)
2. Follow the [quickstart instructions](https://devcenter.heroku.com/articles/quickstart). On step #4, read the [Python introduction](https://devcenter.heroku.com/articles/getting-started-with-python)
3. Create an app, e.g. anyway-*you*
4. Sign up for free tier ClearDB (MySQL). Note that you'll have to enter your credit card details to be eligible for the free MySQL usage.
5. Deploy your git repo to heroku
6. Load the database with our data:
    1. Tweak your Heroku app configurations, by removing `?reconnect=true` from your CLEARDB config (if you have several apps, specify the relevant one with the option `--app <anyway-mydev>` for all following heroku commands):
    2. `heroku config:set DATABASE_URL=$(heroku config:get DATABASE_URL | cut -d '?' -f 1)`
    2. Create tables: `heroku run ./models.py`
    3. Populate data: `heroku run ./process.py`
7. Browse to http://anyway-*you*.herokuapp.com
