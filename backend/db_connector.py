"""
Conector de Base de Datos Abstracto para Hospital Dashboard AI.
Soporta PostgreSQL, SQL Server (T-SQL) y Oracle Database.
"""
import asyncio
import logging
import os
import re
from typing import Any, Dict, List, Optional

# Configuracion del log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_connector")

# Variables de configuracion del entorno
DB_ENGINE = os.getenv("DB_ENGINE", "postgres").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hospital:hospital123@db:5432/hospital")

# Parametros para conexiones directas (MSSQL u Oracle)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "")
DB_USER = os.getenv("DB_USER", "hospital")
DB_PASSWORD = os.getenv("DB_PASSWORD", "hospital123")
DB_NAME = os.getenv("DB_NAME", "hospital")
POSTGRES_POOL_MIN_SIZE = int(os.getenv("POSTGRES_POOL_MIN_SIZE", "1"))
POSTGRES_POOL_MAX_SIZE = int(os.getenv("POSTGRES_POOL_MAX_SIZE", "10"))


class UnsafeQueryError(ValueError):
    """Raised when a query does not satisfy the read-only policy."""


_BLOCKED_SQL_TOKENS = re.compile(
    r"\b("
    r"alter|analyze|call|copy|create|delete|do|drop|exec|execute|grant|"
    r"insert|into|merge|replace|reset|revoke|set|truncate|update|vacuum"
    r")\b",
    re.IGNORECASE,
)


def _strip_sql_literals_and_comments(sql: str) -> str:
    """Strip comments and literals before keyword validation."""
    without_block_comments = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    without_line_comments = re.sub(r"--[^\r\n]*", " ", without_block_comments)
    without_single_quotes = re.sub(r"'(?:''|[^'])*'", "''", without_line_comments)
    without_double_quotes = re.sub(r'"(?:""|[^"])*"', '""', without_single_quotes)
    return re.sub(r"\s+", " ", without_double_quotes).strip()


def assert_read_only_query(sql: str) -> None:
    """
    Validate that a query is a single read-only SELECT/WITH statement.

    The dashboard builds read SQL and the AI is instructed to do the same. This
    guard prevents a direct API call or prompt-injected model output from running
    destructive DDL/DML against the hospital database.
    """
    if not sql or not sql.strip():
        raise UnsafeQueryError("La consulta SQL esta vacia.")

    statement = _strip_sql_literals_and_comments(sql)
    if not statement:
        raise UnsafeQueryError("La consulta SQL esta vacia.")

    if statement.endswith(";"):
        statement = statement[:-1].strip()
    if ";" in statement:
        raise UnsafeQueryError("Solo se permite ejecutar una sentencia SQL.")

    first_token = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)", statement)
    if not first_token or first_token.group(1).lower() not in {"select", "with"}:
        raise UnsafeQueryError("Solo se permiten consultas SELECT de solo lectura.")

    blocked = _BLOCKED_SQL_TOKENS.search(statement)
    if blocked:
        raise UnsafeQueryError(
            f"La consulta contiene una operacion no permitida: {blocked.group(1).upper()}."
        )


class DatabaseClient:
    """Cliente unificado para interactuar con la BD segun el motor seleccionado."""

    def __init__(self):
        self.engine = DB_ENGINE
        self.asyncpg = None
        self.pymssql = None
        self.oracledb = None
        self._postgres_pool = None
        self._postgres_pool_lock: Optional[asyncio.Lock] = None
        logger.info("Inicializando DatabaseClient con motor: %s", self.engine.upper())

    def _load_driver(self) -> None:
        """Load the selected DB driver lazily."""
        if self.engine == "postgres":
            if self.asyncpg is not None:
                return
            import asyncpg

            self.asyncpg = asyncpg
        elif self.engine == "mssql":
            if self.pymssql is not None:
                return
            import pymssql

            self.pymssql = pymssql
        elif self.engine == "oracle":
            if self.oracledb is not None:
                return
            import oracledb

            self.oracledb = oracledb
            use_thick_client = os.getenv("ORACLE_THICK", "").lower() in {"1", "true", "yes"}
            if use_thick_client and hasattr(self.oracledb, "init_oracle_client"):
                self.oracledb.init_oracle_client()

    async def close(self) -> None:
        """Close shared resources such as the PostgreSQL pool."""
        if self._postgres_pool is not None:
            await self._postgres_pool.close()
            self._postgres_pool = None

    def _get_postgres_pool_lock(self) -> asyncio.Lock:
        if self._postgres_pool_lock is None:
            self._postgres_pool_lock = asyncio.Lock()
        return self._postgres_pool_lock

    async def _get_postgres_pool(self):
        self._load_driver()
        if self._postgres_pool is not None:
            return self._postgres_pool

        async with self._get_postgres_pool_lock():
            if self._postgres_pool is None:
                self._postgres_pool = await self.asyncpg.create_pool(
                    DATABASE_URL,
                    min_size=POSTGRES_POOL_MIN_SIZE,
                    max_size=POSTGRES_POOL_MAX_SIZE,
                )
        return self._postgres_pool

    async def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Ejecuta una consulta SQL y devuelve una lista de diccionarios."""
        assert_read_only_query(sql)

        if self.engine == "postgres":
            return await self._execute_postgres(sql)
        if self.engine == "mssql":
            return await asyncio.to_thread(self._execute_mssql, sql)
        if self.engine == "oracle":
            return await asyncio.to_thread(self._execute_oracle, sql)
        raise ValueError(f"Motor de base de datos no soportado: {self.engine}")

    async def _execute_postgres(self, sql: str) -> List[Dict[str, Any]]:
        """Ejecuta query en PostgreSQL usando asyncpg de forma asincrona nativa."""
        pool = await self._get_postgres_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql)
            return [dict(row) for row in rows]

    def _execute_mssql(self, sql: str) -> List[Dict[str, Any]]:
        """Ejecuta query en SQL Server usando pymssql en un hilo secundario."""
        self._load_driver()
        port = int(DB_PORT) if DB_PORT else 1433
        conn = self.pymssql.connect(
            server=DB_HOST,
            port=port,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8",
        )
        try:
            with conn.cursor(as_dict=True) as cursor:
                cursor.execute(sql)
                return list(cursor.fetchall())
        finally:
            conn.close()

    def _execute_oracle(self, sql: str) -> List[Dict[str, Any]]:
        """Ejecuta query en Oracle usando oracledb en un hilo secundario."""
        self._load_driver()
        port = int(DB_PORT) if DB_PORT else 1521
        dsn = f"{DB_HOST}:{port}/{DB_NAME}"

        conn = self.oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=dsn,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                col_names = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(col_names, row)) for row in rows]
        finally:
            conn.close()


# Instancia singleton para compartir en la aplicacion
db_client = DatabaseClient()
