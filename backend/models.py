"""
Modelos Pydantic para la API de Dashboard Hospitalario con IA
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    GAUGE = "gauge"
    HEATMAP = "heatmap"
    TABLE = "table"

class Area(str, Enum):
    URGENCIAS = "urgencias"
    QUIROFANOS = "quirofanos"
    CONSULTAS_EXTERNAS = "consultas_externas"
    CAMAS = "camas"
    GLOBAL = "global"

class TimeRange(str, Enum):
    TODAY = "hoy"
    YESTERDAY = "ayer"
    LAST_7_DAYS = "ultimos_7_dias"
    LAST_30_DAYS = "ultimos_30_dias"
    THIS_MONTH = "este_mes"
    LAST_MONTH = "mes_pasado"
    THIS_YEAR = "este_año"
    CUSTOM = "personalizado"

class NaturalLanguageRequest(BaseModel):
    """Request para generar gráfico desde lenguaje natural"""
    query: str = Field(..., description="Descripción en lenguaje natural del gráfico deseado")
    user_id: Optional[str] = Field(None, description="ID del usuario para personalización")
    area_preference: Optional[Area] = Field(None, description="Área preferida si se detecta")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Muéstrame la ocupación de urgencias esta semana por día",
                "user_id": "medico_001",
                "area_preference": "urgencias"
            }
        }

class ChartConfiguration(BaseModel):
    """Configuración generada por IA para el gráfico"""
    chart_type: ChartType
    title: str
    subtitle: Optional[str] = None
    area: Area
    query_sql: str
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    group_by: Optional[str] = None
    filters: Optional[Dict[str, Any]] = {}
    aggregations: Optional[Dict[str, str]] = {}
    color_scheme: Optional[str] = "hospital"
    time_range: Optional[TimeRange] = TimeRange.LAST_7_DAYS
    
    class Config:
        json_schema_extra = {
            "example": {
                "chart_type": "line",
                "title": "Ocupación de Urgencias",
                "subtitle": "Últimos 7 días",
                "area": "urgencias",
                "query_sql": "SELECT DATE(fecha_entrada) as dia, COUNT(*) as total FROM urgencias WHERE fecha_entrada >= NOW() - INTERVAL '7 days' GROUP BY DATE(fecha_entrada)",
                "x_axis": "dia",
                "y_axis": "total",
                "time_range": "ultimos_7_dias"
            }
        }

class ChartData(BaseModel):
    """Datos resultantes para el gráfico"""
    labels: List[str]
    datasets: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = {}

class AIChartResponse(BaseModel):
    """Respuesta completa del endpoint de generación IA"""
    success: bool
    configuration: ChartConfiguration
    data: Optional[ChartData] = None
    explanation: Optional[str] = None  # Explicación en lenguaje natural de lo que se muestra
    confidence_score: float = Field(..., ge=0, le=1, description="Confianza en la interpretación")
    suggestions: Optional[List[str]] = None  # Sugerencias de gráficos relacionados

class KPIRequest(BaseModel):
    """Request para obtener KPIs específicos"""
    area: Area
    time_range: TimeRange
    custom_start_date: Optional[datetime] = None
    custom_end_date: Optional[datetime] = None

class KPIResponse(BaseModel):
    """Respuesta de KPIs"""
    area: Area
    time_range: TimeRange
    kpis: Dict[str, Union[float, int, str]]
    trends: Optional[Dict[str, float]] = None  # Cambio porcentual vs período anterior
    alertas: Optional[List[str]] = None

class DashboardMetrics(BaseModel):
    """Métricas del dashboard en tiempo real"""
    timestamp: datetime
    ocupacion_urgencias: float  # porcentaje
    espera_media_urgencias: int  # minutos
    cirugias_programadas_hoy: int
    cirugias_completadas_hoy: int
    consultas_atendidas_hoy: int
    consultas_no_show_hoy: int
    camas_ocupadas: int
    camas_disponibles: int

class UserSession(BaseModel):
    """Sesión de usuario para personalización"""
    user_id: str
    role: str  # 'medico', 'enfermeria', 'gerencia', 'admin'
    preferred_areas: List[Area]
    recent_queries: List[str] = []
    saved_charts: List[str] = []
