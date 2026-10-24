"""
Módulo para procesar archivos y manejar la inserción de datos en una base de datos SQL Server.

Este módulo contiene la clase ProcesarArchivo, que proporciona métodos para leer, procesar y eliminar archivos,
así como insertar datos filtrados en una base de datos SQL Server.

Clases:
-------
- ProcesarArchivo: Clase para procesar archivos y manejar la inserción de datos en una base de datos SQL Server.

Dependencias:
-------------
- pandas
- vista.logger.Logger
- servicios.resolver_rutas.resource_path
- os.getenv
- os.listdir
- os.path
- os.remove
- modelo.inserta_datos.InsertaDatos
"""

import pandas as pd
from vista.logger import Logger
from servicios.resolver_rutas import es_excel, resource_path
from datetime import datetime
from os import getenv, listdir, makedirs, path, remove, replace
from modelo.inserta_datos import InsertaDatos

_CARPETA_RECHAZADOS = "rechazados"
_BYTES_DIAGNOSTICO = 64


class ProcesarArchivo:
    """
    Clase para procesar archivos y manejar la inserción de datos en una base de datos SQL Server.

    Atributos:
    ----------
    archivo_reporte : str
        Ruta del archivo de reporte.
    obj_log : Logger
        Objeto para manejar el registro de logs.
    dataframe_filtrado : pandas.DataFrame
        DataFrame para almacenar los datos filtrados.
    obj_inserta_datos : InsertaDatos
        Objeto para manejar la inserción de datos en la base de datos.
    """

    def __init__(self):
        """
        Inicializa la clase ProcesarArchivo con la ruta del archivo de reporte y un objeto de registro de logs.
        """
        self.recursos = resource_path(getenv("DESCARGA_REPORTE"))  # leer ruta archivo
        self.obj_log = Logger()  # Creamos objeto log
        self.dataframe_filtrado = pd.DataFrame()
        self.obj_inserta_datos = InsertaDatos()

    def leer_modificar_archivo(self) -> bool:
        """
        Lee y procesa el archivo de reporte.

        Returns:
        --------
        bool
            True si los datos se cargaron en la base de datos, False en caso contrario.
        """

        self.archivo_reporte = self.listar_archivos(self.recursos)

        if self.archivo_reporte is None:
            self.obj_log.error(f"No se encontró ningún archivo Excel en {self.recursos}\n")
            return False

        # Si el archivo no sirve se aparta en "rechazados" para revisarlo sin volver a leerlo
        if self.archivo_vacio():
            self.rechazar_archivo()
            return False

        try:
            self.leer_archivo()
        except Exception as ex:
            self.obj_log.error(f"Error al leer el archivo: {ex}\n")
            self.rechazar_archivo()
            return False

        return self.procesar_archivo()

    def archivo_vacio(self):
        """
        Verifica si el archivo de reporte está vacío.

        Returns:
        --------
        bool
            True si el archivo está vacío, False en caso contrario.
        """
        if path.getsize(self.archivo_reporte) == 0:
            self.obj_log.error("Archivo vacío\n")
            return True
        return False

    def leer_archivo(self):
        """
        Lee el archivo de reporte y lo carga en un DataFrame.
        """
        self.dataframe = pd.read_excel(self.archivo_reporte)
        self.obj_log.log(
            f"Se lee correctamente el archivo {path.basename(self.archivo_reporte)}"
        )

    def procesar_archivo(self) -> bool:
        """
        Filtra los datos del archivo y los inserta en la base de datos.

        Returns:
        --------
        bool
            True si la inserción terminó bien, False en caso contrario.
        """
        exito = False
        try:
            # Filtramos los datos del archivo y lo guardamos en un nuevo Dataframe
            self.dataframe_filtrado = self.dataframe.loc[
                (self.dataframe["Process"] == "Delivery"), ["VIN", "End_Date"]
            ]
            # Conectamos a la base de datos
            if self.obj_inserta_datos.conexion_sql():
                # Insertamos los datos filtrados ala base de datos
                exito = self.obj_inserta_datos.insertar_datos(self.dataframe_filtrado)

        except Exception as ex:
            # Registramos log
            self.obj_log.error(f"Error al procesar el archivo: {ex}")

        finally:
            # Eliminamos archivo
            self.eliminar_archivo()

        return exito

    def eliminar_archivo(self):
        """
        Elimina el archivo de reporte.
        """
        try:
            remove(self.archivo_reporte)
            self.obj_log.log("El archivo ha sido eliminado\n")
        except Exception as err:
            # Registramos log
            self.obj_log.error(f"Error al eliminar el archivo {err}\n")

    def rechazar_archivo(self):
        """
        Mueve el archivo que no se pudo usar a la subcarpeta "rechazados" y registra
        su nombre, tamaño y primeros bytes para poder diagnosticar qué se descargó.
        """
        try:
            nombre = path.basename(self.archivo_reporte)
            tamano = path.getsize(self.archivo_reporte)
            with open(self.archivo_reporte, "rb") as archivo:
                inicio = archivo.read(_BYTES_DIAGNOSTICO)
            self.obj_log.error(
                f"Archivo rechazado: {nombre} ({tamano} bytes). Primeros bytes: {inicio!r}"
            )
            carpeta = path.join(self.recursos, _CARPETA_RECHAZADOS)
            makedirs(carpeta, exist_ok=True)
            destino = path.join(carpeta, f"{datetime.now():%Y%m%d_%H%M%S}_{nombre}")
            replace(self.archivo_reporte, destino)
            self.obj_log.log(f"El archivo se movió a {destino}\n")
        except Exception as err:
            self.obj_log.error(f"Error al mover el archivo a rechazados: {err}\n")
            self.eliminar_archivo()

    def listar_archivos(self, recursos) -> str:
        """
        Devuelve el Excel más reciente de la carpeta (sin entrar en subcarpetas),
        o None si no hay ninguno. Los demás archivos se ignoran. Si hay varios
        archivos, los registra en el log.
        """
        archivos = [
            path.join(recursos, elemento)
            for elemento in listdir(recursos)
            if path.isfile(path.join(recursos, elemento))
        ]
        if len(archivos) > 1:
            detalle = ", ".join(
                f"{path.basename(a)} ({path.getsize(a)} bytes)" for a in sorted(archivos)
            )
            self.obj_log.log(f"Hay varios archivos en {recursos}: {detalle}")
        excels = [a for a in archivos if es_excel(path.basename(a))]
        if not excels:
            return None
        elegido = max(excels, key=path.getmtime)
        if len(archivos) > 1:
            self.obj_log.log(f"Se usa el más reciente: {path.basename(elegido)}")
        return elegido
