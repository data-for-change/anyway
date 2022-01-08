Code Directory Tree Structure
=============================

This page describes the structure of the code comprising the project.

## Python
All Python modules reside in the `anyway` subdirectory:
* `flask_app.py`: main server code, using the Flask web framework.
* `models.py`: definitions for the classes used in the Python code, and through SQLAlchemy, definitions for the corresponding database tables.
* `process.py`: loading data from the Central Bureau of Statistics (CBS, למ"ס), of which a sample resides in `static/data/cbs`.
* `clusters_calculator.py`, `globalmaptiles.py`: algorithm for calculating clusters of markers to be sent instead of individual ones in far zoom level.
* `localization.py`: translation of field values.
* `field_names.py`: English names of fields from CBS data.
* `constants.py`: default values for map parameters.
* `base.py`, `config.py`, `database.py`: configuration for database and web access.
* `oauth.py`: user authentication.
* `utilities.py`: miscellaneous utilities.

One file, called `main.py` resides in the root of the repository. This file contains all commands needed to manipulate the database and run the server. Run `./main.py --help` for help.

## Widgets
Widgets can be thought of as individual data collections which are produced for consumtion by the end-user. For example: AccidentCountByAccidentTypeWidget which returns, well, the accident count by accident type 

### Structure
Widgets are currently divided into 2 kinds/classes (but this could change in the future by adding more sub-classes): Urban and Suburban, both of these are a subclass of the Widget class, and a superclass for all widgets. For example, AccidentCountByAccidentTypeWidget is a subclass of SubUrbanWidget which is itself a subclass of the Widget class

### Adding new widgets
Every Widget, defined by its own class, should be created in a new file under the relevant module/directory, in snake_casing. In addition, in order to import the newly added widget, you need to add it to the super classe's \_\_init\_\_.py file. For example, if we were to add a new SubUrbanWidget named NewWidget, we should:
1. Create a file named new_widget.py under the suburban_widgets directory
2. Write the code for the new widget as a class named NewWidget(SubUrbanWidget)
3. Add it to the import statement in the \_\_init\_\_.py file of the suburban_widgets module

## Jinja2 Templates
We use Jinja2 for templates, to allow embedding data into HTML files. All templates reside in `templates`.
* `index.html`: template for main page, containing the map and mostly everything else too.
The rest of the templates are used for administration purposes.

## Javascript
All Javascript code resides in `static/js`.
* `app.js`: main client-side code, defining the Backbone models and creating the Google Map.
* `sidebar.js`: creates and handles the sidebar filters menu and list of displayed markers.
* `marker.js`: handles individual markers and the info window that pops when clicked.
* `localization.js`, `constants.js`: contain the same information as in the similarly named Python modules.
* `inv_dict.js`, `veh_dict.js`: strings used for displaying involved/vehicle information.
* `tour.js`: "getting started" tour that pops on the first use of the app.

## CSS
All CSS stylesheets reside in `static/css`.
* `style.css`: main stylesheet for the map, etc.
* `markers.css`: styles for individual markers.
* `accordion.css`: styles for the marker info window.
