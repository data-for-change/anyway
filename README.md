ANYWAY [![Build Status](https://travis-ci.org/hasadna/anyway.png)](https://travis-ci.org/hasadna/anyway) [![Build status](https://ci.appveyor.com/api/projects/status/pg5qvt62y16bu4k5?svg=true)](https://ci.appveyor.com/project/r-darwish/anyway)
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

ANYWAY presents locations over an [interactive map](https://www.anyway.co.il/) as well as information regarding traffic accidents including casualties, information originating from the Central Bureau of Statistics (הלשכה המרכזית לסטטיסטיקה) and United Hatzalah’s (איחוד הצלה) data, and traffic violations as reported by road vigilantes (שומרי הדרך). The website allows visitors to discuss possible solutions in their residential or drive zone with the goal of coming up with field solutions by both drivers and pedestrians, on both local and national scope.

The map is also available at [oway.org.il](https://www.oway.org.il/).


### ANYWAY Schools Report

At the beginning of one of the school years we created a report of pedestrian [accidents around schools](http://www.anyway.co.il/schools) - this is one simple example of insights that can be extracted from the data that we have.


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
* We try to follow the process of other Hasadna projects, e.g. [Open-Knesset](https://oknesset-devel.readthedocs.org/en/latest/).
* Please take a moment to read our ["Contributing to ANYWAY" manifest](docs/CONTRIBUTING.md).
* To see our GitHub issues in a nicer interface, take a look at [HuBoard](https://huboard.com/hasadna/anyway). Check out the Ready list to find a task to work on. The Backlog list there contains issues that are still not ready to be started. The Working list contains issues already started by developers (make sure to move your issue there once you start working on it), and the Done list contains completed issues that are waiting to be confirmed done and closed.

## Getting the code
1. [Fork](https://github.com/hasadna/anyway/fork) this repository on GitHub
1. `git clone https://github.com/*you*/anyway`
1. Add the main repository as your upstream remote: `git remote add upstream https://github.com/hasadna/anyway`

* Get updates whenever you start working: `git pull upstream dev`
* Push to your fork when you've committed your changes and tested them: `git push`. Now make sure CI tests are passing (Travis CI and AppVeyor) and make a pull request from your fork on GitHub

## Docker
We are using DOCKER. See [DOCKER](docs/DOCKER.md)

## Optional: Getting the Data
1. Optionally, Get the [complete accidents file](https://drive.google.com/drive/folders/1JVBNP3oTn12zxWExPKeCf_vetNHVCcoo?usp=sharing) after sending a permission request, and extract it into `/static/data/cbs`. Otherwise, you'll use the example accidents files that you already got with the code.
1. Get the RSA file from [rsa file](https://drive.google.com/drive/folders/1oR3q-RBKy8AWXf5Z1JNBKD9cqqlEG-jC?usp=sharing) after sending a permission request and extract the file into `/static/data/rsa`.

## Optional: Adding CI to your forked repository
1. Add Travis CI to your forked repository - in your github forked repository: Settings -> Integrations & services -> Add service -> Travis CI
1. Add AppVeyor to your forked repository - [Login with your GitHub account](https://ci.appveyor.com/login) -> New Project -> GitHub -> anyway

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
