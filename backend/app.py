"""
Interfaz grafica (web) - Clinica Rodriguez
----------------------------------------------
Sistema modular: cada modulo (doctores, citas) tiene su propio archivo
dentro de la carpeta modulos/, con sus propias rutas.

Requisito nuevo: pip install flask
Ejecutar: python app.py
Abrir:    http://127.0.0.1:5000
"""

import os
from flask import Flask, render_template
from dotenv import load_dotenv
from pymongo import MongoClient

from modulos.doctores import registrar_rutas_doctores
from modulos.citas import registrar_rutas_citas

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

app = Flask(__name__)

client = MongoClient(MONGO_URI)
db = client["clinica-dental"]


# =========================================================
# INICIO
# =========================================================
@app.route("/")
def inicio():
    return render_template("home.html")


# =========================================================
# Aqui se "conectan" los modulos
# =========================================================
registrar_rutas_doctores(app, db)
registrar_rutas_citas(app, db)


if __name__ == "__main__":
    app.run(debug=True)