---
name: Localize Widget
about: Provide description and implementation details
title: 'Localize Widget - '
labels: 'localization'
assignees: ''

---

**Widget ID**
Widget ID

**Widget Fields**
Fields in Widget to localize (For example - accident_severity)

**Dictionaries Missing**
Dictionaries to create (For example - Accident Severity Dictionary)
Note: Create a dictionary containing using the DB code as a key and not the Hebrew translation (for example `{1: 'fatal'}` rather than `{'קטלנית': 'fatal'}`)

**Widget Title**
Current Widget Title for localization, if exists.

**Additional context**
- Existing translation to CBS fields - [see here](https://docs.google.com/spreadsheets/d/1gjeMsPEWayMZ4Z0tGDKkL0mDsXgIRQ4-aAadRpEP9Oc/edit?usp=sharing)
- Existing CBS Fields - [see here](https://docs.google.com/spreadsheets/d/1qaVV7NKXVYNmnxKZ4he2MKZDAjWPHiHfq-U5dcNZM5k/edit?usp=sharing)
(Note - if translation in file is not adequate - please create a better translation)

**Flask Babel**
For updating messages.pot with all strings for translation - use the following command: `pybabel extract -F babel.cfg -o messages.pot .`
For updating existing po files with new strings: `pybabel update -i messages.pot -d translations`
