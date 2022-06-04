from re import template
from colorama import Cursor
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

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return 'Ya esta logueado.'


@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] and request.form['password'] == 'habitacionescli':
        session['logged_in'] = True
        token = jwt.encode({
            'usuario': request.form['username'],
            'tipo usuario': 'Cliente',
            'expiration': str(datetime.utcnow() + timedelta(seconds=120))
        },
            app.config['SECRET_KEY'])
        llave = token
        return render_template('clientes.html', llave =  llave)

    if request.form['username'] and request.form['password'] == 'habitacionesemp':
        session['logged_in'] = True
        token = jwt.encode({
            'usuario': request.form['username'],
            'tipo usuario': 'Empleado',
            'expiration': str(datetime.utcnow() + timedelta(seconds=120))
        },
            app.config['SECRET_KEY'])
        llave = token 
        return render_template('empleados.html', llave = llave) 

    else:
        return make_response('No se puede verificar', 403)

@app.route('/logout', methods=['POST'])
def logout():
    session['logged_in'] = False
    return render_template('login.html')



# conexion con el parametro de esta aplicacion
conexion = MySQL(app)
@app.route('/habitaciones', methods=['GET'])
def mostrar_habitaciones(): #metdo que lista las habitaciones creadas en la BDD
   try:
       
       cursor=conexion.connection.cursor()
       sql="SELECT id, numero, precioPorDia, fecha, estado FROM habitaciones"
       cursor.execute(sql)
       datos=cursor.fetchall()
       print(datos)
       cuartos=[] #creo una lista vacia para poder guardar las habitaciones que vienen de datos
       
       for fila in datos:    #se crea para poder recorrer las habitaciones que vienen en forma de tupla en la variable datos
           cuarto = {'id': fila[0], 'numero': fila[1], 'precioPorDia': fila[2],
           'fecha': fila[3], 'estado': fila[4]} #en este diccionario se almacenan los datos para despues convertirlos a json
           cuartos.append(cuarto)
           #retorna un diccionario con la key habitaciones, los valores de cuartos y una mensaje
       return jsonify({'habitaciones': cuartos, 'mensaje':"las habitaciones estan listadas"})
 
   except Exception as ex:
       return ex

def buscar_cuartobd(numero):
    try:
       cursor=conexion.connection.cursor()
       #se busca la habitacion solicitada con numero, valor que que se le pasa a la url
       sql="SELECT id, numero, precioPorDia, fecha, estado FROM habitaciones WHERE numero = '{0}'".format(numero)
       cursor.execute(sql)
       datos=cursor.fetchone()
       if datos != None:
          cuarto = {'id': datos[0], 'numero': datos[1], 'precioPorDia': datos[2],
          'fecha': datos[3], 'estado': datos[4]}
          return cuarto
       else:
           return None
    except Exception as ex:
        raise ex


#dentro de numero va venir el numero de la habitacion que se quiere buscar
@app.route('/habitaciones/<numero>', methods=['GET']) 
def buscar_habitaciones(numero):
    try:
       cuarto = buscar_cuartobd(numero)
       if cuarto != None:
          return jsonify({'habitaciones': cuarto, 'mensaje':"la habitacion ha sido encontrada", 'exito': True})        
       else:
           return jsonify({'mensaje': "error habitacion no encontrada", 'exito': False})   

       
    except Exception as ex:
        return jsonify({'mensaje': "Error", 'exito': False})    

       

# metodo para que el empleado pueda registrar habitaciones
@app.route('/registrar', methods=['POST'])
def registrar_habitaciones():
    try:
        cursor = conexion.connection.cursor()
        numsql = "SELECT numero FROM habitaciones"        
        cursor.execute(numsql)
        datos = cursor.fetchall()
        nums = []
        for fila in datos:
           #y = {'numero': fila[0]}
           num = [fila]
           nums.append(num)                              
        #return jsonify(num)                      
        sql="""INSERT INTO habitaciones (numero, precioPorDia, fecha, estado) VALUES ('{0}','{1}','{2}','{3}')""".format(request.json['numero'],
        request.json['precioPorDia'], request.json['fecha'], request.json['estado'])   
        numjson = request.json['numero']
        if numjson in nums :
            return jsonify({'mensaje': "ERROR habitacion registrada ya existe"})
        else:
            cursor.execute(sql)
            conexion.connection.commit()
            return jsonify({'mensaje': "habitacion registrada con exito"})
        

    except Exception as ex:
            return jsonify({'mensaje': "Error", 'exito': False})
 
    
   
#metodo para que el empleado pueda actualizar info de las habitaciones
@app.route('/habitaciones/<numero>', methods=['PUT'])
def actualizar_habitaciones(numero):
    try:

       cursor=conexion.connection.cursor()
       sql="""UPDATE habitaciones SET precioPorDia = '{0}', fecha = '{1}',
       estado = '{2}'  WHERE numero = '{3}'""".format(request.json['precioPorDia'], request.json['fecha'],
       request.json['estado'], numero)
       cursor.execute(sql)
       conexion.connection.commit()
       return jsonify({'mensaje':"habitacion actualizada"})

    except Exception as ex:
        return ex



#metodo para que el empleado pueda eliminar habitaciones
@app.route('/habitaciones/<numero>', methods=['DELETE'])
def eliminar_habitaciones(numero):
    try:
       cursor=conexion.connection.cursor()
       sql="DELETE FROM habitaciones WHERE numero = '{0}'".format(numero)
       cursor.execute(sql)
       conexion.connection.commit()
       return jsonify({'mensaje':"habitacion eliminada"})
    except Exception as ex:
        return ex


# rutas de error
def pagina_no_existe(error):
    return "<h1>la pagina no existe</h1>", 404


if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.register_error_handler(404, pagina_no_existe)
    app.run()
