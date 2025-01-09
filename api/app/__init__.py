from flask import Flask

from app.config import current_config
from app.ext import *

api = Flask(__name__)
api.config.from_object(current_config)

init_ext(api)
