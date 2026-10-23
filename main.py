from os import getenv, makedirs, path
from dotenv import load_dotenv
from servicios.resolver_rutas import resource_path
from controlador.lectura_archivo_controlador import etl_dda_controlador


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

    obj_controlador = etl_dda_controlador()
    obj_controlador.procesar_reporte_dda()
