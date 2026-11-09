# controllers/polizas_controller.py
# Capa: controlador (rutas Flask con Blueprint).
# No calcula nada: solo llama a models/ y services/ y devuelve respuestas HTTP.

import io
import zipfile

from flask import Blueprint, render_template, send_file, abort, request

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
