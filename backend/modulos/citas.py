from flask import render_template, request, redirect
from bson.objectid import ObjectId


def registrar_rutas_citas(app, db):
    citas = db["citas"]
    doctores = db["doctores"]  # lo necesitamos para llenar el combo de doctores

    @app.route("/reservar")
    def mostrar_reservar():
        lista_doctores = list(doctores.find())
        return render_template("citas/reservar.html", doctores=lista_doctores)

    @app.route("/guardar-cita", methods=["POST"])
    def guardar_cita():
        doctor_id = request.form["doctor_id"]
        fecha = request.form["fecha"]
        hora = request.form["hora"]

        choque = citas.find_one({
            "doctor_id": ObjectId(doctor_id),
            "fecha": fecha,
            "hora": hora,
            "estado": {"$ne": "cancelada"}
        })
        if choque:
            return "Ese horario ya está ocupado, elige otro. <a href='/reservar'>Volver</a>"

        nueva = {
            "paciente_nombre": request.form["paciente_nombre"],
            "paciente_email": request.form["paciente_email"],
            "paciente_telefono": request.form["paciente_telefono"],
            "doctor_id": ObjectId(doctor_id),
            "fecha": fecha,
            "hora": hora,
            "motivo": request.form["motivo"],
            "estado": "pendiente",
        }
        citas.insert_one(nueva)
        return redirect("/reservar")

    @app.route("/mis-citas")
    def mostrar_mis_citas():
        return render_template("citas/mis_citas.html", citas=None)

    @app.route("/buscar-citas", methods=["POST"])
    def buscar_citas():
        email = request.form["email"]
        encontradas = list(citas.find({"paciente_email": email}))
        # a cada cita le agregamos el nombre del doctor para mostrarlo en la tabla
        for c in encontradas:
            doc = doctores.find_one({"_id": c["doctor_id"]})
            c["doctor_nombre"] = doc["nombre"] if doc else "Doctor no encontrado"
        return render_template("citas/mis_citas.html", citas=encontradas)

    @app.route("/actualizar-cita")
    def mostrar_actualizar_cita():
        lista_citas = list(citas.find())
        for c in lista_citas:
            doc = doctores.find_one({"_id": c["doctor_id"]})
            c["doctor_nombre"] = doc["nombre"] if doc else "Doctor no encontrado"
        return render_template("citas/actualizar_cita.html", citas=lista_citas)

    @app.route("/guardar-cambios-cita", methods=["POST"])
    def guardar_cambios_cita():
        cita_id = request.form["cita_id"]
        citas.update_one(
            {"_id": ObjectId(cita_id)},
            {"$set": {
                "fecha": request.form["fecha"],
                "hora": request.form["hora"],
                "estado": request.form["estado"],
            }}
        )
        return redirect("/actualizar-cita")

    @app.route("/panel-citas")
    def panel_citas():
        todas = list(citas.find())
        for c in todas:
            doc = doctores.find_one({"_id": c["doctor_id"]})
            c["doctor_nombre"] = doc["nombre"] if doc else "Doctor no encontrado"
        return render_template("citas/panel_citas.html", citas=todas)

    # NUEVA: cancelar una cita desde el panel (no la borra, solo cambia su estado)
    @app.route("/cancelar-cita", methods=["POST"])
    def cancelar_cita():
        cita_id = request.form["cita_id"]
        citas.update_one({"_id": ObjectId(cita_id)}, {"$set": {"estado": "cancelada"}})
        return redirect("/panel-citas")
