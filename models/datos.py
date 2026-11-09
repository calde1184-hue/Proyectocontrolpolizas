# models/datos.py
# Capa: modelo (acceso a datos) - único lugar que abre archivos externos.
# Solo lectura. No borra ni modifica nada dentro de la bodega de datos.

import os
from datetime import datetime

import pdfplumber
import pandas as pd

# Ruta base de la bodega de datos (solo lectura).
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "Insumos_Control_Polizas")
EXCEL_PATH = os.path.join(DATA_DIR, "Maestro_Clientes.xlsx")
POLIZAS_DIR = os.path.join(DATA_DIR, "polizas")

# Diccionario que mapea la etiqueta del PDF al nombre del campo interno.
CAMPOS = {
    "Numero de poliza": "numero",
    "Ramo": "ramo",
    "Tomador / Asegurado": "nombre",
    "Cedula": "cedula",
    "Vigencia desde": "desde",
    "Vigencia hasta": "hasta",
    "Prima anual": "prima",
    "Forma de pago": "pago",
    "Suma asegurada": "suma",
    "Asesor": "asesor",
}


def _texto_a_fecha(valor):
    """Convierte un texto dd/mm/aaaa a objeto date.
    Devuelve None si está vacío o no se puede convertir."""
    if valor is None:
        return None
    valor = str(valor).strip()
    if valor == "":
        return None
    try:
        return datetime.strptime(valor, "%d/%m/%Y").date()
    except ValueError:
        return None


def _texto_a_numero(valor):
    """Convierte un monto como 'CRC 228,000.00' a número float.
    Devuelve None si está vacío o no se puede convertir."""
    if valor is None:
        return None
    valor = str(valor).strip()
    if valor == "":
        return None
    # Quitar posible moneda y espacios, y quitar comas de miles
    valor = valor.replace("CRC", "").replace("crc", "").strip()
    valor = valor.replace(",", "")
    try:
        return float(valor)
    except ValueError:
        return None


def cargar_clientes():
    """
    Lee Maestro_Clientes.xlsx (hoja Clientes) con pandas.
    Devuelve un DataFrame con Cedula como texto sin espacios.
    """
    df = pd.read_excel(EXCEL_PATH, sheet_name="Clientes", dtype={"Cedula": str})
    if "Cedula" in df.columns:
        df["Cedula"] = df["Cedula"].astype(str).str.strip()
    return df


def leer_poliza(ruta_pdf):
    """
    Abre un PDF de póliza con pdfplumber, toma el texto de la primera página,
    guarda la primera línea como 'aseguradora' y recorre las demás líneas con
    un bucle extrayendo los campos definidos en CAMPOS.
    Devuelve un diccionario con:
    archivo, aseguradora, numero, ramo, nombre, cedula, desde, hasta,
    prima, pago, suma, asesor.
    """
    archivo = os.path.basename(ruta_pdf)
    datos = {
        "archivo": archivo,
        "aseguradora": None,
        "numero": None,
        "ramo": None,
        "nombre": None,
        "cedula": None,
        "desde": None,
        "hasta": None,
        "prima": None,
        "pago": None,
        "suma": None,
        "asesor": None,
    }

    with pdfplumber.open(ruta_pdf) as pdf:
        pagina = pdf.pages[0]
        texto = pagina.extract_text() or ""
        lineas = texto.split("\n")

    if not lineas:
        return datos

    # Primera línea: nombre de la aseguradora.
    datos["aseguradora"] = lineas[0].strip()

    # Recorrer el resto de las líneas con un bucle.
    for linea in lineas[1:]:
        if ":" not in linea:
            continue
        etiqueta, valor = linea.split(":", 1)
        etiqueta = etiqueta.strip()
        valor = valor.strip()
        if etiqueta in CAMPOS:
            campo = CAMPOS[etiqueta]
            if campo in ("desde", "hasta"):
                datos[campo] = _texto_a_fecha(valor)
            elif campo in ("prima", "suma"):
                datos[campo] = _texto_a_numero(valor)
            else:
                datos[campo] = valor

    return datos


def cargar_polizas():
    """
    Recorre la carpeta de pólizas en orden alfabético y devuelve una lista
    con el diccionario de cada PDF leído por leer_poliza().
    """
    polizas = []
    nombres = sorted(os.listdir(POLIZAS_DIR))
    for nombre in nombres:
        if nombre.lower().endswith(".pdf"):
            ruta = os.path.join(POLIZAS_DIR, nombre)
            polizas.append(leer_poliza(ruta))
    return polizas
