# controllers/polizas_controller.py
# Capa: controlador (rutas Flask con Blueprint).
# No calcula nada: solo llama a models/ y services/ y devuelve respuestas HTTP.

import io
import os
import zipfile
from werkzeug.utils import secure_filename

from flask import (
    Blueprint,
    render_template,
    send_file,
    abort,
    request,
    flash,
    redirect,
    url_for,
)

from models.datos import establecer_excel_importado
from models.polizas import (
    FECHA_CORTE,
    calcular_resultados,
    contar_por_estado,
    primas_por_aseguradora,
    buscar_inconsistencias,
    buscar_por_numero,
)
from services.generador_aviso import crear_aviso_pdf

bp = Blueprint("polizas", __name__)

# Carpeta donde se guardan los Excel importados por el usuario (fuera de data/).
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


@bp.route("/")
def inicio():
    """Tablero principal: contadores, primas, inconsistencias y tabla de pólizas."""
    resultados = calcular_resultados()
    conteo = contar_por_estado(resultados)
    primas = primas_por_aseguradora(resultados)
    inconsistencias = buscar_inconsistencias(resultados)
    return render_template(
        "inicio.html",
        resultados=resultados,
        conteo=conteo,
        primas=primas,
        inconsistencias=inconsistencias,
        fecha_corte=FECHA_CORTE,
    )


@bp.route("/importar-excel", methods=["POST"])
def importar_excel():
    """
    Recibe un archivo .xlsx subido por el usuario, lo guarda en uploads/
    y lo establece como el Excel maestro activo para cruzar con las pólizas.
    No toca nada dentro de data/.
    """
    if "archivo" not in request.files:
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("polizas.inicio"))

    archivo = request.files["archivo"]
    if archivo.filename == "":
        flash("Nombre de archivo vacío.", "error")
        return redirect(url_for("polizas.inicio"))

    if not archivo.filename.lower().endswith(".xlsx"):
        flash("Solo se aceptan archivos .xlsx.", "error")
        return redirect(url_for("polizas.inicio"))

    nombre_seguro = secure_filename(archivo.filename)
    ruta_guardado = os.path.join(UPLOADS_DIR, nombre_seguro)
    archivo.save(ruta_guardado)

    establecer_excel_importado(ruta_guardado)
    flash(f"Excel importado correctamente: {nombre_seguro}", "exito")
    return redirect(url_for("polizas.inicio"))


@bp.route("/procesar", methods=["POST"])
def procesar():
    """
    Vuelve a leer el Excel maestro y los PDF de pólizas, recalcula estados,
    días para vencer, primas e inconsistencias, y refresca el tablero.
    """
    # Forzar recarga de datos desde el Excel activo (importado o original de data/).
    calcular_resultados()
    flash("Proceso completado: se recalcularon estados, primas e inconsistencias.", "exito")
    return redirect(url_for("polizas.inicio"))


@bp.route("/aviso/")
@bp.route("/aviso/<numero>")
def aviso(numero=None):
    """
    Devuelve el PDF de aviso de renovación de una póliza.
    404 si la póliza no existe o está Vigente.
    """
    if numero is None:
        numero = request.args.get("numero")
    if not numero:
        abort(404)

    poliza = buscar_por_numero(numero)
    if poliza is None:
        abort(404)

    resultados = calcular_resultados()
    r = next((x for x in resultados if x["numero"] == numero), None)
    if r is None:
        abort(404)

    if r["estado"] == "Vigente":
        abort(404)

    pdf_bytes = crear_aviso_pdf(r)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        download_name=f"aviso_{numero}.pdf",
    )


@bp.route("/descargar-avisos")
def descargar_avisos():
    """
    Arma en memoria un .zip con los avisos de todas las pólizas Por vencer y Vencidas.
    """
    resultados = calcular_resultados()

    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for r in resultados:
            if r["estado"] in ("Por vencer", "Vencida"):
                pdf_bytes = crear_aviso_pdf(r)
                zf.writestr(f"aviso_{r['numero']}.pdf", pdf_bytes)

    memoria.seek(0)
    return send_file(
        memoria,
        mimetype="application/zip",
        download_name="avisos.zip",
        as_attachment=True,
    )
