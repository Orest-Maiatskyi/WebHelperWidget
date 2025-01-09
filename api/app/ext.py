from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy


cors = CORS()
db = SQLAlchemy()
redis_client = FlaskRedis()
bcrypt = Bcrypt()
jwt = JWTManager()


def init_ext(api):
    cors.init_app(api,
                  origins="http://127.0.0.1:3000/*",
                  methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    db.init_app(api)
    redis_client.init_app(api)
    redis_client.ping()
    bcrypt.init_app(api)
    jwt.init_app(api)
