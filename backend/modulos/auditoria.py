from datetime import datetime, timezone
from flask import g


def registrar_evento(db, cita, observacion, mongo_session, externo=False):
    empleado = None if externo else g.empleado
    db['auditoria_citas'].insert_one({
        'cita_id': cita['_id'],
        'paciente': cita['paciente_nombre'],
        'fecha_cita': cita['fecha'] + ' ' + cita['hora'],
        'fecha_modificacion': datetime.now(timezone.utc),
        'usuario': empleado['codigo'] if empleado else 'Cliente Externo',
        'nombre_empleado': (empleado['nombres'] + ' ' + empleado['apellidos']) if empleado else 'Cliente Externo',
        'observacion': observacion,
        'status': cita['estado'].upper(),
    }, session=mongo_session)


def crear_cita_auditada(db, datos, observacion='Generando cita', externo=False):
    # Un ObjectId estable evita cambiar la referencia si se reintenta la transacción.
    from bson import ObjectId
    cita = dict(datos, _id=ObjectId())

    def operacion(sesion):
        db['citas'].insert_one(dict(cita), session=sesion)
        registrar_evento(db, cita, observacion, sesion, externo)

    with db.client.start_session() as sesion:
        sesion.with_transaction(operacion)
    return cita


def actualizar_cita_auditada(db, cita_id, cambios, observacion):
    from flask import abort
    from pymongo import ReturnDocument

    def operacion(sesion):
        cita = db['citas'].find_one_and_update(
            {'_id': cita_id}, {'$set': cambios},
            return_document=ReturnDocument.AFTER, session=sesion)
        if not cita:
            abort(404, description='Cita no encontrada.')
        registrar_evento(db, cita, observacion, sesion)

    with db.client.start_session() as sesion:
        sesion.with_transaction(operacion)
