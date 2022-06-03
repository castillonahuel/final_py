from re import template
from flask import Flask, jsonify, request, make_response, render_template, session
from config import config
from flask_mysqldb import MySQL
import jwt
from datetime import datetime, timedelta
from functools import wraps


# instancia de flask/sirve para saber si este archivo que se esta ejecutando es el principal
app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = '0b7807f50046438aa179c6987907704e'

# login


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


@app.route('/public')
def public():
    return 'Para el publico'


@app.route('/auth')
@token_required
def auth():
    return 'El JWT fue verificado. Bienvenido al sistema'


@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return 'Ya esta logueado.'


@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] and request.form['password'] == '1234':
        session['logged_in'] = True
        token = jwt.encode({
            'user': request.form['username'],
            'expiration': str(datetime.utcnow() + timedelta(seconds=120))
        },
            app.config['SECRET_KEY'])
        return jsonify({'token': token})
    else:
        return make_response('No se puede verificar', 403)


# conexion con el parametro de esta aplicacion
conexion = MySQL(app)
@app.route('/habitaciones', methods=['GET'])
def mostrar_habitaciones(): #metdo que lista las habitaciones creadas en la BDD
   try:
       
       cursor=conexion.connection.cursor()
       sql="SELECT id, codigo, numero, precioPorDia, fecha, estado FROM habitaciones"
       cursor.execute(sql)
       datos=cursor.fetchall()
       print(datos)
       cuartos=[] #creo una lista vacia para poder guardar las habitaciones que vienen de datos
       
       for fila in datos:    #se crea para poder recorrer las habitaciones que vienen en forma de tupla en la variable datos
           cuarto = {'id': fila[0], 'codigo': fila[1], 'numero': fila[2], 'precioPorDia': fila[3],
           'fecha': fila[4], 'estado': fila[5]} #en este diccionario se almacenan los datos para despues convertirlos a json
           cuartos.append(cuarto)
           #retorna un diccionario con la key habitaciones, los valores de cuartos y una mensaje
       return jsonify({'habitaciones': cuartos, 'mensaje':"las habitaciones estan listadas"})
 
   except Exception as ex:
       return ex

#dentro de numero va venir el numero de la habitacion que se quiere buscar
@app.route('/habitaciones/<codigo>', methods=['GET']) 
def buscar_habitaciones(codigo):
    try:
       cursor=conexion.connection.cursor()
       #se busca la habitacion solicitada con numero, valor que que se le pasa a la url
       sql="SELECT id, codigo, numero, precioPorDia, fecha, estado FROM habitaciones WHERE codigo = '{0}'".format(codigo)
       cursor.execute(sql)
       datos=cursor.fetchone()
       
       #si datos no esta vacio, busca y retorna la habitacion con el numero que se le paso por url
       if datos != None:
          cuarto = {'id': datos[0], 'codigo': datos[1], 'numero': datos[2], 'precioPorDia': datos[3],
          'fecha': datos[4], 'estado': datos[5]}
          return jsonify({'habitaciones': cuarto, 'mensaje':"la habitacion ha sido encontrada"})       
       else:
           return jsonify({'mensaje': "error habitacion no encontrada"})   

    except Exception as ex:
        return ex

# dentro de numero va venir el numero de la habitacion que se quiere buscar


@app.route('/habitaciones/<numero>', methods=['GET'])
def buscar_habitaciones(numero):
    try:
        cursor = conexion.connection.cursor()
        # se busca la habitacion solicitada con numero, valor que que se le pasa a la url
        sql = "SELECT id, numero, precio FROM habitaciones WHERE numero = '{0}'".format(
            numero)
        cursor.execute(sql)
        datos = cursor.fetchone()

        # si datos no esta vacio, busca y retorna la habitacion con el numero que se le paso por url
        if datos != None:
            cuarto = {'id': datos[0], 'numero': datos[1], 'precio': datos[2]}
            return jsonify({'habitaciones': cuarto, 'mensaje': "la habitacion ha sido encontrada"})
        else:
            return jsonify({'mensaje': "error habitacion no encontrada"})

    except Exception as ex:
        return ex


# metodo para que el empleado pueda registrar habitaciones
@app.route('/registrar', methods=['POST'])
def registrar_habitaciones():
    try:
        #print(request.json)
        cursor=conexion.connection.cursor()
        sql="""INSERT INTO habitaciones (id, codigo, numero, precioPorDia, fecha, estado) VALUES ('{0}','{1}','{2}','{3}','{4}','{5}')""".format(request.json['id'],
        request.json['codigo'], request.json['numero'], request.json['precioPorDia'],
        request.json['fecha'], request.json['estado'])
        cursor.execute(sql)
        conexion.connection.commit()  # confirma la insercion de los datos

        return jsonify({'mensaje': "habitacion registrada con exito"})
    except Exception as ex:
        return ex

# metodo para que el empleado pueda actualizar info de las habitaciones



#metodo para que el empleado pueda actualizar info de las habitaciones
@app.route('/habitaciones/<codigo>', methods=['PUT'])
def actualizar_habitaciones(codigo):
    try:

       cursor=conexion.connection.cursor()
       sql="""UPDATE habitaciones SET precioPorDia = '{0}', fecha = '{1}',
       estado = '{2}'  WHERE codigo = '{3}'""".format(request.json['precioPorDia'], request.json['fecha'],
       request.json['estado'], codigo)
       cursor.execute(sql)
       conexion.connection.commit()
       return jsonify({'mensaje':"habitacion actualizada"})

    except Exception as ex:
        return ex



#metodo para que el empleado pueda eliminar habitaciones
@app.route('/habitaciones/<codigo>', methods=['DELETE'])
def eliminar_habitaciones(codigo):
    try:
       cursor=conexion.connection.cursor()
       sql="DELETE FROM habitaciones WHERE codigo = '{0}'".format(codigo)
       cursor.execute(sql)
       conexion.connection.commit()
       return jsonify({'mensaje':"habitacion eliminada"})
    except Exception as ex:
        return ex


# metodo para que el empleado pueda eliminar habitaciones
@app.route('/habitaciones/<numero>', methods=['DELETE'])
def eliminar_habitaciones(numero):
    try:
        cursor = conexion.connection.cursor()
        sql = "DELETE FROM habitaciones WHERE numero = '{0}'".format(numero)
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({'mensaje': "habitacion eliminada"})

    except Exception as ex:
        return ex


# rutas de error
def pagina_no_existe(error):
    return "<h1>la pagina no existe</h1>", 404


if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.register_error_handler(404, pagina_no_existe)
    app.run()
