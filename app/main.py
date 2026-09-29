#!/usr/bin/env python3
import logging
import os
import sys

try:
    from flask import Flask, jsonify
    from controllers.geo_controller import geo_bp
except ImportError:
    logging.exception("[geo-api] Error al importar modulos requeridos")
    print(
        (sys.linesep * 2).join([
            '[http-server] Error al buscar los modulos:',
            str(sys.exc_info()[1]),
            'Debes instalarlos para continuar',
            'Deteniendo...'
        ])
    )
    sys.exit(-2)

# =============================================================================
# Configuracion de logging
# =============================================================================
FORMAT = '%(asctime)s %(levelname)s : %(message)s'
root = logging.getLogger()
root.setLevel(logging.INFO)
formatter = logging.Formatter(FORMAT)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
if not root.handlers:
    root.addHandler(handler)
logger = logging.getLogger('HTTP')

# =============================================================================
# Aplicacion Flask
# =============================================================================
app = Flask(__name__)
app.config['DEBUG'] = False


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check para Kubernetes / Docker / load balancers."""
    return jsonify({"status": "OK", "service": "geo-api"}), 200


@app.errorhandler(404)
def page_not_found(_e):
    return jsonify({"status": "NOK", "message": "Servicio no implementado o no encontrado"}), 404


@app.errorhandler(405)
def method_not_allowed(_e):
    return jsonify({"status": "NOK", "message": "Metodo no permitido"}), 405


@app.errorhandler(500)
def internal_error(_e):
    return jsonify({"status": "NOK", "message": "Error interno del servidor"}), 500


app.register_blueprint(geo_bp, url_prefix='/geo')

# =============================================================================
# Punto de entrada para desarrollo local (no usado por Gunicorn)
# =============================================================================
if __name__ == "__main__":
    port = os.environ.get('PORT', '8075')
    if len(sys.argv) > 1:
        port = sys.argv[1]
    try:
        listen_port = int(port)
        logger.info(f"Server listen at: {listen_port}")
        app.run(host='0.0.0.0', port=listen_port)
    except Exception as e:
        logger.error(f"ERROR MAIN: {e}")
        sys.exit(1)

    logger.info("PROGRAM FINISH")
