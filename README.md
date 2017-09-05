ANYWAY [![Build Status](https://travis-ci.org/hasadna/anyway.png)](https://travis-ci.org/hasadna/anyway)
======

oway.org.il - Crowd-sourced road hazard reporting website.

Feel free to contribute to the project.

To report bugs and feature requests, please [open an issue](https://github.com/hasadna/anyway/issues) on GitHub.

See also [our Android app](https://github.com/hasadna/anywayAndroidApp) on GitHub.

See documentation for our source dataset LAMAS is [here](https://github.com/hasadna/anyway/blob/dev/docs/LMS.md) and United is [here](https://github.com/hasadna/anyway/blob/dev/docs/UNITED.md).

See [Code Directory Tree Structure](docs/CODE.md).

Contributing
-----------------------
* We try to follow the process of other Hasadna projects, e.g. [Open-Knesset](https://oknesset-devel.readthedocs.org/en/latest/).
* Please take a moment to read our ["Contibuting to ANYWAY" manifest](docs/CONTRIBUTING.md).
* To see our GitHub issues in a nicer interface, take a look at [HuBoard](https://huboard.com/hasadna/anyway). Check out the Ready list to find a task to work on. The Backlog list there contains issues that are still not ready to be started. The Working list contains issues already started by developers (make sure to move your issue there once you start working on it), and the Done list contains completed issues that are waiting to be confirmed done and closed.

## Getting the code
1. [Fork](https://github.com/hasadna/anyway/fork) this repository on GitHub
1. `git clone https://github.com/*you*/anyway`
1. Add the main repository as your upstream remote: `git remote add upstream https://github.com/hasadna/anyway`

* Get updates whenever you start working: `git pull upstream dev`
* Push to your fork when you've committed your changes and tested them: `git push`, and make a pull request from your fork on GitHub

## Installing dependencies

You should be fimilar with setting up Python in your computer. You can consult the wiki for
platform specific tutorials. Developing by using a [virtual
environment](https://www.youtube.com/watch?v=N5vscPTWKOk) is highly recommended.

### Ubuntu
`sudo apt-get install python2-pip python2-dev libpq-dev`

### OS X
1. `sudo easy_install pip setuptools`
1. Install postgresql: `brew install postgresql` (after installing [brew](http://brew.sh))

### Both Ubuntu and OS X: 
1. Activate your virtualenv and run `pip install -r requirements.txt`

### Windows (experimental)
See the Wiki.

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

## Testing
Server side testing can be done by adding python tests under `tests` folder, using a `test_*.py` file name pattern.

To run tests: `python -m unittest discover ./tests`.

The code is also checked with Pylint in Travis. In order to run pylint locally you should first
install it in your virtualenv by executing `pip install pylint` and then `pylint -j $(nproc) *.py`
in order to check the entire repository. Note that the `-j` flag is optional.


Docker ------- See [DOCKER](docs/DOCKER.md)

Translation and Localization
----------------------------
See [TRANSLATE](docs/TRANSLATE.md)

