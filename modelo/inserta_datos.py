"""
Módulo para manejar la inserción de datos en una base de datos SQL Server.

Este módulo contiene la clase InsertaDatos, que proporciona métodos para conectar a una base de datos SQL Server,
insertar datos desde un DataFrame de pandas en una tabla temporal, y mover los datos de la tabla temporal a la tabla principal.

Clases:
-------
- InsertaDatos: Clase para manejar la inserción de datos en una base de datos SQL Server.

Dependencias:
-------------
- pyodbc
- os.getenv
- vista.logger.Logger
"""

import pyodbc
from os import getenv
from vista.logger import Logger


class InsertaDatos:
    """
    Clase para manejar la inserción de datos en una base de datos SQL Server.

    Atributos:
    ----------
    servidor : str
        Dirección del servidor SQL.
    usuario : str
        Nombre de usuario para la conexión a la base de datos.
    clave : str
        Contraseña para la conexión a la base de datos.
    obj_log : Logger
        Objeto para manejar el registro de logs.
    cnx : pyodbc.Connection
        Objeto de conexión a la base de datos.
    cursor : pyodbc.Cursor
        Objeto cursor para ejecutar consultas SQL.
    """

    def __init__(self):
        """
        Inicializa la clase InsertaDatos con las credenciales de la base de datos.
        """
        self.servidor = getenv("SERVIDOR_SQL")
        self.usuario = getenv("USUARIO_SQL")
        self.clave = getenv("CONTRASENA_SQL")
        self.bd_datasteward = getenv("BD_DATASTEWARD")
        self.obj_log = Logger()

    def conexion_sql(self) -> bool:
        """
        Establece la conexión a la base de datos SQL Server.

        Returns:
        --------
        bool
            True si la conexión es exitosa, False en caso contrario.
        """
        try:
            self.cnx = pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.servidor};DATABASE={self.bd_datasteward};UID={self.usuario};PWD={self.clave}"
            )
            self.cursor = self.cnx.cursor()
            self.cursor.fast_executemany = True
            # Registro log
            self.obj_log.log("Conexion exitosa a la base de datos")
            return True
        except Exception as err:
            # Registro log
            self.obj_log.error(f"Error en la conexión a la base de datos: {err}")
            return False

    def insertar_datos(self, dataframe) -> bool:
        """
        Inserta los datos de un DataFrame en la tabla temporal y ejecuta el delta.

        Todo ocurre en una sola transacción: si algún paso falla, se deshace
        y la tabla temporal queda como estaba.

        Parámetros:
        -----------
        dataframe : pandas.DataFrame
            DataFrame que contiene los datos a insertar.

        Returns:
        --------
        bool
            True si la inserción y el delta terminan bien, False en caso contrario.
        """
        query_sql = "INSERT INTO DATASTEWARD..reporte_dda_temp VALUES (?,?)"

        try:
            # Limpia restos de corridas anteriores que hayan fallado
            self.cursor.execute("DELETE FROM DATASTEWARD..reporte_dda_temp")
            if dataframe.empty:
                self.obj_log.log("El archivo no tiene registros de Delivery")
            else:
                self.cursor.setinputsizes(self.typeToSize(dataframe))
                self.cursor.executemany(query_sql, dataframe.values.tolist())
            self.delta_data()
            self.cnx.commit()
            self.obj_log.log("Insersión de datos exitosa")
            return True
        except Exception as e:
            try:
                self.cnx.rollback()
            except Exception:
                pass
            self.obj_log.error(
                f"Error al insertar información a la base de datos, se deshacen los cambios: {e}\n"
            )
            return False
        finally:
            self.cursor.close()
            self.cnx.close()

    def typeToSize(self, df):
        """
        Determina los tamaños de los tipos de datos en el DataFrame para la inserción en la base de datos.

        Parámetros:
        -----------
        df : pandas.DataFrame
            DataFrame que contiene los datos a insertar.

        Returns:
        --------
        list
            Lista de tamaños de los tipos de datos.
        """
        try:
            types = df.dtypes.values.tolist()
            size = []

            for i in types:
                if (i == "int64") or (i == "int32"):
                    size.append([pyodbc.SQL_INTEGER])
                if i == "O":
                    size.append([(pyodbc.SQL_WVARCHAR, 255, 0)])
                if i == "float64":
                    size.append([pyodbc.SQL_DOUBLE])
                if (i == "<M8[ns]") or (i == "datetime64[ns]"):
                    size.append([pyodbc.SQL_TYPE_DATE])
                if i == "bool":
                    size.append([pyodbc.SQL_INTEGER])
            return size
        except Exception as e:
            self.obj_log.error(f"error size {e}")

    def delta_data(self):
        """
        Copia a la tabla principal los VIN que aún no existen y limpia la tabla temporal.

        Si un VIN viene repetido en el archivo se inserta una sola vez, con la
        fecha de entrega más reciente. Los errores se propagan para que
        insertar_datos deshaga la transacción.
        """
        sql_query = """INSERT INTO DATASTEWARD..reporte_dda (vin, fecha_entrega, fecha_registro)
                        SELECT t.vin, MAX(t.fecha_entrega), GETDATE()
                        FROM DATASTEWARD..reporte_dda_temp t
                        WHERE t.vin IS NOT NULL
                          AND NOT EXISTS (SELECT 1 FROM DATASTEWARD..reporte_dda d
                                          WHERE d.vin = t.vin)
                        GROUP BY t.vin
                    """
        sql_query_limpiar = "DELETE FROM DATASTEWARD..reporte_dda_temp"

        self.cursor.execute(sql_query)
        nuevos = self.cursor.rowcount
        self.cursor.execute(sql_query_limpiar)
        self.obj_log.log(f"Se ejecuta Delta correctamente: {nuevos} VIN nuevos")
