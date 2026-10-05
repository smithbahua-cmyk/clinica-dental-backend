import os
import re
import secrets
import unicodedata
from datetime import timedelta

from bson import ObjectId
from flask import abort, g, redirect, render_template, request, session
from pymongo.errors import DuplicateKeyError
from werkzeug.security import check_password_hash, generate_password_hash


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', texto.upper())
                   if c.isascii() and c.isalpha())


def clave_inicial(dni, nombres):
    return dni + normalizar(nombres)[:3]


def registrar_rutas_empleados(app, db):
    empleados = db['empleados']
    for campo in ('codigo', 'dni', 'correo'):
        empleados.create_index(campo, unique=True)
    app.permanent_session_lifetime = timedelta(hours=8)

    def csrf_token():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        return session['csrf']

    app.jinja_env.globals['csrf_token'] = csrf_token

    def primer_registro():
        # Activar exclusivamente al ejecutar localmente para dar de alta al primero.
        return (os.getenv('PERMITIR_PRIMER_EMPLEADO') == '1'
                and request.remote_addr in ('127.0.0.1', '::1')
                and request.host.split(':')[0] in ('127.0.0.1', 'localhost')
                and empleados.count_documents({}) == 0)

    @app.before_request
    def proteger_gestion():
        g.empleado = None
        empleado_id = session.get('empleado_id')
        if empleado_id and ObjectId.is_valid(empleado_id):
            g.empleado = empleados.find_one({'_id': ObjectId(empleado_id), 'activo': True})
        if g.empleado:
            session['usuario'] = g.empleado['codigo']
        elif empleado_id:
            session.clear()
        if request.endpoint is None:
            return None
        publicos = {'api_doctores', 'api_reservas', 'login', 'static'}
        inicial = request.endpoint == 'gestionar_empleados' and primer_registro()
        if request.endpoint not in publicos and not inicial and not g.empleado:
            return redirect('/login')
        if request.method == 'POST' and request.endpoint != 'api_reservas':
            esperado = session.get('csrf', '')
            recibido = request.form.get('csrf_token', '')
            if not esperado or not secrets.compare_digest(esperado, recibido):
                abort(400, description='Formulario vencido. Recarga la página e inténtalo de nuevo.')

    @app.after_request
    def evitar_cache_privada(response):
        if request.endpoint not in ('api_doctores', 'api_reservas', 'static'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            empleado = empleados.find_one({'correo': request.form.get('correo', '').strip().lower(), 'activo': True})
            if empleado and check_password_hash(empleado['clave_hash'], request.form.get('clave', '')):
                session.clear()
                session.permanent = True
                session['empleado_id'] = str(empleado['_id'])
                session['usuario'] = empleado['codigo']
                return redirect('/')
            error = 'Correo o clave incorrectos.'
        return render_template('login.html', error=error, primer_registro=primer_registro())

    @app.route('/salir', methods=['POST'])
    def salir():
        session.clear()
        return redirect('/login')

    @app.route('/empleados', methods=['GET', 'POST'])
    def gestionar_empleados():
        error = None
        inicial = primer_registro()
        if request.method == 'POST':
            nombres = ' '.join(request.form.get('nombres', '').strip().upper().split())
            apellidos = ' '.join(request.form.get('apellidos', '').strip().upper().split())
            dni = request.form.get('dni', '').strip()
            correo = request.form.get('correo', '').strip().lower()
            empleado_id = request.form.get('id', '')
            if not normalizar(nombres) or not normalizar(apellidos):
                error = 'Escribe nombres y apellidos válidos.'
            elif not re.fullmatch(r'[0-9]{8}', dni):
                error = 'El DNI debe tener 8 dígitos.'
            elif not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', correo):
                error = 'Escribe un correo válido.'
            elif inicial and empleado_id:
                abort(403)
            else:
                datos = dict(nombres=nombres, apellidos=apellidos, dni=dni, correo=correo,
                             clave_hash=generate_password_hash(clave_inicial(dni, nombres)))
                try:
                    if empleado_id:
                        if not ObjectId.is_valid(empleado_id):
                            abort(400)
                        resultado = empleados.update_one({'_id': ObjectId(empleado_id)}, {'$set': datos})
                        if not resultado.matched_count:
                            abort(404)
                    else:
                        # El índice único resuelve también altas simultáneas.
                        base = normalizar(nombres)[0] + normalizar(apellidos)
                        for numero in range(1, 10001):
                            codigo = base if numero == 1 else base + str(numero)
                            try:
                                empleados.insert_one(dict(datos, codigo=codigo, activo=True))
                                break
                            except DuplicateKeyError:
                                if empleados.find_one({'$or': [{'dni': dni}, {'correo': correo}]}):
                                    raise
                        else:
                            abort(409, description='No se pudo asignar un código. Intenta otra vez.')
                    if inicial:
                        return redirect('/login')
                    return redirect('/empleados?dni=' + dni)
                except DuplicateKeyError:
                    error = 'Ya existe un empleado con ese DNI o correo.'
        seleccionado = None
        clave = None
        if not inicial and request.args.get('dni'):
            seleccionado = empleados.find_one({'dni': request.args['dni'].strip()})
            if seleccionado:
                # Se reconstruye la clave determinista; NO se descifra el hash.
                clave = clave_inicial(seleccionado['dni'], seleccionado['nombres'])
            else:
                error = 'No se encontró ese DNI.'
        lista = [] if inicial else list(empleados.find({}, {'clave_hash': 0}).sort('apellidos', 1))
        return render_template('empleados.html', empleados=lista, empleado=seleccionado,
                               clave=clave, error=error, inicial=inicial)

    @app.route('/empleados/eliminar', methods=['POST'])
    def eliminar_empleado():
        empleado_id = request.form.get('id', '')
        if not ObjectId.is_valid(empleado_id):
            abort(400)
        if empleado_id == session['empleado_id']:
            abort(400, description='No puedes dar de baja tu propia cuenta.')
        # Baja lógica: conserva la identidad y no reutiliza códigos históricos.
        resultado = empleados.update_one({'_id': ObjectId(empleado_id)}, {'$set': {'activo': False}})
        if not resultado.matched_count:
            abort(404)
        return redirect('/empleados')
