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
from modulos.empleados import registrar_rutas_empleados
from datetime import timezone
from zoneinfo import ZoneInfo

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                  SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE', '0') == '1')

@app.template_filter('hora_lima')
def hora_lima(valor):
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(ZoneInfo('America/Lima')).strftime('%d/%m/%Y %H:%M:%S')


client = MongoClient(MONGO_URI)
db = client[os.environ['MONGO_DB']]
registrar_rutas_empleados(app, db)
db['auditoria_citas'].create_index([('cita_id', 1), ('fecha_modificacion', 1)])


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