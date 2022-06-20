from ast import Or
from datetime import date
from distutils import text_file
from logging.config import listen
from re import template
from colorama import Cursor
from flask import Flask, jsonify, request, make_response, render_template, session
from config import config
from flask_mysqldb import MySQL
import jwt
from functools import wraps
from waitress import serve


# instancia de flask/sirve para saber si este archivo que se esta ejecutando es el principal
app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = '0b7807f50046438aa179c6987907704e'

# conexion a la bdd con el parametro de esta aplicacion
conexion = MySQL(app)
# login

# decorador que llama y guarda los datos en un jwt


def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'Alerta': 'No hay token'})
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return jsonify({'Alerta': 'Token Invalido'})
    return decorated

# metodo para detectar la session del usuario


@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('registrar.html')
    if request.form['blogin'] == "Ingresar":
        return render_template('login.html')
    else:
        return 'Ya esta logueado.'


@app.route('/registrar', methods=['POST'])
def registrarUser():

    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT * FROM login WHERE usuario = '{0}' AND password = '{1}'".format(
            request.form['username'], request.form['password'])
        query = cursor.execute(sql)
        #datos = cursor.fetchall()

        if query == 1:
            return 'el usuario ya existe'
        else:

            rol = request.form['tipo']
            verif = request.form['confirmacion']
            # print(verif)
            # return("".format(request.form['pass']))

            if rol == 'cliente':
                sql = """INSERT INTO login (usuario, password, tipo) VALUES ('{0}','{1}','{2}')""".format(request.form['username'],
                                                                                                        request.form['password'], request.form['tipo'])
                cursor.execute(sql)
                conexion.connection.commit()

                return render_template('login.html')

            elif rol == 'empleado' and verif == 'empleados-galacticos':
                sql = """INSERT INTO login (usuario, password, tipo) VALUES ('{0}','{1}','{2}')""".format(request.form['username'],
                request.form['password'], request.form['tipo'])
                cursor.execute(sql)
                conexion.connection.commit()

                return render_template('login.html')
            else:
                return make_response('No se puede verificar', 403)

        # else:
            # return 'el usuario ya existe'

    except Exception as ex:
        raise Exception(ex)


# metodo para login de usuario, devuelve el jwt dependiendo de si es empleado o cliente, tambien redirige a las vistas correspondientes
@app.route('/login', methods=['POST'])
def login():

    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT * FROM login WHERE usuario = '{0}' AND password = '{1}'".format(
            request.form['username'], request.form['password'])
        query = cursor.execute(sql)
        datos = cursor.fetchall()

        if query == 1:

            for fila in datos:
                rol = fila[3]

            if rol == 'cliente':
                session['logged_in'] = True

                token = jwt.encode({
                    'usuario': request.form['username'],
                    'tipo usuario': rol,
                },
                    app.config['SECRET_KEY'])
                llave = token
                return render_template('clientes.html', llave=llave)

            elif rol == 'empleado':

                token = jwt.encode({
                    'usuario': request.form['username'],
                    'tipo usuario': rol,
                },
                    app.config['SECRET_KEY'])
                llave = token
                return render_template('empleados.html', llave=llave)

            else:
                return make_response('No se puede verificar', 403)

        else:
            return 'el usuario no existe'

    except Exception as ex:
        raise Exception(ex)


# metodo de cierre de session
@app.route('/logout', methods=['POST'])
def logout():
    session['logged_in'] = False
    return render_template('login.html')


@app.route('/habitaciones', methods=['GET'])
def mostrar_habitaciones():  # metodo que lista las habitaciones creadas en la BDD
    try:

        cursor = conexion.connection.cursor()
        sql = "SELECT id, numero, precioPorDia FROM habitaciones"
        cursor.execute(sql)
        datos = cursor.fetchall()
        print(datos)
        cuartos = []  # creo una lista vacia para poder guardar las habitaciones que vienen de datos

        for fila in datos:  # for para poder recorrer las habitaciones que vienen en forma de tupla en la variable datos
            # en este diccionario se almacenan los datos para despues convertirlos a json
            cuarto = {'id': fila[0], 'numero': fila[1],
                'precioPorDia': fila[2]}
            cuartos.append(cuarto)
            # retorna un diccionario con la key habitaciones, los valores de cuartos y una mensaje
        return jsonify({'habitaciones': cuartos, 'mensaje': "las habitaciones estan listadas"})

    except Exception as ex:
        return ex


@app.route('/habitaciones-reservadas', methods=['GET'])
# metodo que lista las habitaciones reservadas. Estas tiene un estado de 1. en cambio las que se encuentran libres tiene un estado 0
def mostrar_habitaciones_reservadas():
    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT * FROM reservas"
        cursor.execute(sql)
        datos = cursor.fetchall()
        print(datos)
        cuartos = []

        for fila in datos:
            cuarto = {'id': fila[0], 'numero': fila[1],
                'inicio_resv': fila[2], 'fin_resv': fila[3]}
            cuartos.append(cuarto)

        return jsonify({'habitaciones': cuartos, 'mensaje': "las habitaciones estan listadas"})

    except Exception as ex:
        return ex

# metodo que busca la habitacion solicitada con numero, valor que que se le pasa a la url


def buscar_cuartobd(numero):
    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT id, numero, precioPorDia FROM habitaciones WHERE numero = '{0}'".format(
            numero)
        cursor.execute(sql)
        datos = cursor.fetchone()
        if datos != None:
            cuarto = {'id': datos[0], 'numero': datos[1],
                'precioPorDia': datos[2]}
            return cuarto
        else:
            return None
    except Exception as ex:
        raise ex


# dentro de numero va venir el numero de la habitacion que se quiere buscar.
# si se encuentra en la bdd retorna la habitacion con sus valores. En caso contrario retorna un mensaje
@app.route('/habitaciones/empleado/<numero>', methods=['GET'])
def buscar_habitaciones(numero):
    try:
        cuarto = buscar_cuartobd(numero)
        if cuarto != None:
            return jsonify({'habitaciones': cuarto, 'mensaje': "la habitacion ha sido encontrada", 'exito': True})
        else:
            return jsonify({'mensaje': "error habitacion no encontrada", 'exito': False})

    except Exception as ex:
        return jsonify({'mensaje': "Error", 'exito': False})

# metodo para que el empleado pueda registrar habitaciones


@app.route('/empleado/registrar', methods=['POST'])
def registrar_habitaciones():
    try:
        cursor = conexion.connection.cursor()
        numsql = (
            "SELECT * FROM habitaciones WHERE numero = '{0}'").format(request.json['numero'])
        query = cursor.execute(numsql)
        if query == 1:
            return jsonify({'mensaje': "ERROR habitacion registrada ya existe"})
        else:
            if request.json['precioPorDia'] < 0 :
                return jsonify({'mensaje': "No se permiten precios en negativo"})    
            else:
                sql = """INSERT INTO habitaciones (numero, precioPorDia) VALUES ('{0}','{1}')""".format(request.json['numero'],
                request.json['precioPorDia'])
                cursor.execute(sql)
                conexion.connection.commit()
                return jsonify({'mensaje': "habitacion registrada con exito"})
    except Exception as ex:
        return ex


# metodo para que el empleado pueda actualizar info de las habitaciones
# se busca y trae la habitacion por el numero
@app.route('/habitaciones/empleado/actualizar/<numero>', methods=['PUT'])
def actualizar_habitaciones(numero):
    try:
        if request.json['precioPorDia'] < 0 :
            return jsonify({'mensaje': "No se permiten precios en negativo"})
        else:
            cursor = conexion.connection.cursor()
            sql = """UPDATE habitaciones SET precioPorDia = {0} WHERE numero = {3}""".format(
                request.json['precioPorDia'], numero)
            cursor.execute(sql)
            conexion.connection.commit()
            return jsonify({'mensaje': "habitacion actualizada"})

    except Exception as ex:
        return ex


# metodo para que el empleado pueda eliminar una habitacion
@app.route('/habitaciones/empleado/borrar/<numero>', methods=['DELETE'])
def eliminar_habitaciones(numero):
    try:
        cursor = conexion.connection.cursor()
        sql = "DELETE FROM habitaciones WHERE numero = {0}".format(numero)
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({'mensaje': "habitacion eliminada"})
    except Exception as ex:
        return ex


# metodo para que el cliente pueda buscar por el precio menor al elegido
@app.route('/habitaciones/clientes/precio/<precio>', methods=['GET'])
def buscar_habitaciones_por_precio(precio):
    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT * FROM habitaciones WHERE precioPorDia < {0}".format(
            precio)
        cursor.execute(sql)
        datos = cursor.fetchall()
        print(datos)
        result = []

        for fila in datos:
            cuarto = {'id': fila[0], 'numero': fila[1],
                'precioPorDia': fila[2]}
            result.append(cuarto)

        return jsonify({'habitaciones': result, 'mensaje': "las habitaciones estan listadas"})
    except Exception as ex:
        return ex


# metodo para que el cliente pueda buscar por fecha
@app.route('/habitaciones/clientes/fechaunica/<fecha>', methods=['GET'])
def buscar_habitaciones_por_fecha(fecha):
    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT DISTINCT numero, inicio_resv, fin_resv FROM reservas WHERE inicio_resv = {0}".format(fecha)
        cursor.execute(sql)
        datos = cursor.fetchall()
        print(datos)
        result = []

        for fila in datos:
            cuarto = {'numero': fila[0], 'inicioreserva': fila[1], 'finalreserva': fila[2], 'estado': 'ocupada'}
            result.append(cuarto)

        cursor = conexion.connection.cursor()
        sql = "SELECT DISTINCT habitaciones.numero, habitaciones.precioPorDia FROM habitaciones LEFT JOIN reservas ON habitaciones.numero = reservas.numero WHERE reservas.numero IS NULL"
        cursor.execute(sql)
        datos2 = cursor.fetchall()
        print(datos2)
        result2 = []

        for fila2 in datos2:
            cuarto2 = {'numero': fila2[0], 'precioPorDia': fila2[1], 'estado': 'libre'}
            result2.append(cuarto2)

        return jsonify({'habitaciones ocupadas': result, 'habitaciones libres': result2, 'mensaje': "las habitaciones estan listadas"})
    except Exception as ex:
        return ex


# metodo para que el cliente pueda buscar por un rango de fecha.
# este rango de fecha consta de un inicio y un final. Se mostraran todas las habitaciones pero
# las que no esten disponibles tendrán un estado 1
@app.route('/habitaciones/clientes/rangofecha/<fechainicio>-<fechafinal>', methods=['GET'])
def buscar_habitaciones_por_rango_fecha(fechainicio, fechafinal):
    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT DISTINCT numero, inicio_resv, fin_resv FROM reservas WHERE inicio_resv BETWEEN {0} AND {1}".format(fechainicio, fechafinal)
        cursor.execute(sql)
        datos = cursor.fetchall()
        print(datos)
        result = []

        for fila in datos:
            cuarto = {'numero': fila[0], 'inicioreserva': fila[1], 'finalreserva': fila[2], 'estado': 'ocupada'}
            result.append(cuarto)

        if sql == 1:
            sql = "SELECT DISTINCT habitaciones.numero, habitaciones.precioPorDia FROM habitaciones LEFT JOIN reservas ON habitaciones.numero = reservas.numero WHERE reservas.numero IS NULL"
            cursor.execute(sql)
            datos2 = cursor.fetchall()
            print(datos2)
            result2 = []

            for fila2 in datos2:
                cuarto2 = {'numero': fila2[0], 'precioPorDia': fila2[1], 'estado': 'libre'}
                result2.append(cuarto2)
        else:
            sql = "SELECT numero, precioPorDia FROM habitaciones"
            cursor.execute(sql)
            datos2 = cursor.fetchall()
            print(datos2)
            result2 = []

            for fila2 in datos2:
                cuarto2 = {'numero': fila2[0], 'precioPorDia': fila2[1], 'estado': 'libre'}
                result2.append(cuarto2)

        return jsonify({'habitaciones ocupadas': result, 'habitaciones libres': result2, 'mensaje': "las habitaciones estan listadas"})
    except Exception as ex:
        return ex

# metodo para que el cliente pueda reservar una habitacion si esta disponible, indicando la fecha cuando la va a reservar y la cantidad de dias que la reserva
@app.route('/habitaciones/clientes/reserva', methods=['POST'])
def reservar_habitacion():
    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT * FROM habitaciones WHERE numero = {0}".format(request.json['numero'])
        query = cursor.execute(sql)
        if query != 1:
            return jsonify({'mensaje': 'La habitacion no existe'})
        else:
            if isinstance(request.json['fecha'], str) == True or request.json['fecha'] < 0:
                return jsonify({'mensaje': "La fechas en formato 'aaaa-mm-dd'(sin separadores) y no van fechas en negativo"})
            else:
                sql = "SELECT * FROM reservas WHERE numero = {0}".format(request.json['numero'])
                query = cursor.execute(sql)
                if query != 1: 
                    sql = """INSERT INTO reservas (numero, inicio_resv, fin_resv) VALUES ({0}, {1}, DATE_ADD(inicio_resv, INTERVAL {2} DAY))""".format(request.json['numero'], request.json['fecha'], request.json['cantdias'])
                    cursor.execute(sql)
                    conexion.connection.commit()
                    return jsonify({'mensaje': "la habitacion ha sido reservada"})
                else:
                    sql = "SELECT * FROM reservas WHERE inicio_resv = {0}".format(request.json['fecha'])
                    query = cursor.execute(sql)
                    if query == 1:
                        sql = """INSERT INTO reservas (numero, inicio_resv, fin_resv) VALUES ({0}, {1}, DATE_ADD(inicio_resv, INTERVAL {2} DAY))""".format(request.json['numero'], request.json['fecha'], request.json['cantdias'])
                        cursor.execute(sql)
                        conexion.connection.commit()
                        return jsonify({'mensaje': "la habitacion ha sido reservada"})       
                    else:
                        return jsonify({'mensaje': "la habitacion no esta disponible"})
                
    except Exception as ex:
        return ex

# rutas de error

def pagina_no_existe(error):
    return "<h1>la pagina no existe</h1>", 404


if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.register_error_handler(404, pagina_no_existe)
    serve(app, host='0.0.0.0', port= 8080)
