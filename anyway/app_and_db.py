from . import utilities
from flask_sqlalchemy import SQLAlchemy

app = utilities.init_flask()
db = SQLAlchemy(app)
