#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import time
    import requests
    import json
    from flask_cors import CORS
    from flask_wtf.csrf import CSRFProtect
    from flask_httpauth import HTTPBasicAuth
    from flask_login import UserMixin, current_user, login_required, login_user
    from flask import Flask, render_template, abort, make_response, request, redirect, jsonify, send_from_directory
    from utilgeo import UtilGeo

except ImportError:

    logging.error(ImportError)
    print((os.linesep * 2).join(['[http-server] Error al buscar los modulos:',
                                 str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

############################# Configuraci'on de Registro de Log  ################################
FORMAT = '%(asctime)s %(levelname)s : %(message)s'
root = logging.getLogger()
root.setLevel(logging.INFO)
formatter = logging.Formatter(FORMAT)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
root.addHandler(handler)
logger = logging.getLogger('HTTP')
# ===============================================================================
# Configuraciones generales del servidor Web
# ===============================================================================

SECRET_CSRF = os.environ.get('SECRET_KEY_CSRF','KEY-CSRF-ACA-DEBE-IR')
app = Flask(__name__)
app.config['DEBUG'] = False 
app.config.update( DEBUG=False, SECRET_KEY = str(SECRET_CSRF), )

csrf = CSRFProtect()
csrf.init_app(app)

auth = HTTPBasicAuth()
cors = CORS(app, resources={r"/geo/*": {"origins": ["dev.jonnattan.com"]}})
# ===============================================================================
# variables globales
# ===============================================================================
ROOT_DIR = os.path.dirname(__file__)

#===============================================================================
# Servicios basicos
#===============================================================================
@app.route('/', methods=['GET', 'POST'])
@csrf.exempt
def index():
    logging.info("Reciv solicitude endpoint: /" )
    return redirect('/info'), 302

@app.route('/<path:subpath>', methods=('GET', 'POST'))
@csrf.exempt
def processOtherContext( subpath ):
    logging.info("Reciv solicitude endpoint: " + subpath )
    return redirect('/info'), 302

@app.route('/info', methods=['GET', 'POST'])
@csrf.exempt
def infoJonnaProccess():
    logging.info("Reciv solicitude endpoint: /infojonna" )
    return jsonify({
        "Name": "Geo API",
        "Description": "API de servicios para trabajos con"
    })
#===============================================================================
# Metodo solicitado por la biblioteca de autenticaci'on b'asica
#===============================================================================
@auth.verify_password
def verify_password(username, password):
    user = None
    if username != None :
        pswd = os.environ.get('PASS_USER_REQUEST','NO_INFO')
        if str(password) == str(pswd) : 
            user = username
    return user

#===============================================================================
# Implementacion del handler que respondera el error en caso de mala autenticacion
#===============================================================================
@auth.error_handler
def unauthorized():
    return make_response(jsonify({'message':'invalid credentials'}), 401)

# ==============================================================================
# Procesa solicitudes desde pagina web
# ==============================================================================
@app.route('/geo/<path:subpath>', methods=('GET', 'POST'))
@csrf.exempt
@auth.login_required
def process_page( subpath ):
    geo = UtilGeo()
    data_response, http_status = geo.request_process( request, str(subpath) )
    del geo
    return jsonify(data_response), http_status

# ===============================================================================
# Metodo Principal que levanta el servidor
# ===============================================================================
if __name__ == "__main__":
    listenPort = 8085
    logger.info("ROOT_DIR: " + ROOT_DIR)
    if(len(sys.argv) == 1):
        logger.error("Se requiere el puerto como parametro")
        exit(0)
    try:
        logger.info("Server listen at: " + sys.argv[1])
        listenPort = int(sys.argv[1])
        app.run( host='0.0.0.0', port=listenPort)
    except Exception as e:
        print("ERROR MAIN:", e)

    logging.info("PROGRAM FINISH")
