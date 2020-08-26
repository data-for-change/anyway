ANYWAY [![Build Status](https://github.com/hasadna/anyway/workflows/Tests/badge.svg)](https://github.com/hasadna/anyway/actions?query=workflow%3ATests)
======

Welcome to ANYWAY!

ANYWAY is a volunteer based project acting under the umbrella of the Public Knowledge Workshop (“[HASADNA](https://www.hasadna.org.il/about-us/)”).

Feel free to contribute to the project. To report bugs and feature requests, please [open an issue](https://github.com/hasadna/anyway/issues) on GitHub. See [Code Directory Tree Structure](docs/CODE.md).


About
-----------------------

### Our Goal

At ANYWAY we aim to reduce road accidents by: 
1. Raising public awareness of existing road hazards, thereby leading towards safer road behaviour.
1. Collaborating with authorities in order to assist and drive them to find solutions in light of Vision Zero. Such solutions will improve road infrastructure and behavioural problems in attempt to prevent road fatalities.

Take a look at our [facebook page](https://www.facebook.com/anywayisrael). See also our [Android app](https://github.com/samuelregev/anywayAndroidApp/) and [iOS app](https://github.com/hasadna/Anyway-iOS/) on GitHub.


### ANYWAY’s Interactive Map:

ANYWAY presents locations over an [interactive map](https://www.anyway.co.il/) as well as information regarding traffic accidents including casualties, information originating from the Central Bureau of Statistics (הלשכה המרכזית לסטטיסטיקה) and traffic violations as reported by road vigilantes (שומרי הדרך). The website allows visitors to discuss possible solutions in their residential or drive zone with the goal of coming up with field solutions by both drivers and pedestrians, on both local and national scope.

The map is also available at [oway.org.il](https://www.oway.org.il/).


### ANYWAY Schools Report

At the beginning of one of the school years we created a report of pedestrian [accidents around schools](https://reports.anyway.co.il/accidents_around_schools) - this is one simple example of insights that can be extracted from the data that we have.


### ANYWAY’s Infographics Generator - Our Next Challenge

ANYWAY’s next challenge is to form an automatic generator of infographics to empower and serve journalists, bloggers, public opinion leaders, community leaders etc. in the era of **data journalism**. The generated infographics will enhance reporting and news writing with the use of **statistics**. Each infographic will be created for a real-time road accident related **news flash** and will provide a deeper insight into the story based on historical data. This, we believe, will increase both the quantity and quality of articles dealing with road accidents, and will result in raising public awareness and creating pressure on decision makers to initiate infrastructure improvements in light of **Vision Zero**.


### HASADNA

The Public Knowledge Workshop (“[HASADNA](https://www.hasadna.org.il/about-us/)”) is a volunteer-based, non-profit, non-governmental, and non-political organization, working to promote transparency and civic involvement by building open source technological tools to liberate valuable data collected by public institutions and make them accessible, simple and understandable for everyone.
The Public Knowledge Workshop functions as an organizational basis to the projects acting within it. One of those projects is ANYWAY.


### Vision Zero

Read about Vision Zero: [Hebrew](https://ecowiki.org.il/wiki/%D7%97%D7%96%D7%95%D7%9F_%D7%90%D7%A4%D7%A1_%D7%94%D7%A8%D7%95%D7%92%D7%99%D7%9D_%D7%91%D7%AA%D7%90%D7%95%D7%A0%D7%95%D7%AA_%D7%93%D7%A8%D7%9B%D7%99%D7%9D), [English](https://en.wikipedia.org/wiki/Vision_Zero) 


### The Israel National Road Safety Authority (הרשות הלאומית לבטיחות בדרכים)

Take a look at the [daily reports](https://www.gov.il/he/Departments/General/daily_report), [2018 yearly report](https://www.gov.il/BlobFolder/reports/trends_2018/he/research_megamot_2018.pdf) (Hebrew)


Contributing
-----------------------
* Please take a moment to read our ["Contributing to ANYWAY" manifest](docs/CONTRIBUTING.md).

## Getting the code
1. [Fork](https://github.com/hasadna/anyway/fork) this repository on GitHub
1. `git clone https://github.com/*you*/anyway`
1. `cd anyway`
1. Add the main repository as your upstream remote: `git remote add upstream https://github.com/hasadna/anyway`

* Get updates whenever you start working: `git pull upstream dev`
* Push to your fork when you've committed your changes and tested them: `git push`. Now make sure CI tests are passing (see Actions tab) and make a pull request from your fork on GitHub

## Docker
We are using DOCKER. See [DOCKER](docs/DOCKER.md)
For Windows users please first install ubuntu VM. See [UBUNTU_VM_ON_WINDOWS](docs/UBUNTU_VM_ON_WINDOWS.md)

## Testing
### Pylint
To run pylint tests: `pylint -j $(nproc) anyway tests && pytest -m "not browser" ./tests`
### Black
To format the code using black: `black anyway/**/*.py -l 100 anyway` should be executed from the root directory.
Alternatively, one can execute `docker run -v $(pwd):/code jbbarth/black anyway -l 100` to run the command with docker.
        
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
