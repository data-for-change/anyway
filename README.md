ANYWAY
======

oway.org.il - Crowd-sourced road hazard reporting website.

Feel free to contribute to the project. It is currently hosted on Heroku:
http://anyway.herokuapp.com

To report bugs and feature requests, please [open an issue](https://github.com/hasadna/anyway/issues) on GitHub.

See also [our Android app](https://github.com/hasadna/anywayAndroidApp) on GitHub.

See [documentation for our source dataset](docs/DATA_SOURCE.md).

Contributing
-----------------------
* We try to follow the process of other Hasadna projects, e.g. [Open-Knesset](https://oknesset-devel.readthedocs.org/en/latest/).
* Please take a moment to read our ["Contibuting to ANYWAY" manifest](docs/CONTRIBUTING.md).
* To see our GitHub issues in a nicer interface, take a look at [HuBoard](https://huboard.com/hasadna/anyway). Check out the Ready list to find a task to work on. The Backlog list there contains issues that are still not ready to be started. The Working list contains issues already started by developers (make sure to move your issue there once you start working on it), and the Done list contains completed issues that are waiting to be confirmed done and closed.

Development environment setup notes
-----------------------
##### Choose one of two environment setup options: <br>

1.  **Local installation**:

## Getting the code
1. [Fork](https://github.com/hasadna/anyway/fork) this repository on GitHub
1. `git clone https://github.com/*you*/anyway`
1. Add the main repository as your upstream remote: `git remote add upstream https://github.com/hasadna/anyway`

* Get updates whenever you start working: `git pull upstream dev`
* Push to your fork when you've committed your changes and tested them: `git push`, and make a pull request from your fork on GitHub

## Installing dependencies

### Ubuntu
`sudo apt-get install python-pip python-dev python-tk libpq-dev`

### OS X
1. `sudo easy_install pip setuptools`
1. Install postgresql: `brew install postgresql` (after installing [brew](http://brew.sh))

### Both Ubuntu and OS X: `virtualenv` setup
1. `sudo pip install virtualenvwrapper`
1. Add to your `~/.bashrc`:

      `source /usr/local/bin/virtualenvwrapper.sh`

   (Assuming it exists. Otherwise, it might be in `/usr/bin/virtualenvwrapper.sh`, so use that instead in that case.)
1. `source ~/.bashrc`
1. `mkvirtualenv anyway`
1. `cd anyway`
1. `pip install -r requirements.txt`

* Each time you start working: `workon anyway`

### Windows (experimental)
1.  Install [Python 2.7.11](http://www.python.org/getit)
    *  If Python is already installed and its version is lower than 2.7.11 update to a version >= 2.7.11 OR install [setuptools](http://www.lfd.uci.edu/~gohlke/pythonlibs/#setuptools) & [pip](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pip)(package manager) 
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

### Creating a cloud development environment on c9

1. Create an account at c9.io (preferably with github verification, but can also be done with a simple IP address

2. Create a new public python based project that receives code from   https://github.com/hasadna/anyway repository 

3. Preform git checkout dev
After the Clone activity is completed (can take a few minutes) run the following:
    * sudo pip install -r requirements.txt
    * export DATABASE_URL='sqlite:///local.db'
    * python models.py
    * python process.py

4. Go to configurations page (using the top right configuration icon) go to the `Run Configuration` part and press `Add New config`

5. Do the following definitions on the window that just popped up:
    * Definition Name - Anyway
    * File to be run - main.py
    * Press enter to save the setting.
    * Environment variables  - DATABASE_URL sqlite:///local.db (in two different colums)

6. Set this to be the default by selecting the definitions window and pressing `Set As Default`

7. Run the environment by pressing `Run Application` and see it by pressing `Preview` and then `Preview Running Application`

## Local first run (all platforms)
1. Define connection string (needs to be defined whenever you start working):
  * bash: `export DATABASE_URL='sqlite:///local.db'`
  * windows shell: `set DATABASE_URL=sqlite:///local.db`
  
1. First time, create tables: `python models.py`
1. Optionally, get the [complete accidents file](https://drive.google.com/file/d/0B4yX8HDe1VaTdWdPMXV5c2gycW8/view?usp=sharing) after sending a permission request, and extract it into `/static/data/lms`. Otherwise you'll use the [example accidents file](https://drive.google.com/file/d/0B4yX8HDe1VaTSjNMUXYyeW4yQkk/view?usp=sharing) that you already got with the code, so no need to get it again.
1. Populate the data (markers etc.): `python process.py`: this will take less than an hour if you're using the example files (default), but if you have the complete data it may take several days. Be prepared.
1. Populate united hatzala sample data: `python united.py --light` for the complete, or more recent data please contact the Anyway team.
1. Run the app: `python main.py`: do this whenever you start working and want to try out your code.
1. Navigate to http://127.0.0.1:5000 in your browser.
1. If the site fails to load properly, make sure you have JDK installed on your machine
1. If you wish to share your app on the local network you can expose flask by running `python main.py --open`
    (Please note that this would expose your machine on port 5000 to all local nodes)

It is useful to add the following to your `~/.bashrc` (fixing for the correct path):

    alias anyway='cd *path*/anyway && workon anyway && export DATABASE_URL=sqlite:///local.db'

Then you can simply start working by running the `anyway` command.

## IDE
[PyCharm](https://www.jetbrains.com/pycharm) is recommended for development.

You can do most of the setup through PyCharm:

1. After getting the code, open the `anyway` directory in PyCharm.
1. Set up a virtualenv: File -> Settings -> Project -> Project Interpreter -> Click the cog icon at the top right -> Create VirtualEnv. Name it "anyway" and choose Python 2.7.11 as the base interpreter.
1. Restart PyCharm, and when it asks whether to install the packages from `requirements.txt`, answer Yes.
1. Right click `models.py` and choose Run 'models', then click the dropdown menu at the top that says `models` and click Edit Configurations. Under Environment, click the `...` next to Environment variables and add the variable `DATABASE_URL` with the value `sqlite:///local.db`. Then click OK twice and run `models.py` again.
1. Run `process.py` the same way (adding the `DATABASE_URL` variable).
1. Run `united.py` the same way, but in Edit Configurations, also add `--light` in the Script parameters.
1. Run `main.py` the same way (without `--light`).
1. Navigate to http://127.0.0.1:5000 in your browser.

## Testing
Server side testing can be done by adding python tests under `tests` folder, using a `test_*.py` file name pattern.

To run tests: `python -m unittest discover ./tests`.


Heroku deployment
-----------------
1. Create an account on [Heroku](http://heroku.com)
1. Install the [Heroku toolbelt](https://toolbelt.heroku.com)
1. Follow the [quickstart instructions](https://devcenter.heroku.com/articles/quickstart). On step #4, read the [Python introduction](https://devcenter.heroku.com/articles/getting-started-with-python)
1. Create an app, e.g. anyway-*you*
1. Sign up for a free Heroku Postgres add-on (note that you'll have to enter your credit card details to be eligible): `heroku addons:add heroku-postgresql:hobby-dev`
1. Push from your Git repository to Heroku
1. Populate the database with the data (assuming you have it in your local directory):
    1. Copy the database URL from your Heroku config: `heroku config:get DATABASE_URL` (if you have several apps, specify the relevant one with the option `--app <anyway-*you*>` for any Heroku command)
    1. Create tables: `python models.py`
    1. Populate data: `python process.py`
1. Navigate to http://anyway-*you*.herokuapp.com

Docker
-------
See [DOCKER](docs/DOCKER.md)

Translation and Localization
----------------------------
See [TRANSLATE](docs/TRANSLATE.md)

