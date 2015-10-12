ANYWAY
======

oway.org.il - Crowd-sourced road hazard reporting website.

Feel free to contribute to the project. It is currently hosted on Heroku:
http://anyway.herokuapp.com

To report bugs and feature requests, please [open an issue](https://github.com/hasadna/anyway/issues) on GitHub.

See also [our Android app](https://github.com/hasadna/anywayAndroidApp) on GitHub.

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
1. `sudo apt-get install python-pip python-dev python-tk libpq-dev`

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
1.  Install [Python 2.7](http://www.python.org/getit)
    *  If Python is already installed and its version is lower than 2.7.9 update to a version >= 2.7.9 OR install [setuptools](http://www.lfd.uci.edu/~gohlke/pythonlibs/#setuptools) & [pip](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pip)(package manager) 
1. Update the `PATH` to include a reference to the `Python` and `Python/scripts` directories (replace `C:\Python27` with your path to Python).
    * Command Line: Run this command with Administrator privileges: `SETX /M PATH "%PATH%";C:\Python27;C:\Python27\Scripts`. The new path will be available in the next opened terminal.
    * GUI: `Control Panel > System Properties > Advanced > Environment Variables > System Variables > Path > Edit >` Add `;C:\Python27;C:\Python27\Scripts` to the end of the line.
1.  Install [VC2008 Express](http://download.microsoft.com/download/A/5/4/A54BADB6-9C3F-478D-8657-93B3FC9FE62D/vcsetup.exe) (alt: mingw)
1.  Install [PostgreSQL] (http://www.postgresql.org/download/windows/) ( __x86 version! even if you have 64 bit os__ )
    * Add its bin folder to your path: `C:\Program Files (x86)\PostgreSQL\9.4\bin\`
1.  Install [GitHub for windows](http://windows.github.com/) and get the code
1.  `cd` to the anyway directory
1.  `pip install -r requirements.txt`
    * If any package fails to install, download it from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs) and install it using `pip install <package>`. 
    * If this fails, you might have to download the `win32` package, even if you are on a 64-bit platform. 
    * Currently, the packages `pyproj` and `psycopg2` are failing to install so for both of them, you need to download and install the `cp27 win32` version, even if you have a 64 bit Windows version installed.
        * http://www.stickpeople.com/projects/python/win-psycopg/

## Local first run (all platforms)
1. Define connection string (needs to be defined whenever you start working):
  * bash: `export DATABASE_URL='sqlite:///local.db'`
  * windows shell: `set DATABASE_URL=sqlite:///local.db`
  
2. First time, create tables: `python models.py`
3. Optionally, get the [complete accidents file](https://drive.google.com/file/d/0B4yX8HDe1VaTdWdPMXV5c2gycW8/view?usp=sharing) after sending a permission request, and extract it into `/static/data/lms`. Otherwise you'll use the [example accidents file](https://drive.google.com/file/d/0B4yX8HDe1VaTSjNMUXYyeW4yQkk/view?usp=sharing) that you already got with the code, so no need to get it again.
4. Populate the data (markers etc.): `python process.py`: this will take less than an hour if you're using the example files (default), but if you have the complete data it may take several days. Be prepared.
5. Populate united hatzala sample data: `python united.py --light` for the complete, or more recent data please contact the Anyway team.
6. Run the app: `python main.py`: do this whenever you start working and want to try out your code.
7. Browse to http://127.0.0.1:5000
8. If the site fails to load properly, make sure you have JDK installed on your machine

It is useful to add the following to your `~/.bashrc` (fixing for the correct path):

    alias anyway='cd *path*/anyway && workon anyway && export DATABASE_URL=sqlite:///local.db'

Then you can simply start working by running the `anyway` command.

## IDE
[PyCharm](https://www.jetbrains.com/pycharm) is recommended for development.

## Testing
Server side testing cand be done by adding python tests under `tests` folder, using a `test_*.py` file name pattern.

To run tests: `python -m unittest discover ./tests`.


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
