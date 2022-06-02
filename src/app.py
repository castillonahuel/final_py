from flask import Flask, jsonify, request
from config import config
from flask_mysqldb import MySQL



#instancia de flask/sirve para saber si este archivo que se esta ejecutando es el principal
app = Flask(__name__)

#conexion con el parametro de esta aplicacion
conexion = MySQL(app)
@app.route('/habitaciones', methods=['GET'])
def mostrar_habitaciones(): #metdo que lista las habitaciones creadas en la BDD
   try:
       
       cursor=conexion.connection.cursor()
       sql="SELECT id, numero, precio FROM habitaciones"
       cursor.execute(sql)
       datos=cursor.fetchall()
       print(datos)
       cuartos=[] #creo una lista vacia para poder guardar las habitaciones que vienen de datos
       
       for fila in datos:    #se crea para poder recorrer las habitaciones que vienen en forma de tupla en la variable datos
           cuarto = {'id': fila[0], 'numero': fila[1], 'precio': fila[2]} #en este diccionario se almacenan los datos para despues convertirlos a json
           cuartos.append(cuarto)
           #retorna un diccionario con la key habitaciones, los valores de cuartos y una mensaje
       return jsonify({'habitaciones': cuartos, 'mensaje':"las habitaciones estan listadas"})
 
   except Exception as ex:
       return ex

#dentro de numero va venir el numero de la habitacion que se quiere buscar
@app.route('/habitaciones/<numero>', methods=['GET']) 
def buscar_habitaciones(numero):
    try:
       cursor=conexion.connection.cursor()
       #se busca la habitacion solicitada con numero, valor que que se le pasa a la url
       sql="SELECT id, numero, precio FROM habitaciones WHERE numero = '{0}'".format(numero)
       cursor.execute(sql)
       datos=cursor.fetchone()
       
       #si datos no esta vacio, busca y retorna la habitacion con el numero que se le paso por url
       if datos != None:
          cuarto = {'id': datos[0], 'numero': datos[1], 'precio': datos[2]}
          return jsonify({'habitaciones': cuarto, 'mensaje':"la habitacion ha sido encontrada"})       
       else:
           return jsonify({'mensaje': "error habitacion no encontrada"})   

    except Exception as ex:
       return ex 


#metodo para que el empleado pueda registrar habitaciones
@app.route('/registrar', methods=['POST'])
def registrar_habitaciones():
    try:
        #print(request.json)
        cursor=conexion.connection.cursor()
        sql="""INSERT INTO habitaciones (id, numero, precio) VALUES ('{0}','{1}','{2}')""".format(request.json['id'],
        request.json['numero'], request.json['precio'])
        cursor.execute(sql)
        conexion.connection.commit() #confirma la insercion de los datos
                
        return jsonify({'mensaje':"habitacion registrada con exito"})
    except Exception as ex:
       return ex 

#metodo para que el empleado pueda actualizar info de las habitaciones
@app.route('/habitaciones/<numero>', methods=['PUT'])
def actualizar_habitaciones(numero):
    try:
       cursor=conexion.connection.cursor()
       sql="""UPDATE habitaciones SET id = '{0}', numero = '{1}', precio = '{2}' WHERE numero = '{3}'""".format(request.json['id'],
       request.json['numero'], request.json['precio'],numero)
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



#rutas de error
def pagina_no_existe(error):
    return "<h1>la pagina no existe</h1>", 404

if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.register_error_handler(404, pagina_no_existe)
    app.run()
