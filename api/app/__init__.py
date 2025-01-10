from flask import Flask

from app.config import current_config
from app.ext import *

app = Flask(__name__)
app.config.from_object(current_config)

init_ext(app)


from app.database import *


with app.app_context():
    if app.config.get('DEBUG'):
        db.drop_all()
        db.create_all()
        app.logger.info('The application was launched in DEBUG mode, all DB columns were dropped!')
    db.create_all()


@app.errorhandler(DAOException)
def handle_dao_error(error):
    return {'error': 'Internal Server Error', 'message': 'Something went wrong :('}, 500
