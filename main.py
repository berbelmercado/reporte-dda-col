import sys
import traceback
from os import getenv, makedirs, path
from dotenv import load_dotenv
from servicios.resolver_rutas import resource_path
from controlador.lectura_archivo_controlador import etl_dda_controlador
from infraestructura.cliente_correo import ClienteCorreo
from vista.logger import Logger


def crear_carpetas():
    """Crea las carpetas del log y de descarga si no existen."""
    carpetas = (
        path.dirname(resource_path(getenv("ARCHIVO_LOG"))),
        resource_path(getenv("DESCARGA_REPORTE")),
    )
    for carpeta in carpetas:
        makedirs(carpeta, exist_ok=True)


if __name__ == "__main__":

    load_dotenv(resource_path(".env"))
    crear_carpetas()
    obj_log = Logger()
    obj_log.inicio_ejecucion()

    try:
        obj_controlador = etl_dda_controlador()
        exito = obj_controlador.procesar_reporte_dda()
    except Exception:
        obj_log.error(f"Error inesperado:\n{traceback.format_exc()}")
        exito = False

    if not exito:
        ClienteCorreo().enviar_alerta_fallo(obj_log.log_ejecucion_actual())

    obj_log.fin_ejecucion(exito)

    # Código de salida distinto de 0 para que el Programador de tareas marque el fallo
    sys.exit(0 if exito else 1)
