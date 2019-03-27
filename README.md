ANYWAY [![Build Status](https://travis-ci.org/hasadna/anyway.png)](https://travis-ci.org/hasadna/anyway) [![Build status](https://ci.appveyor.com/api/projects/status/pg5qvt62y16bu4k5?svg=true)](https://ci.appveyor.com/project/r-darwish/anyway)
======

[anyway.co.il](https://www.anyway.co.il/) - Crowd-sourced road hazard reporting website.<br>
Also available at [oway.org.il](https://www.oway.org.il/).

Feel free to contribute to the project.

To report bugs and feature requests, please [open an issue](https://github.com/hasadna/anyway/issues) on GitHub.

See also our [Android app](https://github.com/samuelregev/anywayAndroidApp/)
and [iOS app](https://github.com/hasadna/Anyway-iOS/) on GitHub.

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

## Docker
We are using DOCKER. See [DOCKER](docs/DOCKER.md)

## Getting the code and Adding CI to your forked repository
1. [Fork](https://github.com/hasadna/anyway/fork) this repository on GitHub
1. Add Travis CI to your forked repository - in your github forked repository: Settings -> Integrations & services -> Add service -> Travis CI
1. Add AppVeyor to your forked repository - [Login with your GitHub account](https://ci.appveyor.com/login) -> New Project -> GitHub -> anyway
1. `git clone https://github.com/*you*/anyway`
1. Add the main repository as your upstream remote: `git remote add upstream https://github.com/hasadna/anyway`

* Get updates whenever you start working: `git pull upstream dev`
* Push to your fork when you've committed your changes and tested them: `git push`. Now make sure CI tests are passing (Travis CI and AppVeyor) and make a pull request from your fork on GitHub

## Optional: Getting the Data
1. Optionally, Get the [complete accidents file](https://drive.google.com/drive/folders/1JVBNP3oTn12zxWExPKeCf_vetNHVCcoo?usp=sharing) after sending a permission request, and extract it into `/static/data/cbs`. Otherwise, you'll use the example accidents files that you already got with the code.
1. Get the RSA file from [rsa file](https://drive.google.com/drive/folders/1oR3q-RBKy8AWXf5Z1JNBKD9cqqlEG-jC?usp=sharing) after sending a permission request and extract the file into `/static/data/rsa`.

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

## Translation and Localization
See [TRANSLATE](docs/TRANSLATE.md)
