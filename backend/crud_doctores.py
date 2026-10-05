"""
CRUD de Doctores - Clinica Dental
----------------------------------
Conecta a MongoDB Atlas (base: clinica-dental, coleccion: doctores)
y permite Crear, Leer, Actualizar y Eliminar doctores desde la consola.

Requisitos:
    pip install pymongo python-dotenv

Configuracion:
    1. Crea un archivo llamado ".env" en la misma carpeta que este script.
    2. Dentro escribe una sola linea asi (con TU connection string real):
    3. Ese archivo .env NO se sube a GitHub (agregalo a tu .gitignore).
"""
import os #te permite acceder a variables del sistema operativo (la usamos para leer el .env)
import sys #te permite, entre otras cosas, cerrar el programa de forma controlada (sys.exit()).
from dotenv import load_dotenv #lee tu archivo .env y carga lo que hay adentro como si fueran variables del sistema.
from pymongo import MongoClient #es el "traductor" que le permite a Python hablar el idioma de MongoDB.
from pymongo.errors import ConnectionFailure #es un tipo de error específico que Python puede detectar si la conexión falla.
from bson.objectid import ObjectId #sirve para manejar los IDs únicos que MongoDB genera para cada documento (los vas a usar en el CRUD).

# --- 1. Cargar variables de entorno (.env) ---
load_dotenv() #le dice a Python "ve y lee el archivo .env que está en esta carpeta".
MONGO_URI = os.getenv("MONGO_URI") #busca dentro de esas variables cargadas la que se llama
#MONGO_URI (la línea que tú escribiste con tu connection string) y la guarda en la variable de Python MONGO_URI.

if not MONGO_URI:
    print("ERROR: No se encontro la variable MONGO_URI.")
    print("Crea un archivo .env con: MONGO_URI=tu_connection_string")
    sys.exit(1)

# --- 2. Conectar a MongoDB Atlas ---
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    #MongoClient(MONGO_URI, ...) — crea el "cliente", es decir, el objeto que va a manejar toda la comunicación con tu cluster de Atlas usando el connection string. El
    #serverSelectionTimeoutMS=5000 le dice "si no logras conectarte en 5 segundos, avísame que falló, no te quedes esperando para siempre".

    client.admin.command("ping")  # fuerza la conexion para validar que funciona
    #envía un comando de prueba ("ping") a MongoDB para confirmar que realmente responde (no basta con crear el objeto client, hay que probar que de verdad hay comunicación).

    print("Conexion exitosa a MongoDB Atlas.\n")
except ConnectionFailure as e:
    print(f"No se pudo conectar a MongoDB: {e}")
    sys.exit(1)

db = client["clinica-dental"]
#le dice "dentro de todo el cluster, quiero trabajar con la base de datos llamada clinica-dental".

doctores = db["doctores"]
#dentro de esa base de datos, quiero trabajar con la colección doctores.


# --- 3. Funciones CRUD ---

def crear_doctor():
    print("\n--- Nuevo Doctor ---")
    nombre = input("Nombre: ").strip()
    especialidad = input("Especialidad: ").strip()
    email = input("Email: ").strip()
    telefono = input("Telefono: ").strip()
    descripcion = input("Descripcion: ").strip()
    estado = input("Estado (activo/inactivo) [activo]: ").strip() or "activo"

    nuevo_doctor = {
        "nombre": nombre,
        "especialidad": especialidad,
        "email": email,
        "telefono": telefono,
        "descripcion": descripcion,
        "estado": estado,
    }

    resultado = doctores.insert_one(nuevo_doctor)
    print(f"\nDoctor creado con id: {resultado.inserted_id}")

    

""" 
resultado = doctores.insert_one(nuevo_doctor)

Aquí nuevo_doctor es un diccionario con nombre, especialidad, email, etc. — tú nunca le pones un _id. MongoDB, al ejecutar insert_one, automáticamente le agrega un campo _id con un valor único (un ObjectId) antes de guardar el documento. Es decir, MongoDB genera ese ID por su cuenta, sin que tú lo pidas explícitamente. Por eso el script después te muestra:
 """

def listar_doctores():
    print("\n--- Lista de Doctores ---")
    registros = list(doctores.find())

    if not registros:
        print("No hay doctores registrados todavia.")
        return

    for doc in registros:
        print(f"\nID: {doc['_id']}")
        print(f"  Nombre       : {doc.get('nombre')}")
        print(f"  Especialidad : {doc.get('especialidad')}")
        print(f"  Email        : {doc.get('email')}")
        print(f"  Telefono     : {doc.get('telefono')}")
        print(f"  Descripcion  : {doc.get('descripcion')}")
        print(f"  Estado       : {doc.get('estado')}")


def actualizar_doctor():
    print("\n--- Actualizar Doctor ---")
    id_texto = input("Ingresa el ID del doctor a actualizar: ").strip()

    try:
        id_obj = ObjectId(id_texto)
#""" id_obj = ObjectId(id_texto)

#Esta línea es la clave: convierte ese texto en un objeto especial de tipo ObjectId (el mismo tipo de dato #que usa MongoDB internamente para sus IDs). No es lo mismo un string "65f3a1..." que un ObjectId
#("65f3a1...#") — se ven parecidos al imprimirlos, pero para MongoDB son tipos de dato distintos. """

    except Exception:
        print("ID invalido.")
        return

    doctor = doctores.find_one({"_id": id_obj})
    if not doctor:
        print("No se encontro ningun doctor con ese ID.")
        return

    print("Deja el campo vacio si no quieres cambiarlo.")
    nombre = input(f"Nombre [{doctor.get('nombre')}]: ").strip()
    especialidad = input(f"Especialidad [{doctor.get('especialidad')}]: ").strip()
    email = input(f"Email [{doctor.get('email')}]: ").strip()
    telefono = input(f"Telefono [{doctor.get('telefono')}]: ").strip()
    descripcion = input(f"Descripcion [{doctor.get('descripcion')}]: ").strip()
    estado = input(f"Estado [{doctor.get('estado')}]: ").strip()

    cambios = {}
    if nombre: cambios["nombre"] = nombre
    if especialidad: cambios["especialidad"] = especialidad
    if email: cambios["email"] = email
    if telefono: cambios["telefono"] = telefono
    if descripcion: cambios["descripcion"] = descripcion
    if estado: cambios["estado"] = estado

    if not cambios:
        print("No se hicieron cambios.")
        return

    doctores.update_one({"_id": id_obj}, {"$set": cambios})
    print("Doctor actualizado correctamente.")


def eliminar_doctor():
    print("\n--- Eliminar Doctor ---")
    id_texto = input("Ingresa el ID del doctor a eliminar: ").strip()

    try:
        id_obj = ObjectId(id_texto)
    except Exception:
        print("ID invalido.")
        return

    resultado = doctores.delete_one({"_id": id_obj})
    if resultado.deleted_count == 1:
        print("Doctor eliminado correctamente.")
    else:
        print("No se encontro ningun doctor con ese ID.")


# --- 4. Menu principal ---

def menu():
    while True:
        print("\n========== CRUD DOCTORES - Clinica Dental ==========")
        print("1. Crear doctor")
        print("2. Ver todos los doctores")
        print("3. Actualizar doctor")
        print("4. Eliminar doctor")
        print("5. Salir")
        opcion = input("Elige una opcion (1-5): ").strip()

        if opcion == "1":
            crear_doctor()
        elif opcion == "2":
            listar_doctores()
        elif opcion == "3":
            actualizar_doctor()
        elif opcion == "4":
            eliminar_doctor()
        elif opcion == "5":
            print("Saliendo...")
            break
        else:
            print("Opcion invalida, intenta de nuevo.")


if __name__ == "__main__":
    menu()
