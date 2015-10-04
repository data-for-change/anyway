In the python code, instead of writing a message string like `'Message'`, use `gettext(u'Message In English')` (see `main.py`)
Dont forget to import gettext:

```from flask.ext.babel import gettext, ngettext```

In the templates, instead of writing strings like `<title>ANYWAY</title>`, use `<title>{{ gettext('ANYWAY - Influencing in Any Way') }}</title>` (See `templates/index.html`)

After adding strings they will appear in English as they are (Babel's instructions suggest these strings be English). if you wish to add Hebrew translation you should extract the new strings you added by using this command:

```pybabel extract -F babel.cfg -o messages.pot .```

Then, you need to merge this strings into the Hebrew translation file:

```pybabel update -i messages.pot -d translations```

Then, edit translationa/he/LC_MESSAGES/messages.po, and translate the strings there. Finally, to compile your changes run

``` pybabel compile -d translations```

See https://pythonhosted.org/Flask-Babel/ for more.

Depending on which changes you've made, you might need to commit 3 files (messages.pot, messages.po, messages.mo) 