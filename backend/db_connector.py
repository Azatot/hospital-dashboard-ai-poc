"""
Conector de Base de Datos Abstracto para Hospital Dashboard AI
Soporta PostgreSQL, SQL Server (T-SQL) y Oracle Database (Thin Client)
"""
import os
import asyncio
import logging
from typing import List, Dict, Any, Optional

# Configuración del log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_connector")

# Variables de configuración del entorno
DB_ENGINE = os.getenv("DB_ENGINE", "postgres").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hospital:hospital123@db:5432/hospital")

# Parámetros para conexiones directas (MSSQL u Oracle)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "")
DB_USER = os.getenv("DB_USER", "hospital")
DB_PASSWORD = os.getenv("DB_PASSWORD", "hospital123")
DB_NAME = os.getenv("DB_NAME", "hospital")

class DatabaseClient:
    """Cliente unificado para interactuar con la BD según el motor seleccionado"""
    
    def __init__(self):
        self.engine = DB_ENGINE
        logger.info(f"🔌 Inicializando DatabaseClient con motor: {self.engine.upper()}")
        
        # Cargar drivers dinámicamente si es necesario
        if self.engine == "postgres":
            import asyncpg
            self.asyncpg = asyncpg
        elif self.engine == "mssql":
            import pymssql
            self.pymssql = pymssql
        elif self.engine == "oracle":
            import oracledb
            self.oracledb = oracledb
            # Forzar cliente en modo THIN (sin requerir librerías nativas de Oracle)
            self.oracledb.init_oracle_client() if hasattr(self.oracledb, "init_oracle_client") and not os.getenv("ORACLE_THICK") else None

    async def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Ejecuta una consulta SQL y devuelve una lista de diccionarios"""
        if self.engine == "postgres":
            return await self._execute_postgres(sql)
        elif self.engine == "mssql":
            return await asyncio.to_thread(self._execute_mssql, sql)
        elif self.engine == "oracle":
            return await asyncio.to_thread(self._execute_oracle, sql)
        else:
            raise ValueError(f"Motor de base de datos no soportado: {self.engine}")

    async def _execute_postgres(self, sql: str) -> List[Dict[str, Any]]:
        """Ejecuta query en PostgreSQL usando asyncpg de forma asíncrona nativa"""
        # Intentar conectar usando DATABASE_URL
        conn = await self.asyncpg.connect(DATABASE_URL)
        try:
            rows = await conn.fetch(sql)
            return [dict(row) for row in rows]
        finally:
            await conn.close()

    def _execute_mssql(self, sql: str) -> List[Dict[str, Any]]:
        """Ejecuta query en SQL Server usando pymssql (en un hilo secundario)"""
        port = int(DB_PORT) if DB_PORT else 1433
        # Conectar
        conn = self.pymssql.connect(
            server=DB_HOST,
            port=port,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8'
        )
        try:
            with conn.cursor(as_dict=True) as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                #pymssql ya devuelve dicts gracias a as_dict=True
                return list(rows)
        finally:
            conn.close()

    def _execute_oracle(self, sql: str) -> List[Dict[str, Any]]:
        """Ejecuta query en Oracle usando oracledb Thin Client (en un hilo secundario)"""
        port = int(DB_PORT) if DB_PORT else 1521
        
        # En Oracle Thin, la cadena de conexión suele ser host:port/service_name
        dsn = f"{DB_HOST}:{port}/{DB_NAME}"
        
        conn = self.oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=dsn
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                # Obtener metadatos de las columnas para armar los diccionarios
                col_names = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    result.append(dict(zip(col_names, row)))
                return result
        finally:
            conn.close()

# Instancia singleton para compartir en la aplicación
db_client = DatabaseClient()
