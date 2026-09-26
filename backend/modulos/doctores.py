from flask import render_template, request, redirect
from bson.objectid import ObjectId


def registrar_rutas_doctores(app, db):
    doctores = db["doctores"]

    @app.route("/ingresar")
    def mostrar_ingresar():
        return render_template("doctores/ingresar.html")

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

    @app.route("/consultar")
    def consultar_doctor():
        lista = list(doctores.find())
        doctor_id = request.args.get("doctor_id")
        doctor = None
        if doctor_id:
            doctor = doctores.find_one({"_id": ObjectId(doctor_id)})
        return render_template("doctores/consultar.html", doctores=lista, doctor=doctor)

    @app.route("/actualizar")
    def mostrar_actualizar():
        lista = list(doctores.find())
        doctor_id = request.args.get("doctor_id")
        doctor = None
        if doctor_id:
            doctor = doctores.find_one({"_id": ObjectId(doctor_id)})
        return render_template("doctores/actualizar.html", doctores=lista, doctor=doctor)

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

    # === AQUÍ ESTABA EL ERROR: la indentación de "lista" y "return" no coincidía ===
    @app.route("/eliminar")
    def mostrar_eliminar():
        lista = list(doctores.find())
        return render_template("doctores/eliminar.html", doctores=lista)

    @app.route("/eliminar-doctor", methods=["POST"])
    def eliminar_doctor():
        id_doctor = request.form["doctor_id"]
        doctores.delete_one({"_id": ObjectId(id_doctor)})
        return redirect("/eliminar")