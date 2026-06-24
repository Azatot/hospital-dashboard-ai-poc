"""
Generador de configuraciones de gráficos usando IA (via OpenRouter/API local)
Convierte lenguaje natural a SQL y configuraciones de visualización
"""
import json
import re
from typing import Dict, Any, List, Optional
import httpx
from models import ChartConfiguration, ChartType, Area, TimeRange
import os
from db_connector import DB_ENGINE

# Configuración de IA
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEFAULT_MODEL = os.getenv("AI_MODEL", "deepseek/deepseek-v4-flash:free")

# Esquema de la base de datos para contexto
DB_SCHEMA = """
TABLAS DISPONIBLES:

1. URGENCIAS
   - id: INTEGER
   - paciente_id: INTEGER (FK)
   - fecha_entrada: TIMESTAMP
   - fecha_atencion_medica: TIMESTAMP
   - fecha_alta: TIMESTAMP
   - triaje_nivel: INTEGER (1-5, 1=crítico, 5=no urgente)
   - motivo: VARCHAR
   - diagnostico: VARCHAR
   - destino: VARCHAR ('ALTA', 'INGRESO', 'FALLECIMIENTO', 'FUGA')
   - box: INTEGER
   - tiempo_espera_minutos: INTEGER (calculado)

2. CIRUGIAS
   - id: INTEGER
   - paciente_id: INTEGER (FK)
   - quirofano_id: INTEGER (FK)
   - fecha_programada: DATE
   - hora_inicio_programada: TIME
   - hora_inicio_real: TIME
   - hora_fin: TIME
   - tipo_cirugia: VARCHAR
   - cirujano: VARCHAR
   - estado: VARCHAR ('COMPLETADA', 'CANCELADA', 'EN_CURSO', 'PROGRAMADA')
   - motivo_cancelacion: VARCHAR

3. CONSULTAS_EXTERNAS
   - id: INTEGER
   - paciente_id: INTEGER (FK)
   - especialidad: VARCHAR
   - medico: VARCHAR
   - fecha_cita: TIMESTAMP
   - fecha_atencion: TIMESTAMP
   - estado: VARCHAR ('ATENDIDA', 'NO_SHOW', 'CANCELADA', 'PENDIENTE')
   - tipo: VARCHAR ('PRIMERA_VISITA', 'REVISIT', 'CONTROL')

4. PACIENTES
   - id: INTEGER
   - nombre: VARCHAR
   - edad: INTEGER
   - genero: CHAR('M', 'F', 'O')
   - fecha_registro: TIMESTAMP
   - tipo_ingreso: VARCHAR

5. CAMAS
   - id: INTEGER
   - numero: VARCHAR
   - servicio: VARCHAR ('UC', 'UCI', 'MEDICINA', 'CIRUGIA', 'PEDIATRIA')
   - estado: VARCHAR ('OCUPADA', 'LIBRE', 'LIMPIEZA')
"""

# Mapeo de intenciones a tipos de gráfico
CHART_PATTERNS = {
    r"evoluci[oó]n|tendencia|historico|serie temporal": ChartType.LINE,
    r"comparar|comparaci[oó]n|versus|dif.*rencia": ChartType.BAR,
    r"distribuci[oó]n|porcentaje|proporci[oó]n": ChartType.PIE,
    r"acumulado|acumula": ChartType.AREA,
    r"puntos|dispersi[oó]n|scatter": ChartType.SCATTER,
    r"^ocupaci[oó]n$|indicador|gauge|tasa actual$": ChartType.GAUGE,
    r"heatmap|mapa de calor|calor": ChartType.HEATMAP,
    r"tabla|listado|detalle": ChartType.TABLE,
}

# Mapeo de áreas
AREA_PATTERNS = {
    r"urgencia|emergencia|urgencias|ER": Area.URGENCIAS,
    r"quir[oó]fano|cirug[ií]a|operaci[oó]n": Area.QUIROFANOS,
    r"consulta|externa|ambulatorio|cita": Area.CONSULTAS_EXTERNAS,
    r"cama|ingreso|planta|uci|hospitalizaci[oó]n": Area.CAMAS,
}

# Mapeo de rangos de tiempo
TIME_PATTERNS = {
    r"hoy|este d[ií]a|dia (actual|de hoy)": TimeRange.TODAY,
    r"ayer|d[ií]a (pasado|anterior)": TimeRange.YESTERDAY,
    r"(ultima|última) semana|7 d[ií]as|semanal": TimeRange.LAST_7_DAYS,
    r"(ultimo|último) mes|30 d[ií]as|mensual": TimeRange.LAST_30_DAYS,
    r"este mes|mes actual": TimeRange.THIS_MONTH,
    r"mes (pasado|anterior)": TimeRange.LAST_MONTH,
    r"este a[ñn]o|a[ñn]o actual|anual": TimeRange.THIS_YEAR,
}

class AIGraphGenerator:
    """Generador de gráficos basado en IA"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or OPENROUTER_API_KEY
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def _detect_chart_type(self, query: str) -> ChartType:
        """Detecta el tipo de gráfico desde el prompt"""
        query_lower = query.lower()
        for pattern, chart_type in CHART_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                return chart_type
        # Detectar palabras de tiempo que indican evolución temporal
        time_words = ["día", "dia", "semana", "mes", "año", "ultimos", "últimos", "pasado", "anterior", "historico", "evolución", "tendencia"]
        if any(word in query_lower for word in time_words):
            return ChartType.LINE
        
        if "tiempo" in query_lower or "fecha" in query_lower:
            return ChartType.LINE
        if "por" in query_lower and any(x in query_lower for x in ["categor", "tipo", "estado", "especialidad", "servicio"]):
            return ChartType.BAR
        return ChartType.LINE
    
    def _detect_area(self, query: str) -> Area:
        """Detecta el área hospitalaria desde el prompt"""
        query_lower = query.lower()
        for pattern, area in AREA_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                return area
        return Area.GLOBAL
    
    def _detect_time_range(self, query: str) -> TimeRange:
        """Detecta el rango de tiempo desde el prompt"""
        query_lower = query.lower()
        for pattern, time_range in TIME_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                return time_range
        return TimeRange.LAST_7_DAYS
    
    def _build_system_prompt(self) -> str:
        """Construye el prompt del sistema para la IA adaptado a la base de datos"""
        if DB_ENGINE == "mssql":
            rules = """
1. Genera SOLO consultas SELECT válidas para Microsoft SQL Server (T-SQL)
2. Usa nombres de columnas exactamente como aparecen en el esquema
3. Para tiempo, usa CAST(columna AS DATE) o DATEDIFF/DATEADD para calcular rangos de fecha y diferencias
4. Para diferencias temporales en minutos, usa DATEDIFF(minute, fecha_inicio, fecha_fin)
5. Para límites de resultados, usa SELECT TOP N en lugar de LIMIT
6. Usa aliases descriptivos para las columnas
7. Para agregaciones, usa COUNT, SUM, AVG según corresponda
8. Ordena resultados cronológicamente cuando sea serie temporal"""
        elif DB_ENGINE == "oracle":
            rules = """
1. Genera SOLO consultas SELECT válidas para Oracle Database (PL/SQL)
2. Usa nombres de columnas exactamente como aparecen en el esquema
3. Para tiempo, usa TRUNC(columna) o aritmética directa (ej. (fecha_fin - fecha_inicio)*24*60) para diferencias en minutos
4. Para límites de resultados, usa FETCH FIRST N ROWS ONLY al final de la consulta (no uses LIMIT ni TOP)
5. Usa aliases descriptivos para las columnas sin la palabra AS si genera conflictos, pero preferiblemente aliases válidos
6. Para agregaciones, usa COUNT, SUM, AVG según corresponda
7. Ordena resultados cronológicamente cuando sea serie temporal"""
        else: # postgres
            rules = """
1. Genera SOLO consultas SELECT válidas para PostgreSQL
2. Usa nombres de columnas exactamente como aparecen en el esquema
3. Para tiempo, usa siempre DATE() o funciones de fecha PostgreSQL
4. Incluye filtros de fecha apropiados usando NOW() - INTERVAL
5. Para diferencias en minutos, usa EXTRACT(EPOCH FROM (fecha_fin - fecha_inicio))/60
6. Usa aliases descriptivos para las columnas
7. Para agregaciones, usa COUNT, SUM, AVG según corresponda
8. Ordena resultados cronológicamente cuando sea serie temporal"""

        return f"""Eres un asistente especializado en análisis de datos hospitalarios.
Tu tarea es convertir solicitudes en lenguaje natural a consultas SQL y configuraciones de visualización.

{DB_SCHEMA}

REGLAS IMPORTANTES:
{rules}

Tu respuesta debe ser JSON con el siguiente formato:
{{
    "chart_type": "line|bar|pie|area|gauge|table",
    "title": "Título descriptivo",
    "subtitle": "Subtítulo opcional",
    "sql": "Consulta SQL completa",
    "x_axis": "nombre_columna_x",
    "y_axis": "nombre_columna_y",
    "group_by": "columna_agrupación (opcional)",
    "area": "urgencias|quirofanos|consultas_externas|camas|global",
    "time_range": "hoy|ayer|ultimos_7_dias|ultimos_30_dias|este_mes|mes_pasado|este_año",
    "explanation": "Explicación en lenguaje natural de qué muestra el gráfico",
    "confidence": 0.95
}}"""

    def _parse_ai_json(self, content: str) -> Dict[str, Any]:
        """Parsea respuestas JSON aunque el modelo las envuelva en markdown."""
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE | re.DOTALL).strip()
        return json.loads(cleaned)
    
    async def generate_chart_config(self, user_query: str) -> ChartConfiguration:
        """Genera configuración de gráfico usando IA"""
        
        if not self.api_key:
            # Fallback: generación basada en reglas sin IA externa
            return self._generate_fallback_config(user_query)
        
        # Llamada a la API de IA
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://hospital-dashboard.local",
                    },
                    json={
                        "model": DEFAULT_MODEL,
                        "messages": [
                            {"role": "system", "content": self._build_system_prompt()},
                            {"role": "user", "content": f"Genera un gráfico para: {user_query}"}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1000,
                        "response_format": {"type": "json_object"}
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices") or []
                content = choices[0].get("message", {}).get("content") if choices else None
                if not content:
                    raise ValueError("La respuesta de IA no contiene contenido.")

                ai_response = self._parse_ai_json(content)
                
                return ChartConfiguration(
                    chart_type=ChartType(ai_response.get("chart_type", "line")),
                    title=ai_response.get("title", "Gráfico Hospitalario"),
                    subtitle=ai_response.get("subtitle"),
                    area=Area(ai_response.get("area", "global")),
                    query_sql=ai_response.get("sql", "SELECT 1"),
                    x_axis=ai_response.get("x_axis"),
                    y_axis=ai_response.get("y_axis"),
                    group_by=ai_response.get("group_by"),
                    time_range=TimeRange(ai_response.get("time_range", "ultimos_7_dias"))
                )
                
            except Exception as e:
                print(f"Error en IA, usando fallback: {e}")
                return self._generate_fallback_config(user_query)
    
    def _generate_fallback_config(self, query: str) -> ChartConfiguration:
        """Generación basada en reglas cuando la IA no disponible"""
        chart_type = self._detect_chart_type(query)
        area = self._detect_area(query)
        time_range = self._detect_time_range(query)
        
        # Construir SQL según el área y tipo de gráfico
        sql, title, x_axis, y_axis = self._build_sql_for_query(query, area, chart_type, time_range)
        
        return ChartConfiguration(
            chart_type=chart_type,
            title=title,
            subtitle=f"Rango: {time_range.value}",
            area=area,
            query_sql=sql,
            x_axis=x_axis,
            y_axis=y_axis,
            time_range=time_range
        )
    
    def _build_sql_for_query(self, query: str, area: Area, chart_type: ChartType, time_range: TimeRange) -> tuple:
        """Construye SQL según contexto y dialecto"""
        
        # 1. Definir filtro de tiempo según el motor
        if DB_ENGINE == "mssql":
            time_filter = {
                TimeRange.TODAY: "CAST(fecha_entrada AS DATE) = CAST(GETDATE() AS DATE)",
                TimeRange.YESTERDAY: "CAST(fecha_entrada AS DATE) = CAST(DATEADD(day, -1, GETDATE()) AS DATE)",
                TimeRange.LAST_7_DAYS: "fecha_entrada >= DATEADD(day, -7, GETDATE())",
                TimeRange.LAST_30_DAYS: "fecha_entrada >= DATEADD(day, -30, GETDATE())",
                TimeRange.THIS_MONTH: "fecha_entrada >= DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0)",
                TimeRange.THIS_YEAR: "fecha_entrada >= DATEADD(year, DATEDIFF(year, 0, GETDATE()), 0)",
            }.get(time_range, "fecha_entrada >= DATEADD(day, -7, GETDATE())")
        elif DB_ENGINE == "oracle":
            time_filter = {
                TimeRange.TODAY: "TRUNC(fecha_entrada) = TRUNC(SYSDATE)",
                TimeRange.YESTERDAY: "TRUNC(fecha_entrada) = TRUNC(SYSDATE) - 1",
                TimeRange.LAST_7_DAYS: "fecha_entrada >= SYSDATE - 7",
                TimeRange.LAST_30_DAYS: "fecha_entrada >= SYSDATE - 30",
                TimeRange.THIS_MONTH: "fecha_entrada >= TRUNC(SYSDATE, 'MM')",
                TimeRange.THIS_YEAR: "fecha_entrada >= TRUNC(SYSDATE, 'YYYY')",
            }.get(time_range, "fecha_entrada >= SYSDATE - 7")
        else: # postgres
            time_filter = {
                TimeRange.TODAY: "DATE(fecha_entrada) = CURRENT_DATE",
                TimeRange.YESTERDAY: "DATE(fecha_entrada) = CURRENT_DATE - 1",
                TimeRange.LAST_7_DAYS: "fecha_entrada >= NOW() - INTERVAL '7 days'",
                TimeRange.LAST_30_DAYS: "fecha_entrada >= NOW() - INTERVAL '30 days'",
                TimeRange.THIS_MONTH: "fecha_entrada >= DATE_TRUNC('month', NOW())",
                TimeRange.THIS_YEAR: "fecha_entrada >= DATE_TRUNC('year', NOW())",
            }.get(time_range, "fecha_entrada >= NOW() - INTERVAL '7 days'")

        # Función auxiliar para adaptar el filtro de tiempo a otra columna
        def get_filter(col):
            return time_filter.replace('fecha_entrada', col)

        # 2. Definir catálogo de consultas por dialecto
        if DB_ENGINE == "mssql":
            queries = {
                Area.URGENCIAS: {
                    "ocupación": (
                        f"""SELECT CAST(fecha_entrada AS DATE) as fecha, 
                            COUNT(*) as total_ingresos,
                            AVG(DATEDIFF(minute, fecha_entrada, fecha_atencion_medica)) as espera_media_min
                        FROM urgencias 
                        WHERE {get_filter('fecha_entrada')} 
                        GROUP BY CAST(fecha_entrada AS DATE) 
                        ORDER BY fecha""",
                        "Ocupación y Espera en Urgencias",
                        "fecha",
                        "total_ingresos"
                    ),
                    "triaje": (
                        f"""SELECT triaje_nivel, COUNT(*) as cantidad 
                        FROM urgencias 
                        WHERE {get_filter('fecha_entrada')} 
                        GROUP BY triaje_nivel 
                        ORDER BY triaje_nivel""",
                        "Distribución por Nivel de Triaje",
                        "triaje_nivel",
                        "cantidad"
                    ),
                    "destino": (
                        f"""SELECT destino, COUNT(*) as cantidad, 
                            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
                        FROM urgencias 
                        WHERE {get_filter('fecha_entrada')} 
                        GROUP BY destino""",
                        "Destino de Pacientes en Urgencias",
                        "destino",
                        "cantidad"
                    ),
                },
                Area.QUIROFANOS: {
                    "utilización": (
                        f"""SELECT TOP 10 tipo_cirugia, 
                            COUNT(*) as total
                        FROM cirugias 
                        WHERE estado = 'COMPLETADA' AND {get_filter('fecha_programada')}
                        GROUP BY tipo_cirugia 
                        ORDER BY total DESC""",
                        "Tipos de Cirugías Más Frecuentes",
                        "tipo_cirugia",
                        "total"
                    ),
                    "cancelaciones": (
                        f"""SELECT estado, COUNT(*) as cantidad,
                            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
                        FROM cirugias 
                        WHERE {get_filter('fecha_programada')}
                        GROUP BY estado""",
                        "Estado de Cirugías",
                        "estado",
                        "cantidad"
                    ),
                },
                Area.CONSULTAS_EXTERNAS: {
                    "no_show": (
                        f"""SELECT estado, COUNT(*) as cantidad,
                            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
                        FROM consultas_externas 
                        WHERE {get_filter('fecha_cita')}
                        GROUP BY estado""",
                        "Estado de Consultas Externas",
                        "estado",
                        "cantidad"
                    ),
                    "especialidad": (
                        f"""SELECT especialidad, COUNT(*) as total_citas
                        FROM consultas_externas 
                        WHERE estado = 'ATENDIDA' AND {get_filter('fecha_cita')}
                        GROUP BY especialidad 
                        ORDER BY total_citas DESC""",
                        "Consultas por Especialidad",
                        "especialidad",
                        "total_citas"
                    ),
                },
                Area.CAMAS: {
                    "ocupación": (
                        """SELECT servicio, COUNT(CASE WHEN estado = 'OCUPADA' THEN 1 END) as ocupadas, COUNT(*) as total 
                        FROM camas GROUP BY servicio""",
                        "Ocupación de Camas por Servicio",
                        "servicio",
                        "ocupadas"
                    ),
                    "estado": (
                        """SELECT estado, COUNT(*) as cantidad FROM camas GROUP BY estado""",
                        "Estado General de Camas",
                        "estado",
                        "cantidad"
                    )
                },
                Area.GLOBAL: {
                    "ingresos": (
                        f"""SELECT CAST(fecha_registro AS DATE) as fecha, COUNT(*) as cantidad 
                        FROM pacientes 
                        WHERE {get_filter('fecha_registro')}
                        GROUP BY CAST(fecha_registro AS DATE) ORDER BY fecha""",
                        "Evolución Global de Registros de Pacientes",
                        "fecha",
                        "cantidad"
                    )
                }
            }
        elif DB_ENGINE == "oracle":
            queries = {
                Area.URGENCIAS: {
                    "ocupación": (
                        f"""SELECT TRUNC(fecha_entrada) as fecha, 
                            COUNT(*) as total_ingresos,
                            AVG((fecha_atencion_medica - fecha_entrada)*24*60) as espera_media_min
                        FROM urgencias 
                        WHERE {get_filter('fecha_entrada')} 
                        GROUP BY TRUNC(fecha_entrada) 
                        ORDER BY fecha""",
                        "Ocupación y Espera en Urgencias",
                        "fecha",
                        "total_ingresos"
                    ),
                    "triaje": (
                        f"""SELECT triaje_nivel, COUNT(*) as cantidad 
                        FROM urgencias 
                        WHERE {get_filter('fecha_entrada')} 
                        GROUP BY triaje_nivel 
                        ORDER BY triaje_nivel""",
                        "Distribución por Nivel de Triaje",
                        "triaje_nivel",
                        "cantidad"
                    ),
                    "destino": (
                        f"""SELECT destino, COUNT(*) as cantidad, 
                            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
                        FROM urgencias 
                        WHERE {get_filter('fecha_entrada')} 
                        GROUP BY destino""",
                        "Destino de Pacientes en Urgencias",
                        "destino",
                        "cantidad"
                    ),
                },
                Area.QUIROFANOS: {
                    "utilización": (
                        f"""SELECT tipo_cirugia, 
                            COUNT(*) as total
                        FROM cirugias 
                        WHERE estado = 'COMPLETADA' AND {get_filter('fecha_programada')}
                        GROUP BY tipo_cirugia 
                        ORDER BY total DESC
                        FETCH FIRST 10 ROWS ONLY""",
                        "Tipos de Cirugías Más Frecuentes",
                        "tipo_cirugia",
                        "total"
                    ),
                    "cancelaciones": (
                        f"""SELECT estado, COUNT(*) as cantidad,
                            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
                        FROM cirugias 
                        WHERE {get_filter('fecha_programada')}
                        GROUP BY estado""",
                        "Estado de Cirugías",
                        "estado",
                        "cantidad"
                    ),
                },
                Area.CONSULTAS_EXTERNAS: {
                    "no_show": (
                        f"""SELECT estado, COUNT(*) as cantidad,
                            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
                        FROM consultas_externas 
                        WHERE {get_filter('fecha_cita')}
                        GROUP BY estado""",
                        "Estado de Consultas Externas",
                        "estado",
                        "cantidad"
                    ),
                    "especialidad": (
                        f"""SELECT especialidad, COUNT(*) as total_citas
                        FROM consultas_externas 
                        WHERE estado = 'ATENDIDA' AND {get_filter('fecha_cita')}
                        GROUP BY especialidad 
                        ORDER BY total_citas DESC""",
                        "Consultas por Especialidad",
                        "especialidad",
                        "total_citas"
                    ),
                },
                Area.CAMAS: {
                    "ocupación": (
                        """SELECT servicio, COUNT(CASE WHEN estado = 'OCUPADA' THEN 1 END) as ocupadas, COUNT(*) as total 
                        FROM camas GROUP BY servicio""",
                        "Ocupación de Camas por Servicio",
                        "servicio",
                        "ocupadas"
                    ),
                    "estado": (
                        """SELECT estado, COUNT(*) as cantidad FROM camas GROUP BY estado""",
                        "Estado General de Camas",
                        "estado",
                        "cantidad"
                    )
                },
                Area.GLOBAL: {
                    "ingresos": (
                        f"""SELECT TRUNC(fecha_registro) as fecha, COUNT(*) as cantidad 
                        FROM pacientes 
                        WHERE {get_filter('fecha_registro')}
                        GROUP BY TRUNC(fecha_registro) ORDER BY fecha""",
                        "Evolución Global de Registros de Pacientes",
                        "fecha",
                        "cantidad"
                    )
                }
            }
        else: # postgres
            queries = {
                Area.URGENCIAS: {
                    "ocupación": (
                        f"""SELECT DATE(fecha_entrada) as fecha, 
                            COUNT(*) as total_ingresos,
                            AVG(EXTRACT(EPOCH FROM (fecha_atencion_medica - fecha_entrada))/60) as espera_media_min
                        FROM urgencias 
                        WHERE {get_filter('fecha_entrada')} 
                        GROUP BY DATE(fecha_entrada) 
                        ORDER BY fecha""",
                        "Ocupación y Espera en Urgencias",
                        "fecha",
                        "total_ingresos"
                    ),
                    "triaje": (
                        f"""SELECT triaje_nivel, COUNT(*) as cantidad 
                        FROM urgencias 
                        WHERE {get_filter('fecha_entrada')} 
                        GROUP BY triaje_nivel 
                        ORDER BY triaje_nivel""",
                        "Distribución por Nivel de Triaje",
                        "triaje_nivel",
                        "cantidad"
                    ),
                    "destino": (
                        f"""SELECT destino, COUNT(*) as cantidad, 
                            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
                        FROM urgencias 
                        WHERE {get_filter('fecha_entrada')} 
                        GROUP BY destino""",
                        "Destino de Pacientes en Urgencias",
                        "destino",
                        "cantidad"
                    ),
                },
                Area.QUIROFANOS: {
                    "utilización": (
                        f"""SELECT tipo_cirugia, 
                            COUNT(*) as total,
                            AVG(EXTRACT(EPOCH FROM (hora_fin - hora_inicio_real))/60) as duracion_media_min
                        FROM cirugias 
                        WHERE estado = 'COMPLETADA' AND {get_filter('fecha_programada')}
                        GROUP BY tipo_cirugia 
                        ORDER BY total DESC 
                        LIMIT 10""",
                        "Tipos de Cirugías Más Frecuentes",
                        "tipo_cirugia",
                        "total"
                    ),
                    "cancelaciones": (
                        f"""SELECT estado, COUNT(*) as cantidad,
                            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
                        FROM cirugias 
                        WHERE {get_filter('fecha_programada')}
                        GROUP BY estado""",
                        "Estado de Cirugías",
                        "estado",
                        "cantidad"
                    ),
                },
                Area.CONSULTAS_EXTERNAS: {
                    "no_show": (
                        f"""SELECT estado, COUNT(*) as cantidad,
                            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
                        FROM consultas_externas 
                        WHERE {get_filter('fecha_cita')}
                        GROUP BY estado""",
                        "Estado de Consultas Externas",
                        "estado",
                        "cantidad"
                    ),
                    "especialidad": (
                        f"""SELECT especialidad, COUNT(*) as total_citas
                        FROM consultas_externas 
                        WHERE estado = 'ATENDIDA' AND {get_filter('fecha_cita')}
                        GROUP BY especialidad 
                        ORDER BY total_citas DESC""",
                        "Consultas por Especialidad",
                        "especialidad",
                        "total_citas"
                    ),
                },
                Area.CAMAS: {
                    "ocupación": (
                        """SELECT servicio, COUNT(CASE WHEN estado = 'OCUPADA' THEN 1 END) as ocupadas, COUNT(*) as total 
                        FROM camas GROUP BY servicio""",
                        "Ocupación de Camas por Servicio",
                        "servicio",
                        "ocupadas"
                    ),
                    "estado": (
                        """SELECT estado, COUNT(*) as cantidad FROM camas GROUP BY estado""",
                        "Estado General de Camas",
                        "estado",
                        "cantidad"
                    )
                },
                Area.GLOBAL: {
                    "ingresos": (
                        f"""SELECT DATE(fecha_registro) as fecha, COUNT(*) as cantidad 
                        FROM pacientes 
                        WHERE {get_filter('fecha_registro')}
                        GROUP BY DATE(fecha_registro) ORDER BY fecha""",
                        "Evolución Global de Registros de Pacientes",
                        "fecha",
                        "cantidad"
                    )
                }
            }
        
        # Buscar patrón en la query
        query_lower = query.lower()
        area_queries = queries.get(area, {})
        
        for pattern, (sql, title, x, y) in area_queries.items():
            if pattern in query_lower:
                return sql, title, x, y
        
        # Query default para el área
        sql, title, x, y = area_queries.get("ocupación", area_queries.get("no_show", area_queries.get("utilización", area_queries.get("ingresos", ("SELECT 1", "Sin datos", "x", "y")))))
        return sql, title, x, y

# Instancia singleton
generator = AIGraphGenerator()

async def generate_chart_from_query(query: str) -> ChartConfiguration:
    """Función de conveniencia"""
    return await generator.generate_chart_config(query)
