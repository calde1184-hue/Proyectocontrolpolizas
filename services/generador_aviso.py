# services/generador_aviso.py
# Capa: servicios. Crea el aviso de renovación en PDF (A4 vertical) con fpdf2
# y lo devuelve en bytes. No guarda nada en disco por sí mismo.

from datetime import date

from fpdf import FPDF

# Colores del diseño (según AGENTS.md).
ROJO_BANDA = (174, 24, 0)      # #AE1800
GRIS_PIE = (243, 242, 242)     # #F3F2F2
GRIS_TEXTO_PIE = (80, 80, 80)

ANCHO_PAGINA = 210  # mm (A4)
ALTO_PAGINA = 297   # mm (A4)
MARGEN = 10


def _latin1(texto):
    """Convierte texto a latin-1 para que tildes y eñes no fallen con Helvetica."""
    if texto is None:
        return ""
    return str(texto).encode("latin-1", "replace").decode("latin-1")


def _fecha_es(fecha):
    """Formatea una fecha date a dd/mm/aaaa o devuelve '-' si es None."""
    if fecha is None:
        return "-"
    return fecha.strftime("%d/%m/%Y")


def _prima_es(prima):
    """Formatea la prima anual como 'CRC 228,000.00' o 'No registrada'."""
    if prima is None:
        return "No registrada"
    return f"CRC {prima:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def crear_aviso_pdf(poliza):
    """
    Crea un aviso de renovación de póliza en PDF (A4 vertical) y lo devuelve en bytes.

    El diccionario `poliza` debe contener al menos:
    nombre, estado, hasta, dias_hasta_vencer, numero, aseguradora, ramo,
    cedula, desde, prima, pago.
    """
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # ---------- Banda superior roja ----------
    pdf.set_fill_color(*ROJO_BANDA)
    pdf.rect(0, 0, ANCHO_PAGINA, 30, "F")

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_xy(MARGEN, 8)
    pdf.cell(0, 7, _latin1("Corredora de Seguros Horizonte"), ln=True, align="C")

    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 7, _latin1("Aviso de renovación de póliza"), ln=True, align="C")

    # ---------- Cuerpo ----------
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(45)

    # Saludo
    pdf.set_font("Helvetica", "", 12)
    nombre = poliza.get("nombre", "cliente")
    pdf.cell(0, 7, _latin1(f"Estimado(a) {nombre}:"), ln=True)
    pdf.ln(5)

    # Párrafo según estado
    pdf.set_font("Helvetica", "", 11)
    estado = poliza.get("estado", "Vigente")
    hasta = poliza.get("hasta")
    dias = poliza.get("dias_hasta_vencer")

    if estado == "Vencida":
        pdf.multi_cell(
            0,
            6,
            _latin1(f"Su póliza venció el {_fecha_es(hasta)}. Comuníquese con su asesor para renovar."),
        )
    elif estado == "Por vencer":
        pdf.multi_cell(
            0,
            6,
            _latin1(
                f"Su póliza vence el {_fecha_es(hasta)} en {dias} días. "
                f"Su asesor se comunicará con usted."
            ),
        )
    else:
        pdf.multi_cell(
            0,
            6,
            _latin1("Su póliza se encuentra vigente."),
        )

    pdf.ln(10)

    # ---------- Tabla ----------
    pdf.set_font("Helvetica", "B", 10)
    ancho_util = ANCHO_PAGINA - 2 * MARGEN
    col_campo = 50
    col_valor = ancho_util - col_campo

    filas = [
        ("Número de póliza", poliza.get("numero", "-")),
        ("Aseguradora", poliza.get("aseguradora", "-")),
        ("Ramo", poliza.get("ramo", "-")),
        ("Cédula", poliza.get("cedula", "-")),
        (
            "Vigencia",
            f"{_fecha_es(poliza.get('desde'))} al {_fecha_es(poliza.get('hasta'))}",
        ),
        ("Prima anual", _prima_es(poliza.get("prima"))),
        ("Forma de pago", poliza.get("pago", "-")),
    ]

    # Encabezado de tabla
    pdf.set_fill_color(230, 230, 230)
    pdf.set_x(MARGEN)
    pdf.cell(col_campo, 8, _latin1("Campo"), border=1, fill=True)
    pdf.cell(col_valor, 8, _latin1("Valor"), border=1, fill=True, ln=True)

    # Filas de datos
    pdf.set_font("Helvetica", "", 10)
    for campo, valor in filas:
        pdf.set_x(MARGEN)
        pdf.cell(col_campo, 8, _latin1(campo), border=1)
        pdf.cell(col_valor, 8, _latin1(valor), border=1, ln=True)

    pdf.ln(12)

    # ---------- Pie de página gris ----------
    pie_y = ALTO_PAGINA - 20
    pdf.set_fill_color(*GRIS_PIE)
    pdf.rect(0, pie_y, ANCHO_PAGINA, 20, "F")
    pdf.set_text_color(*GRIS_TEXTO_PIE)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_xy(MARGEN, pie_y + 5)
    pdf.cell(
        0,
        5,
        _latin1("Documento ficticio - uso académico. No tiene validez legal."),
        ln=True,
        align="C",
    )

    # ---------- Devolver bytes ----------
    salida = pdf.output(dest="S")
    if isinstance(salida, (bytes, bytearray)):
        return bytes(salida)
    return salida.encode("latin-1")
