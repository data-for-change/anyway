from flask_sqlalchemy import SQLAlchemy

from anyway import utilities

app = utilities.init_flask()
db = SQLAlchemy(app)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()
