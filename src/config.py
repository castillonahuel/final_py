class configDesarrollo():
    #modo debug del servidor
    DEBUG = True
    #datos de la conexion a la bdd
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'hoteles'

config = {
    'development' : configDesarrollo
}