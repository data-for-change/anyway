ANYWAY [![Build Status](https://github.com/data-for-change/anyway/workflows/Tests/badge.svg)](https://github.com/data-for-change/anyway/actions?query=workflow%3ATests)
======

Welcome to ANYWAY!

ANYWAY is a volunteer based project acting under the umbrella of the Data For Change Organization.

Feel free to contribute to the project. To report bugs and feature requests, please [open an issue](https://github.com/data-for-change/anyway/issues) on GitHub. See [Code Directory Tree Structure](docs/CODE.md).

Note: This is ANYWAY BackEnd and Map repository. If you're a FrontEnd developer see our [FE Infographics repository here](https://github.com/data-for-change/anyway-newsflash-infographics).


About
-----------------------

### Our Goal

At ANYWAY we aim to reduce road accidents by: 
1. Raising public awareness of existing road hazards, thereby leading towards safer road behaviour.
1. Collaborating with authorities in order to assist and drive them to find solutions in light of Vision Zero. Such solutions will improve road infrastructure and behavioural problems in attempt to prevent road fatalities.

Take a look at our [facebook page](https://www.facebook.com/anywayisrael). See also our [Android app](https://github.com/data-for-change/anywayAndroidApp/) and [iOS app](https://github.com/data-for-change/Anyway-iOS/) on GitHub.


### ANYWAY’s Interactive Map:

ANYWAY presents locations over an [interactive map](https://www.anyway.co.il/) as well as information regarding traffic accidents including casualties, information originating from the Central Bureau of Statistics (הלשכה המרכזית לסטטיסטיקה) and traffic violations as reported by road vigilantes (שומרי הדרך). The website allows visitors to discuss possible solutions in their residential or drive zone with the goal of coming up with field solutions by both drivers and pedestrians, on both local and national scope.

The map is also available at [oway.org.il](https://www.oway.org.il/).


### ANYWAY Schools Report

At the beginning of one of the school years we created a report of pedestrian [accidents around schools](https://reports.anyway.co.il/accidents_around_schools) - this is one simple example of insights that can be extracted from the data that we have.


### ANYWAY’s Infographics Generator - Our Next Challenge

ANYWAY’s next challenge is to form an automatic generator of infographics to empower and serve journalists, bloggers, public opinion leaders, community leaders etc. in the era of **data journalism**. The generated infographics will enhance reporting and news writing with the use of **statistics**. Each infographic will be created for a real-time road accident related **news flash** and will provide a deeper insight into the story based on historical data. This, we believe, will increase both the quantity and quality of articles dealing with road accidents, and will result in raising public awareness and creating pressure on decision makers to initiate infrastructure improvements in light of **Vision Zero**.
Relevant github repositories:
- [Infographics FrontEnd](https://github.com/data-for-change/anyway-newsflash-infographics)
- [ANYWAY ETL Flows](https://github.com/data-for-change/anyway-etl)
Note: ANYWAY ETL Flows uses current repository code - to update ANYWAY ETL with most updated anyway code, the change needs to be introduced in a release of anyway-etl.


### Data For Change
Data For Change (“NATOON LESHINUI” - in hebrew ״נתון לשינוי״) is a volunteer-based, non-profit organization, promoting transparency and opening data from governmental and public organizations. Together with our volunteers community, we are developing technological tools for accessibility and analysis of data, enhancing practical use of data for data-driven decision-making, providing decision-makers with accessible information and creating public discourse. Our volunteers are made of talented programmers, data analysts, data scientists, product managers and designers who seek to use their skills in order to create a positive data driven change in the world.


### Vision Zero

Read about Vision Zero: [Hebrew](https://ecowiki.org.il/wiki/%D7%97%D7%96%D7%95%D7%9F_%D7%90%D7%A4%D7%A1_%D7%94%D7%A8%D7%95%D7%92%D7%99%D7%9D_%D7%91%D7%AA%D7%90%D7%95%D7%A0%D7%95%D7%AA_%D7%93%D7%A8%D7%9B%D7%99%D7%9D), [English](https://en.wikipedia.org/wiki/Vision_Zero) 


### The Israel National Road Safety Authority (הרשות הלאומית לבטיחות בדרכים)

Take a look at the [daily reports](https://www.gov.il/he/Departments/General/daily_report), [2018 yearly report](https://www.gov.il/BlobFolder/reports/trends_2018/he/research_megamot_2018.pdf) (Hebrew)


Contributing
-----------------------
* Please take a moment to read our ["Contributing to ANYWAY" manifest](docs/CONTRIBUTING.md).

## Getting the code

### NOTE: If you are setting up anyway on Windows using WSL - PLEASE MAKE SURE TO COMPLETE THE FOLLOWING STEPS FROM YOUR WSL TERMINAL!!!

1. [Fork](https://github.com/data-for-change/anyway/fork) this repository on GitHub
1. `git clone https://github.com/*you*/anyway`
1. `cd anyway`
1. Add the main repository as your upstream remote: `git remote add upstream https://github.com/data-for-change/anyway`
1. Note that at this stage your workstation isn't ready yet, Please see [DOCKER](docs/DOCKER.md) instructions for feather instructions.

* Get updates whenever you start working: `git pull upstream dev`
* Push to your fork when you've committed your changes and tested them: `git push`. Now make sure CI tests are passing (see Actions tab) and make a pull request from your fork on GitHub

## WSL2

In order to use WSL2, please follow [these official Docker instructions](https://docs.docker.com/desktop/windows/wsl/). Note that although you run Docker from a Linux distribution, you are instructed to install the Docker Desktop app, and specify usage of WSL2

## Docker
We are using DOCKER. See [DOCKER](docs/DOCKER.md)  
See also an [introductory lecture](https://youtu.be/qh-hnPWViZA) by Assaf Dayan.

## Code formatting
### Black
To format the code using black: `black anyway/**/*.py -l 100 anyway` should be executed from the root directory.
Alternatively, one can execute `docker run -v $(pwd):/code jbbarth/black anyway -l 100` to run the command with docker.
       
## Testing
### Pylint
To run pylint tests: `pylint -j $(nproc) anyway tests && pytest -m "not browser" ./tests`

 
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
