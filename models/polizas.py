# models/polizas.py
# Capa: modelo (reglas del negocio). No abre archivos; recibe los datos de models/datos.py.

from datetime import date

from models.datos import cargar_clientes, cargar_polizas

FECHA_CORTE = date(2026, 11, 9)
DIAS_AVISO = 30


def estado_poliza(hasta, fecha_corte=FECHA_CORTE):
    """
    Devuelve el estado de una póliza según la fecha de vigencia 'hasta'.
    Usa condicionales if / elif / else.
    """
    if hasta is None:
        return "Sin fecha"
    if hasta < fecha_corte:
        return "Vencida"
    elif 0 <= (hasta - fecha_corte).days <= DIAS_AVISO:
        return "Por vencer"
    else:
        return "Vigente"


def calcular_resultados(fecha_corte=FECHA_CORTE):
    """
    Cruza cada póliza con el maestro por cédula (correo y en_maestro),
    calcula los días hasta vencer y el estado, y devuelve una lista de
    diccionarios ordenada de menos a más días (lo urgente primero).
    """
    clientes_df = cargar_clientes()
    polizas = cargar_polizas()

    # Diccionario de clientes indexado por cédula para cruce rápido.
    clientes_por_cedula = {}
    for _, fila in clientes_df.iterrows():
        cedula = str(fila["Cedula"]).strip()
        clientes_por_cedula[cedula] = {
            "correo": fila.get("Correo", None),
            "en_maestro": True,
        }

    resultados = []
    for poliza in polizas:
        cedula = poliza["cedula"]
        if cedula is not None:
            cedula = str(cedula).strip()
        info_cliente = clientes_por_cedula.get(cedula, {})
        en_maestro = cedula in clientes_por_cedula
        correo = info_cliente.get("correo", None) if en_maestro else None

        hasta = poliza["hasta"]
        if hasta is None:
            dias_hasta_vencer = None
            estado = "Sin fecha"
        else:
            dias_hasta_vencer = (hasta - fecha_corte).days
            estado = estado_poliza(hasta, fecha_corte)

        resultado = {
            "archivo": poliza["archivo"],
            "aseguradora": poliza["aseguradora"],
            "numero": poliza["numero"],
            "ramo": poliza["ramo"],
            "nombre": poliza["nombre"],
            "cedula": cedula,
            "correo": correo,
            "en_maestro": en_maestro,
            "desde": poliza["desde"],
            "hasta": poliza["hasta"],
            "prima": poliza["prima"],
            "pago": poliza["pago"],
            "suma": poliza["suma"],
            "asesor": poliza["asesor"],
            "dias_hasta_vencer": dias_hasta_vencer,
            "estado": estado,
        }
        resultados.append(resultado)

    # Ordenar de menos a más días (lo urgente primero). Las fechas None van al final.
    resultados.sort(
        key=lambda r: (
            r["dias_hasta_vencer"] is None,
            r["dias_hasta_vencer"] if r["dias_hasta_vencer"] is not None else float("inf"),
        )
    )

    return resultados


def contar_por_estado(resultados):
    """Devuelve un diccionario con la cantidad de pólizas por estado."""
    conteo = {}
    for r in resultados:
        estado = r["estado"]
        conteo[estado] = conteo.get(estado, 0) + 1
    return conteo


def primas_por_aseguradora(resultados):
    """
    Devuelve un diccionario aseguradora -> suma de primas de pólizas no vencidas,
    ordenado de mayor a menor suma.
    """
    suma = {}
    for r in resultados:
        if r["estado"] == "Vencida":
            continue
        aseguradora = r["aseguradora"]
        prima = r["prima"] if r["prima"] is not None else 0
        suma[aseguradora] = suma.get(aseguradora, 0) + prima
    return dict(sorted(suma.items(), key=lambda item: item[1], reverse=True))


def buscar_inconsistencias(resultados):
    """
    Devuelve una lista de textos con los 3 tipos de problema:
    (1) cliente del maestro sin ninguna póliza,
    (2) póliza cuya cédula no está en el maestro,
    (3) póliza sin prima o con fecha ilegible.
    """
    clientes_df = cargar_clientes()
    polizas = cargar_polizas()
    inconsistencias = []

    # (1) Clientes del maestro sin ninguna póliza.
    cedulas_con_poliza = set()
    for p in polizas:
        if p["cedula"] is not None:
            cedulas_con_poliza.add(str(p["cedula"]).strip())

    for _, fila in clientes_df.iterrows():
        cedula = str(fila["Cedula"]).strip()
        nombre = fila.get("Nombre", cedula)
        if cedula not in cedulas_con_poliza:
            inconsistencias.append(f"Cliente sin póliza: cédula {cedula} ({nombre})")

    # (2) Póliza cuya cédula no está en el maestro.
    cedulas_maestro = set()
    for _, fila in clientes_df.iterrows():
        cedulas_maestro.add(str(fila["Cedula"]).strip())

    for p in polizas:
        if p["cedula"] is not None and str(p["cedula"]).strip() not in cedulas_maestro:
            inconsistencias.append(
                f"Cédula no registrada: póliza {p['numero']}, cédula {p['cedula']}"
            )

    # (3) Póliza sin prima o con fecha ilegible.
    for p in polizas:
        problemas = []
        if p["prima"] is None:
            problemas.append("prima vacía")
        if p["desde"] is None or p["hasta"] is None:
            problemas.append("fecha ilegible")
        if problemas:
            inconsistencias.append(
                f"Póliza {p['numero']}: {', '.join(problemas)}"
            )

    return inconsistencias


def buscar_por_numero(numero):
    """Busca y devuelve la póliza cuyo número coincida, o None si no existe."""
    polizas = cargar_polizas()
    for p in polizas:
        if p["numero"] == numero:
            return p
    return None
