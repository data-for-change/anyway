Anyway
======

Any-way.co.il (soon...) - Crowd-sourced road hazard reporting website.

Feel free to contribute to the project. It is currently hosted on Heroku:
http://anyway.herokuapp.com/

Contributing
------------
* Install [Virtualbox](http://virtualbox.org) and [Vagrant](http://vagrantup.com/)
* Clone this repo
* Run `vagrant up` in your shell
* Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser
* Commit and send pull request
* Have fun!

Develpment/Staging/Production Worflow
-------------------------------------
* Make some changes
* Refresh your browser
* If needed: Ctrl+C in the shell, run `vagrant provision`

Heroku deployment
-----------------
* Create an account on [Heroku](http://heroku.com/)
* Follow the [quickstart instructions](https://devcenter.heroku.com/articles/quickstart). On step #4, read the [Python introduction](https://devcenter.heroku.com/articles/getting-started-with-python)
* Create an app
* Sign up for free tier ClearDB (MySQL). Note that you'll have to enter your credit card details to be eliable for the free MySQL usage.
* Tweak your Heroku app configurations:
	* Remove `?reconnect=true` from your CLEARDB config: `heroku config:set CLEARDB_DATABASE_URL=$(heroku config:get CLEARDB_DATABASE_URL | cut -d '?' -f 1)`
	* Set BUILDPACK_URL: `heroku config:set BUILDPACK_URL="https://github.com/omribahumi/heroku-buildpack-python.git"`
* Load the data:
    * Run vagrant
    * In `vagrant ssh`:
    	* `sudo -i`
    	* `source ~/venv/bin/activate`
    	* `cd /vagrant`
    	* `export CLEARDB_DATABASE_URL="your_app_cleardb_database_url"`
    	* `python models.py`
    	* `python process.py --ratio 10`
* Deploy your git repo to heroku


Bugs & Feature Requests
-----------------------
* Read our forum (soon)
* Open an issue here

Developer Documentation
-----------------------
* [Manual setup](https://github.com/hasadna/anyway/wiki/Setup) of our development stack
* We try to follow the process of other Hasadna projects, e.g. [Open-Knesset](https://oknesset-devel.readthedocs.org/en/latest/)


