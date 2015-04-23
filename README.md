Anyway
======

www.anyway.co.il - Crowd-sourced road hazard reporting website.

Feel free to contribute to the project. It is currently hosted on Heroku:
http://anyway.herokuapp.com

To report bugs and feature requests, please [open an issue](https://github.com/hasadna/anyway/issues) on GitHub.

Contributing
-----------------------
* We try to follow the process of other Hasadna projects, e.g. [Open-Knesset](https://oknesset-devel.readthedocs.org/en/latest/)

## Development environment setup notes 

## Getting the code
1. [Fork](https://github.com/hasadna/anyway/fork) this repository on GitHub
2. `git clone https://github.com/*you*/anyway`
3. Add the main repository as your upstream remote: `git remote add upstream https://github.com/hasadna/anyway`

* Get updates whenever you start working: `git pull upstream master`
* Push to your fork when you've committed your changes and tested them: `git push`, and make a pull request from your fork on GitHub

## Installing dependencies

### Ubuntu
1. `sudo apt-get install python-pip python-dev libpq-dev`

### OS X
1. `sudo easy_install pip setuptools`
2. Install postgresql: `brew install postgresql` (after installing [brew](http://brew.sh))

### virtualenv setup (both Ubuntu and OS X)
1. `sudo pip install virtualenvwrapper`
2. Add to your `~/.bashrc`: `source /usr/local/bin/virtualenvwrapper.sh`
3. `mkvirtualenv anyway`
4. `cd anyway`
5. `pip install -r requirements.txt`

* Each time you start working: `workon anyway`

### Windows (experimental)
1. Install [Python 2.7](http://www.python.org/getit)
2. Install [setuptools](http://www.lfd.uci.edu/~gohlke/pythonlibs/#setuptools) & [pip](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pip)(package manager) and update PATH to python and python/scripts directories (e.g. `PATH=%PATH%;C:\Python27\Scripts`)
3. Install [VC2008 Express](http://download.microsoft.com/download/A/5/4/A54BADB6-9C3F-478D-8657-93B3FC9FE62D/vcsetup.exe) (alt: mingw)
4. Install [GitHub for windows](http://windows.github.com/) and get the code
5. `cd` to the anyway directory
7. `pip install -r requirements.txt`
8. If any package fails to install, download it from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs) and install it using `pip install <package>`. If this fails, you might have to download the `win32` package, even if you are on a 64-bit platform.

## Local first run (all platforms)
1. Define connection string (needs to be defined whenever you start working):
  * bash: `export DATABASE_URL='sqlite:///local.db'`
  * windows shell: `set DATABASE_URL="sqlite:///local.db"`
  
2. First time, create tables: `python models.py`
3. Optionally, get the [complete accidents file](https://drive.google.com/file/d/0B4yX8HDe1VaTdWdPMXV5c2gycW8/view?usp=sharing) after sending a permission request, and extract it into `/static/data/lms`. Otherwise you'll use the [example accidents file](https://drive.google.com/file/d/0B4yX8HDe1VaTSjNMUXYyeW4yQkk/view?usp=sharing) that you already got with the code, so no need to get it again.
4. Populate the data (markers etc.): `python process.py`: this will take less than an hour if you're using the example files (default), but if you have the complete data it may take several days. Be prepared.
5. Run the app: `python main.py`: do this whenever you start working and want to try out your code.
6. Browse to http://127.0.0.1:5000

It is useful to add the following to your `~/.bashrc` (fixing for the correct path):

    alias anyway='cd *path*/anyway && workon anyway && export DATABASE_URL=sqlite:///local.db'

Then you can simply start working by running the `anyway` command.

## IDE
[PyCharm](https://www.jetbrains.com/pycharm) is recommended for development.


Heroku deployment
-----------------
1. Create an account on [Heroku](http://heroku.com)
2. Install the [Heroku toolbelt](https://toolbelt.heroku.com)
3. Follow the [quickstart instructions](https://devcenter.heroku.com/articles/quickstart). On step #4, read the [Python introduction](https://devcenter.heroku.com/articles/getting-started-with-python)
4. Create an app, e.g. anyway-*you*
5. Sign up for a free Heroku Postgres add-on (note that you'll have to enter your credit card details to be eligible): `heroku addons:add heroku-postgresql:hobby-dev`
6. Push from your Git repository to Heroku
7. Populate the database with the data (assuming you have it in your local directory):
    1. Copy the database URL from your Heroku config: `heroku config:get DATABASE_URL` (if you have several apps, specify the relevant one with the option `--app <anyway-*you*>` for any Heroku command)
    2. Create tables: `python models.py`
    3. Populate data: `python process.py`
8. Browse to http://anyway-*you*.herokuapp.com
