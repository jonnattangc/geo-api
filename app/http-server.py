#!/usr/bin/python

try:
    import logging
    import sys
    import os
    from flask import Flask, request, jsonify
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

app = Flask(__name__)
app.config['DEBUG'] = False 
app.config.update( DEBUG=False)

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"status": "NOK", "message": "Servicio no implementado o no encontrado"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"status": "NOK", "message": "Servicio no implementado o no encontrado"}), 405


# ==============================================================================
# Procesa solicitudes desde pagina web
# ==============================================================================
@app.route('/geo/<path:subpath>', methods=('GET', 'POST'))
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
