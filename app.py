# app.py
# Punto de entrada de la aplicación Flask.
# Crea la app, registra el Blueprint y la ejecuta en el puerto 5000.
# En Render se lee el puerto de la variable de entorno PORT y se escucha en 0.0.0.0.

import os

from flask import Flask
from controllers.polizas_controller import bp

app = Flask(
    __name__,
    template_folder="views",
    static_folder="public/static",
    static_url_path="/static",
)

app.register_blueprint(bp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
