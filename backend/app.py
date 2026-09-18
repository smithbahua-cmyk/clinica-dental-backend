"""
Interfaz grafica (web) - Clinica Rodriguez
----------------------------------------------
4 interfaces separadas, cada una con su propio menu y su propio proposito:
  - Ingresar doctor  (cajas de texto vacias)
  - Consultar doctor (combo + cajas deshabilitadas, solo para ver)
  - Actualizar doctor (combo + cajas habilitadas, para modificar)
  - Eliminar doctor  (combo + boton eliminar)

Requisito nuevo: pip install flask
Ejecutar: python app.py
Abrir:    http://127.0.0.1:5000
"""

import os
from flask import Flask, render_template, request, redirect
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

app = Flask(__name__)

client = MongoClient(MONGO_URI)
db = client["clinica-dental"]
doctores = db["doctores"]


# =========================================================
# INICIO
# =========================================================
@app.route("/")
def inicio():
    return render_template("home.html")


# =========================================================
# INGRESAR DOCTOR
# =========================================================

# Muestra el formulario vacio
@app.route("/ingresar")
def mostrar_ingresar():
    return render_template("ingresar.html")


# Recibe lo escrito en el formulario y lo guarda
@app.route("/guardar", methods=["POST"])
def guardar_doctor():
    nuevo = {
        "nombre": request.form["nombre"],
        "especialidad": request.form["especialidad"],
        "email": request.form["email"],
        "telefono": request.form["telefono"],
        "descripcion": request.form["descripcion"],
        "estado": request.form.get("estado", "activo"),
    }
    doctores.insert_one(nuevo)
    return redirect("/ingresar")


# =========================================================
# CONSULTAR DOCTOR (solo lectura)
# =========================================================
@app.route("/consultar")
def consultar_doctor():
    lista = list(doctores.find())

    doctor_id = request.args.get("doctor_id")  # viene de ?doctor_id=... en la URL
    doctor = None
    if doctor_id:
        doctor = doctores.find_one({"_id": ObjectId(doctor_id)})

    return render_template("consultar.html", doctores=lista, doctor=doctor)


# =========================================================
# ACTUALIZAR DOCTOR
# =========================================================

# Muestra el combo, y si ya eligieron un doctor, tambien el formulario lleno
@app.route("/actualizar")
def mostrar_actualizar():
    lista = list(doctores.find())

    doctor_id = request.args.get("doctor_id")
    doctor = None
    if doctor_id:
        doctor = doctores.find_one({"_id": ObjectId(doctor_id)})

    return render_template("actualizar.html", doctores=lista, doctor=doctor)


# Recibe los cambios del formulario y actualiza ese doctor
@app.route("/guardar-cambios", methods=["POST"])
def guardar_cambios():
    id_doctor = request.form["id"]
    cambios = {
        "nombre": request.form["nombre"],
        "especialidad": request.form["especialidad"],
        "email": request.form["email"],
        "telefono": request.form["telefono"],
        "descripcion": request.form["descripcion"],
        "estado": request.form.get("estado", "activo"),
    }
    doctores.update_one({"_id": ObjectId(id_doctor)}, {"$set": cambios})
    return redirect("/actualizar")


# =========================================================
# ELIMINAR DOCTOR
# =========================================================

# Muestra el combo con todos los doctores
@app.route("/eliminar")
def mostrar_eliminar():
   lista = list(doctores.find().sort("nombre", 1))   # ← agregaste .sort("nombre", 1)
    return render_template("eliminar.html", doctores=lista)


# Recibe el id elegido en el combo y lo elimina
@app.route("/eliminar-doctor", methods=["POST"])
def eliminar_doctor():
    id_doctor = request.form["doctor_id"]
    doctores.delete_one({"_id": ObjectId(id_doctor)})
    return redirect("/eliminar")


if __name__ == "__main__":
    app.run(debug=True)
