from flask import Flask, Blueprint

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
        UserDAO.create_user('Jon', 'Don', 'jon_don@gamil.com',
                            bcrypt.generate_password_hash('12345JonDon!'), True)
        app.logger.info('The application was launched in DEBUG mode, all DB columns were dropped!')
    db.create_all()


from app.apis import *


api_bp = Blueprint('api', __name__)
api_bp.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(api_bp, url_prefix='/api/v1')


# Callback function to check if a JWT exists in the redis blocklist
@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
    return redis_client.get(jwt_payload["jti"]) is not None


@app.errorhandler(DAOException)
def handle_dao_error(error):
    return {'error': 'Internal Server Error', 'message': 'Something went wrong :('}, 500
