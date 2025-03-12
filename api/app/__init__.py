import os
from flask import Flask, Blueprint

from app.config import current_config
from app.ext import *

app = Flask(__name__)
app.config.from_object(current_config)

init_ext(app)


from app.database import *


with app.app_context():

    # https://stackoverflow.com/a/9476701
    if not app.config.get('DEBUG') or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        db.drop_all()
        db.create_all()
        UserDAO.create_user('Jon', 'Don', 'jon_don@gamil.com',
                            bcrypt.generate_password_hash('12345JonDon!'), True)
        user = UserDAO.get_user_by_email('jon_don@gamil.com')
        db.session.close()
        ApiKeyDAO.create_api_key(user.uuid)
        app.logger.info('The application was launched in DEBUG mode, all DB columns were dropped!')
    db.create_all()


from app.apis import *


api_bp = Blueprint('api', __name__)

api_bp.register_blueprint(
    cookie_auth_bp if 'cookies' in app.config.get('JWT_TOKEN_LOCATION') else header_auth_bp, url_prefix='/auth')

api_bp.register_blueprint(confirm_email_bp, url_prefix='/confirm_email')
api_bp.register_blueprint(account_bp, url_prefix='/account')
api_bp.register_blueprint(api_key_bp, url_prefix='/account/api_key')
api_bp.register_blueprint(fine_tuning_bp, url_prefix='/account/fine_tuning')
api_bp.register_blueprint(training_file_bp, url_prefix='/account/fine_tuning/training_file')
app.register_blueprint(api_bp, url_prefix='/api/v1')


# Callback function to check if a JWT exists in the redis blocklist
@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
    return redis_client.get(jwt_payload["jti"]) is not None


@app.errorhandler(DAOException)
def handle_dao_error(error):
    return {'error': 'Internal Server Error', 'message': 'Something went wrong :('}, 500
