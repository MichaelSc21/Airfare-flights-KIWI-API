from flask import Flask
from flask_wtf.csrf import CSRFProtect
import Getting_data.API_details as API_details



app = Flask(__name__)
app.secret_key = API_details.FORMS_KEY
csrf = CSRFProtect(app)
csrf.init_app(app)

from flask_app import routes