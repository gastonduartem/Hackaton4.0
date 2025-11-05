# Importa Flask y la base de datos
import os
from flask import Flask
from models import db

# Inicializa la aplicación Flask
app = Flask(__name__)

# Configuración de la base de datos (env o SQLite local)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///corrupt.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # evita advertencias innecesarias

# Vincula SQLAlchemy con la aplicación Flask
db.init_app(app)

# Crea todas las tablas definidas en models.py si no existen
with app.app_context():
    db.create_all()
