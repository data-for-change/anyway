Contributing to ANYWAY
======================

OMG. OMG. OMG. We are really glad you are joining the team!  We set up a contributor's guide that explains all about [setting up ANYWAY's development environment](DOCKER.md) - prepare to be amazed.

![Contributors guide](../static/img/anyway.png)

This page contains information about reporting issues as well as some tips and
guidelines useful to experienced open source contributors.

## Topics

* [Issues and Bugs](#issues-and-bugs)
* [Feature Requests](#feature-requests)
* [Coding Rules](#coding-rules)
* [Contribution Tips](#contribution-tips)

## Issues and Bugs

As one of the teams working in the Public Knowledge Workshop, we put data
credibility first. If you find any discrepancies between the presented data and
the information in the used open-source databases, please let us know.
Also, if you happen to stumble upon a bug, don't hesitate and raise a flag and we will get it fixed. You can send any your reports to [anyway@anyway.co.il](mailto:anyway@anyway.co.il).
Don't forget to mention which operating system and browser you were using, so we can easily track down the issue.

If you are already digging through the code and our [website](https://www.anyway.co.il) and you happen to find a bug, please go ahead and [open a new issue](https://github.com/hasadna/anyway/issues).
 Just remember to look through the pre-existing ones to make sure there are no duplicates. Even better if you can take it on yourself, then we encourage you to report the issue, assign yourself and submit a Pull Request with a fix.

**Issue Report Format:**

* **Title** `**Issue** One-liner regarding the issue you discovered`

* **Description** Explain why this is a bug, how to reproduce it and on which OS and browser you encounter it. If you can't fix it yourself, try to suggest a fix or any leads you found in the code.
Add any errors thrown from a non-minified stack trace, if possible.
Attach any screenshots that are relevant.

Once you are done with the basics, don't forget to tag it with `bug` and `1 - Ready` and other relevant tags from the following list: `backend`, `frontend`, `easy`, `good-first-issue`, `news-flash-report`

## Feature Requests

New feature requests are more than welcome, just don't forget to pass them by the team and also check the issue list to avoid duplicates.
We generally submit **major changes** via direct email to our [mail center](mailto:anyway@anyway.co.il) and request **small changes** by [submitting an issue](https://github.com/hasadna/anyway/issues).

**Feature Request Format:**

* **Title** `**Feature** One-liner on the feature you'd like to implement`

* **Description** Elaborate on the feature, why it is needed and the time frame in which you'd like it to be completed. If you have any suggestions or advice, share it with the team.
Also, mockups are very helpful - so you can try to make a simple screenshot to help us understand the concept.

Now tag it with `enhancement` and `1 - Ready` and other relevant tags from the following list: `backend`, `frontend`, `easy`,

## Coding Rules

**Branch Names**

Branch naming convention is as following:

```
TYPE-ISSUE_ID-DESCRIPTION

examples:
feat-1247-add-vision-zero-widgets
refactor-1242-move-rank-field-to-meta
```
When `TYPE` can be:
* **feat** - is a new feature
* **doc** - documentation only changes
* **cicd** - changes related to CI/CD system
* **fix** - a bug fix
* **refactor** -  code change that neither fixes a bug nor adds a feature

**All PRs must include commit message with the changes description!**

Branching system:
*master* - used for production <br>
*dev* - anything else <br>

**Working Procedure**

A standard procedure for working on an issue would be to:
1. Change to dev branch: `git checkout dev` and pull changes from upstream `git pull upstream dev`
2. Create new branch from `dev` , like: `refactor-1242-move-rank-field-to-meta`
3. Work on your new branch - commit - repeat
4. Change to dev branch: `git checkout dev` and git pull at `dev`: `git pull upstream dev`
5. Change to your branch: `git checkout dev` and merge: `git merge your-branch-name` and solve conflicts if they exist
6. Push branch dev to **your forked directory** using `git push origin dev` and open PR to hasadna's `dev` branch.
7. Get a code review approval / reject
8. After approval, merge your PR
9. Delete your branch after merge

**Clean Code**

See the following Python and JavaScript format guidelines and stick to them:
* [Airbnb JavaScript Guidelines] (https://github.com/airbnb/javascript)
* [Python Style Guide] (https://www.python.org/dev/peps/pep-0008/)

Universally formatted code is crucial in open source projects and promotes ease of writing, reading and maintenance.

**Logging**

Do not use `print` for messages in Python code! Instead, use the `logging` class.
Remember that log messages are very helpful for debugging server issues, so add as much information as you can.

**Unit Tests**

All unit tests can be found in the "tests" folder. When adding a new test, make sure you follow this pattern: `test_*.py` (e.g.: `test_bounding_box_query.py`).
To run the tests, use the following command:

    python -m unittest discover tests

Note that you can add a pattern so the discover command will find only your file as such:

    python -m unittest discover tests "*bounding*.py"


Also, if you add an empty file, named `__init__.py` at tests folder, you'll be able to run more commands as:

    python -m unittest test_module.TestClass.test_method

(e.g.: `python -m unittest tests.test_bounding_box_query`)

**Pull Requests**

Code review comments may be added to your pull requests, keep an eye out for necessary changes before merge approval. If the maintainer decides that your code is good, it will be merged to ANYWAY's `dev` repository.
On your pull requests, don't forget to reference to the issue using the Linked issues section of the Pull Request. Also, shortly summarize the changes made and list any
known-issues after the future merge (open new issues for them and reference to them as well).

**Squash Comment**

Before you make a pull request, squash your commits into logical units of work using `git rebase -i` and `git push -f`.

## Contribution Tips

**Remote Volunteering**

On regular days, the team meets each Monday evening at Google Campus, Tel Aviv.
However, during these days of covid-19 - we're volunteering remotely and meet our teammates once a week via ZOOM.
You are more than welcome to join us - [email us](mailto:anyway@anyway.co.il).

**Slack**

[Our Slack channel](https://hasadna.slack.com/) is our communication tool and is connected to the relevant git notifications.
If you want to join us, [Email us](mailto:anyway@anyway.co.il) and we'll add you to our workspace.

**Points of Contacts**

* galraij - Project Entrepreneur and Manager
* atalyaalon - Head of R&D, BackEnd and DevOps Team Leader
* assafdayan - Back End Tech Leader
* yuvalbl - Front End Team Leader
* inbalbeka - Product Team Leader
* Mano3 - Algorithms Team Leader
* Alonr6 and elashahar01 - Data Team Leaders

(contributors: feel free to edit the file, add yourselves to the POC list, and share any tips that you find helpful)
