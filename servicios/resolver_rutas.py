"""modulo para resolver rutas base y rutas relativas"""
import os
import sys

def resource_path(ruta_relativa):
    """resuelve las rutas"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path,ruta_relativa)

_EXTENSIONES_EXCEL = (".xlsx", ".xls")


def es_excel(nombre):
    """Indica si el nombre corresponde a un archivo de Excel (el reporte DDA)."""
    return nombre.lower().endswith(_EXTENSIONES_EXCEL)
