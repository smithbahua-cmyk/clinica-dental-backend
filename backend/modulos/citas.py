from datetime import date, time
from flask import render_template, request, redirect, jsonify
from bson.objectid import ObjectId


def registrar_rutas_citas(app, db):
    citas = db["citas"]
    doctores = db["doctores"]  # lo necesitamos para llenar el combo de doctores

    @app.after_request
    def permitir_api_reservas(response):
        # El formulario público está alojado en Netlify y consulta este backend.
        if request.path in ("/api/doctores", "/api/reservas"):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.route("/api/doctores")
    def api_doctores():
        lista = doctores.find({}, {"nombre": 1, "especialidad": 1, "estado": 1})
        return jsonify([
            {"id": str(d["_id"]), "nombre": d.get("nombre", ""),
             "especialidad": d.get("especialidad", "")}
            for d in lista if d.get("estado", "activo") == "activo"
        ])

    @app.route("/api/reservas", methods=["POST"])
    def api_reservas():
        datos = request.get_json(silent=True)
        if not isinstance(datos, dict):
            return jsonify({"mensaje": "Envía los datos de la cita en formato JSON."}), 400

        campos = ("paciente_nombre", "paciente_email", "paciente_telefono",
                  "doctor_id", "fecha", "hora", "motivo")
        if any(not isinstance(datos.get(c), str) or not datos[c].strip() for c in campos):
            return jsonify({"mensaje": "Completa todos los campos de la cita."}), 400

        try:
            fecha = date.fromisoformat(datos["fecha"].strip()).isoformat()
            hora = time.fromisoformat(datos["hora"].strip()).strftime("%H:%M")
        except ValueError:
            return jsonify({"mensaje": "La fecha o la hora no es válida."}), 400

        if not ObjectId.is_valid(datos["doctor_id"]):
            return jsonify({"mensaje": "Selecciona un doctor válido."}), 400
        doctor_id = ObjectId(datos["doctor_id"])
        doctor = doctores.find_one({"_id": doctor_id})
        if not doctor or doctor.get("estado", "activo") != "activo":
            return jsonify({"mensaje": "Ese doctor no está disponible."}), 400

        if citas.find_one({"doctor_id": doctor_id, "fecha": fecha, "hora": hora,
                           "estado": {"$ne": "cancelada"}}):
            return jsonify({"mensaje": "Ese horario ya está ocupado. Elige otro."}), 409

        citas.insert_one({
            "paciente_nombre": datos["paciente_nombre"].strip(),
            "paciente_email": datos["paciente_email"].strip(),
            "paciente_telefono": datos["paciente_telefono"].strip(),
            "doctor_id": doctor_id,
            "fecha": fecha,
            "hora": hora,
            "motivo": datos["motivo"].strip(),
            "estado": "pendiente",
        })
        return jsonify({"mensaje": "Tu cita se registró correctamente."}), 201

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
