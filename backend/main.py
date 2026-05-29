"""
Backend FastAPI para Hospital Dashboard con IA
API REST para generar gráficos, KPIs y métricas en tiempo real
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from db_connector import db_client, DB_ENGINE
from ai_generator import generate_chart_from_query, generator
from models import (
    NaturalLanguageRequest, AIChartResponse, ChartConfiguration, 
    ChartData, ChartType, Area, TimeRange,
    KPIRequest, KPIResponse, DashboardMetrics
)

# Conexión a base de datos (se mantiene para compatibilidad de firmas)
async def get_db():
    """Obtiene el cliente de base de datos unificado"""
    yield db_client

# Lifespan para startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de inicio y cierre"""
    print("🚀 Iniciando Hospital Dashboard AI API...")
    yield
    print("👋 Cerrando conexiones...")

# Crear app FastAPI
app = FastAPI(
    title="Hospital Dashboard AI API",
    description="API para generar dashboards hospitalarios con integración de IA",
    version="1.0.0",
    lifespan=lifespan
)

# CORS para permitir conexión desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# ENDPOINTS PRINCIPALES
# =============================================================================

@app.get("/")
async def root():
    """Endpoint de verificación"""
    return {
        "status": "online",
        "service": "Hospital Dashboard AI",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "generate_chart": "/api/v1/charts/generate",
            "kpis": "/api/v1/kpis/{area}",
            "metrics": "/api/v1/metrics/realtime"
        }
    }

@app.get("/health")
async def health_check():
    """Verificación de salud del servicio"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/v1/config")
async def get_config():
    """Obtiene configuraciones activas del backend"""
    return {
        "db_engine": DB_ENGINE
    }

# =============================================================================
# GENERACIÓN DE GRÁFICOS CON IA
# =============================================================================

@app.post("/api/v1/charts/generate", response_model=AIChartResponse)
async def generate_chart(request: NaturalLanguageRequest):
    """
    Genera un gráfico desde descripción en lenguaje natural.
    
    Ejemplo de uso:
    {
        "query": "Muéstrame la ocupación de urgencias esta semana",
        "user_id": "medico_001"
    }
    """
    try:
        # Generar configuración con IA o fallback
        config = await generate_chart_from_query(request.query)
        
        # Ejecutar la consulta SQL para obtener datos reales
        rows = await db_client.execute_query(config.query_sql)
        
        # Transformar a formato de ChartData
        labels = [str(row[config.x_axis or list(row.keys())[0]]) for row in rows] if rows else []
        datasets = []
        
        if rows:
            if config.y_axis:
                values = [row[config.y_axis] for row in rows]
                datasets.append({
                    "label": config.y_axis,
                    "data": values,
                    "backgroundColor": "rgba(54, 162, 235, 0.5)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 2
                })
            else:
                # Si no hay y_axis específico, usar todas las columnas numéricas
                for key in rows[0].keys():
                    if isinstance(rows[0][key], (int, float)) and key != config.x_axis:
                        values = [row[key] for row in rows]
                        datasets.append({
                            "label": key,
                            "data": values,
                            "backgroundColor": f"rgba({random.randint(50, 200)}, {random.randint(50, 200)}, {random.randint(50, 200)}, 0.5)",
                            "borderWidth": 1
                        })
        
        chart_data = ChartData(
            labels=labels,
            datasets=datasets,
            metadata={
                "total_rows": len(rows),
                "sql_executed": config.query_sql,
                "execution_time_ms": 0  # Se podría medir
            }
        )
        
        # Generar explicación
        explanation = f"""
        Este gráfico muestra {config.title.lower()}.
        Datos obtenidos de la tabla de {config.area.value}.
        El análisis cubre el período: {config.time_range.value}.
        """
        
        # Sugerencias relacionadas
        suggestions = generate_suggestions(config.area, request.query)
        
        return AIChartResponse(
            success=True,
            configuration=config,
            data=chart_data,
            explanation=explanation.strip(),
            confidence_score=0.85 if config.query_sql != "SELECT 1" else 0.6,
            suggestions=suggestions
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando gráfico: {str(e)}")

@app.post("/api/v1/charts/execute")
async def execute_sql(config: ChartConfiguration):
    """
    Ejecuta una consulta SQL personalizada y devuelve datos para el gráfico.
    """
    try:
        rows = await db_client.execute_query(config.query_sql)
        return {
            "success": True,
            "data": rows,
            "row_count": len(rows)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en SQL: {str(e)}")

# =============================================================================
# KPIs Y MÉTRICAS
# =============================================================================

@app.get("/api/v1/kpis/{area}", response_model=KPIResponse)
async def get_kpis(
    area: Area,
    time_range: TimeRange = Query(default=TimeRange.TODAY),
    conn=Depends(get_db)
):
    """
    Obtiene KPIs específicos para un área hospitalaria.
    """
    try:
        kpis = {}
        
        if area == Area.URGENCIAS:
            if DB_ENGINE == "mssql":
                query = """
                    SELECT COUNT(*) as total,
                           AVG(DATEDIFF(minute, fecha_entrada, fecha_atencion_medica)) as espera_media,
                           COUNT(CASE WHEN destino = 'FUGA' THEN 1 END) as fugas
                    FROM urgencias 
                    WHERE CAST(fecha_entrada AS DATE) = CAST(GETDATE() AS DATE)
                """
            elif DB_ENGINE == "oracle":
                query = """
                    SELECT COUNT(*) as total,
                           AVG((fecha_atencion_medica - fecha_entrada)*24*60) as espera_media,
                           COUNT(CASE WHEN destino = 'FUGA' THEN 1 END) as fugas
                    FROM urgencias 
                    WHERE TRUNC(fecha_entrada) = TRUNC(SYSDATE)
                """
            else:  # postgres
                query = """
                    SELECT COUNT(*) as total,
                           AVG(EXTRACT(EPOCH FROM (fecha_atencion_medica - fecha_entrada))/60) as espera_media,
                           COUNT(CASE WHEN destino = 'FUGA' THEN 1 END) as fugas
                    FROM urgencias 
                    WHERE DATE(fecha_entrada) = CURRENT_DATE
                """
            
            rows = await conn.execute_query(query)
            if rows:
                row = rows[0]
                kpis = {
                    "total_urgencias_hoy": row['total'] or 0,
                    "espera_media_minutos": round(row['espera_media'] or 0, 1),
                    "tasa_fugas": f"{round((row['fugas'] / row['total'] * 100) if row['total'] and row['total'] > 0 else 0, 1)}%"
                }
                
        elif area == Area.QUIROFANOS:
            if DB_ENGINE == "mssql":
                query = """
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN estado = 'COMPLETADA' THEN 1 END) as completadas,
                           COUNT(CASE WHEN estado = 'CANCELADA' THEN 1 END) as canceladas
                    FROM cirugias 
                    WHERE fecha_programada = CAST(GETDATE() AS DATE)
                """
            elif DB_ENGINE == "oracle":
                query = """
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN estado = 'COMPLETADA' THEN 1 END) as completadas,
                           COUNT(CASE WHEN estado = 'CANCELADA' THEN 1 END) as canceladas
                    FROM cirugias 
                    WHERE TRUNC(fecha_programada) = TRUNC(SYSDATE)
                """
            else:  # postgres
                query = """
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN estado = 'COMPLETADA' THEN 1 END) as completadas,
                           COUNT(CASE WHEN estado = 'CANCELADA' THEN 1 END) as canceladas
                    FROM cirugias 
                    WHERE fecha_programada = CURRENT_DATE
                """
            
            rows = await conn.execute_query(query)
            if rows:
                row = rows[0]
                kpis = {
                    "cirugias_programadas_hoy": row['total'] or 0,
                    "cirugias_completadas": row['completadas'] or 0,
                    "cirugias_canceladas": row['canceladas'] or 0,
                    "tasa_completitud": f"{round((row['completadas'] / row['total'] * 100) if row['total'] and row['total'] > 0 else 0, 1)}%"
                }
                
        elif area == Area.CONSULTAS_EXTERNAS:
            if DB_ENGINE == "mssql":
                query = """
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN estado = 'ATENDIDA' THEN 1 END) as atendidas,
                           COUNT(CASE WHEN estado = 'NO_SHOW' THEN 1 END) as no_show
                    FROM consultas_externas 
                    WHERE CAST(fecha_cita AS DATE) = CAST(GETDATE() AS DATE)
                """
            elif DB_ENGINE == "oracle":
                query = """
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN estado = 'ATENDIDA' THEN 1 END) as atendidas,
                           COUNT(CASE WHEN estado = 'NO_SHOW' THEN 1 END) as no_show
                    FROM consultas_externas 
                    WHERE TRUNC(fecha_cita) = TRUNC(SYSDATE)
                """
            else:  # postgres
                query = """
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN estado = 'ATENDIDA' THEN 1 END) as atendidas,
                           COUNT(CASE WHEN estado = 'NO_SHOW' THEN 1 END) as no_show
                    FROM consultas_externas 
                    WHERE DATE(fecha_cita) = CURRENT_DATE
                """
            
            rows = await conn.execute_query(query)
            if rows:
                row = rows[0]
                kpis = {
                    "citas_programadas_hoy": row['total'] or 0,
                    "citas_atendidas": row['atendidas'] or 0,
                    "no_show": row['no_show'] or 0,
                    "tasa_asistencia": f"{round((row['atendidas'] / row['total'] * 100) if row['total'] and row['total'] > 0 else 0, 1)}%"
                }
        
        return KPIResponse(
            area=area,
            time_range=time_range,
            kpis=kpis,
            trends={},  # Calcular vs período anterior
            alertas=[]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/metrics/realtime")
async def get_realtime_metrics(conn=Depends(get_db)):
    """
    Métricas en tiempo real del hospital.
    """
    try:
        # Urgencias hoy
        if DB_ENGINE == "mssql":
            q_urgencias = """
                SELECT COUNT(*) as total,
                       AVG(DATEDIFF(minute, fecha_entrada, fecha_atencion_medica)) as espera
                FROM urgencias 
                WHERE CAST(fecha_entrada AS DATE) = CAST(GETDATE() AS DATE)
            """
        elif DB_ENGINE == "oracle":
            q_urgencias = """
                SELECT COUNT(*) as total,
                       AVG((fecha_atencion_medica - fecha_entrada)*24*60) as espera
                FROM urgencias 
                WHERE TRUNC(fecha_entrada) = TRUNC(SYSDATE)
            """
        else:  # postgres
            q_urgencias = """
                SELECT COUNT(*) as total,
                       AVG(EXTRACT(EPOCH FROM (fecha_atencion_medica - fecha_entrada))/60) as espera
                FROM urgencias 
                WHERE DATE(fecha_entrada) = CURRENT_DATE
            """
        
        # Cirugías hoy
        if DB_ENGINE == "mssql":
            q_cirugias = """
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN estado = 'COMPLETADA' THEN 1 END) as completadas
                FROM cirugias 
                WHERE fecha_programada = CAST(GETDATE() AS DATE)
            """
        elif DB_ENGINE == "oracle":
            q_cirugias = """
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN estado = 'COMPLETADA' THEN 1 END) as completadas
                FROM cirugias 
                WHERE TRUNC(fecha_programada) = TRUNC(SYSDATE)
            """
        else:  # postgres
            q_cirugias = """
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN estado = 'COMPLETADA' THEN 1 END) as completadas
                FROM cirugias 
                WHERE fecha_programada = CURRENT_DATE
            """
            
        # Consultas
        if DB_ENGINE == "mssql":
            q_consultas = """
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN estado = 'ATENDIDA' THEN 1 END) as atendidas,
                       COUNT(CASE WHEN estado = 'NO_SHOW' THEN 1 END) as no_show
                FROM consultas_externas 
                WHERE CAST(fecha_cita AS DATE) = CAST(GETDATE() AS DATE)
            """
        elif DB_ENGINE == "oracle":
            q_consultas = """
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN estado = 'ATENDIDA' THEN 1 END) as atendidas,
                       COUNT(CASE WHEN estado = 'NO_SHOW' THEN 1 END) as no_show
                FROM consultas_externas 
                WHERE TRUNC(fecha_cita) = TRUNC(SYSDATE)
            """
        else:  # postgres
            q_consultas = """
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN estado = 'ATENDIDA' THEN 1 END) as atendidas,
                       COUNT(CASE WHEN estado = 'NO_SHOW' THEN 1 END) as no_show
                FROM consultas_externas 
                WHERE DATE(fecha_cita) = CURRENT_DATE
            """
            
        # Ejecutar todas
        urgencias_rows = await conn.execute_query(q_urgencias)
        cirugias_rows = await conn.execute_query(q_cirugias)
        consultas_rows = await conn.execute_query(q_consultas)
        
        # Ocupación camas
        camas_rows = await conn.execute_query("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN estado = 'OCUPADA' THEN 1 END) as ocupadas
            FROM camas
        """)
        
        urgencias = urgencias_rows[0] if urgencias_rows else {'total': 0, 'espera': 0}
        cirugias = cirugias_rows[0] if cirugias_rows else {'total': 0, 'completadas': 0}
        consultas = consultas_rows[0] if consultas_rows else {'total': 0, 'atendidas': 0, 'no_show': 0}
        camas = camas_rows[0] if camas_rows else {'total': 0, 'ocupadas': 0}
        
        ocupacion_pct = round((camas['ocupadas'] / camas['total'] * 100) if camas['total'] and camas['total'] > 0 else 0, 1)
        
        return DashboardMetrics(
            timestamp=datetime.now(),
            ocupacion_urgencias=ocupacion_pct,
            espera_media_urgencias=int(urgencias['espera'] or 0),
            cirugias_programadas_hoy=cirugias['total'] or 0,
            cirugias_completadas_hoy=cirugias['completadas'] or 0,
            consultas_atendidas_hoy=consultas['atendidas'] or 0,
            consultas_no_show_hoy=consultas['no_show'] or 0,
            camas_ocupadas=camas['ocupadas'] or 0,
            camas_disponibles=(camas['total'] or 0) - (camas['ocupadas'] or 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# UTILIDADES
# =============================================================================

def generate_suggestions(area: Area, original_query: str) -> List[str]:
    """Genera sugerencias de gráficos relacionados"""
    suggestions = {
        Area.URGENCIAS: [
            "Comparar evolución de urgencias de esta semana vs la anterior",
            "Distribución por nivel de triaje",
            "Destino de pacientes (alta, ingreso, fuga)",
            "Tiempo medio de espera por box"
        ],
        Area.QUIROFANOS: [
            "Utilización de quirófanos por hora del día",
            "Cirugías canceladas por motivo",
            "Top cirujanos por volumen",
            "Duración media por tipo de cirugía"
        ],
        Area.CONSULTAS_EXTERNAS: [
            "Especialidades con mayor demanda",
            "Tasa de no-show por especialidad",
            "Tiempo de espera hasta primera cita",
            "Pacientes atendidos por médico"
        ]
    }
    return suggestions.get(area, [])

import random

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
