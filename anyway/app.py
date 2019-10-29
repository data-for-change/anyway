from flask_sqlalchemy import SQLAlchemy

from anyway.utilities import init_flask

app = init_flask()
db = SQLAlchemy(app)
