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

# Configuración de IA
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEFAULT_MODEL = "deepseek/deepseek-v4-flash:free"

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
        """Construye el prompt del sistema para la IA"""
        return f"""Eres un asistente especializado en análisis de datos hospitalarios.
Tu tarea es convertir solicitudes en lenguaje natural a consultas SQL y configuraciones de visualización.

{DB_SCHEMA}

REGLAS IMPORTANTES:
1. Genera SOLO consultas SELECT válidas para PostgreSQL
2. Usa nombres de columnas exactamente como aparecen en el esquema
3. Para tiempo, usa siempre DATE() o funciones de fecha PostgreSQL
4. Incluye filtros de fecha apropiados usando NOW() - INTERVAL
5. Usa aliases descriptivos para las columnas
6. Para agregaciones, usa COUNT, SUM, AVG según corresponda
7. Ordena resultados cronológicamente cuando sea serie temporal

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
                
                data = response.json()
                ai_response = json.loads(data["choices"][0]["message"]["content"])
                
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
        """Construye SQL según contexto"""
        
        # Definir filtro de tiempo
        time_filter = {
            TimeRange.TODAY: "DATE(fecha_entrada) = CURRENT_DATE",
            TimeRange.YESTERDAY: "DATE(fecha_entrada) = CURRENT_DATE - 1",
            TimeRange.LAST_7_DAYS: "fecha_entrada >= NOW() - INTERVAL '7 days'",
            TimeRange.LAST_30_DAYS: "fecha_entrada >= NOW() - INTERVAL '30 days'",
            TimeRange.THIS_MONTH: "fecha_entrada >= DATE_TRUNC('month', NOW())",
            TimeRange.THIS_YEAR: "fecha_entrada >= DATE_TRUNC('year', NOW())",
        }.get(time_range, "fecha_entrada >= NOW() - INTERVAL '7 days'")
        
        queries = {
            Area.URGENCIAS: {
                "ocupación": (
                    f"""SELECT DATE(fecha_entrada) as fecha, 
                        COUNT(*) as total_ingresos,
                        AVG(EXTRACT(EPOCH FROM (fecha_atencion_medica - fecha_entrada))/60) as espera_media_min
                    FROM urgencias 
                    WHERE {time_filter} 
                    GROUP BY DATE(fecha_entrada) 
                    ORDER BY fecha""",
                    "Ocupación y Espera en Urgencias",
                    "fecha",
                    "total_ingresos"
                ),
                "triaje": (
                    f"""SELECT triaje_nivel, COUNT(*) as cantidad 
                    FROM urgencias 
                    WHERE {time_filter} 
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
                    WHERE {time_filter} 
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
                    WHERE estado = 'COMPLETADA' AND {time_filter.replace('fecha_entrada', 'fecha_programada')}
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
                    WHERE {time_filter.replace('fecha_entrada', 'fecha_programada')}
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
                    WHERE {time_filter.replace('fecha_entrada', 'fecha_cita')}
                    GROUP BY estado""",
                    "Estado de Consultas Externas",
                    "estado",
                    "cantidad"
                ),
                "especialidad": (
                    f"""SELECT especialidad, COUNT(*) as total_citas
                    FROM consultas_externas 
                    WHERE estado = 'ATENDIDA' AND {time_filter.replace('fecha_entrada', 'fecha_cita')}
                    GROUP BY especialidad 
                    ORDER BY total_citas DESC""",
                    "Consultas por Especialidad",
                    "especialidad",
                    "total_citas"
                ),
            },
        }
        
        # Buscar patrón en la query
        query_lower = query.lower()
        area_queries = queries.get(area, {})
        
        for pattern, (sql, title, x, y) in area_queries.items():
            if pattern in query_lower:
                return sql, title, x, y
        
        # Query default para el área
        sql, title, x, y = area_queries.get("ocupación", area_queries.get("no_show", area_queries.get("utilización", ("SELECT 1", "Sin datos", "x", "y"))))
        return sql, title, x, y

# Instancia singleton
generator = AIGraphGenerator()

async def generate_chart_from_query(query: str) -> ChartConfiguration:
    """Función de conveniencia"""
    return await generator.generate_chart_config(query)
