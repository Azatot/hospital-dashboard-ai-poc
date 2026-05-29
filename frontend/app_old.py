"""
Frontend Streamlit para Hospital Dashboard con IA
Interfaz de chat para generar gráficos mediante lenguaje natural
"""
import streamlit as st
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objects import Figure
import pandas as pd
from datetime import datetime, timedelta
import time
import os

# Configuración de la página
st.set_page_config(
    page_title="Hospital Dashboard AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL del backend
# En Docker Compose, el backend se llama "backend", no "localhost"
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
    }
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .chat-user {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .chat-assistant {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    .stButton>button {
        width: 100%;
    }
    .suggestion-btn {
        margin: 2px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def check_api_status():
    """Verifica si la API está disponible"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def create_chart(chart_config, chart_data):
    """Crea un gráfico Plotly basado en la configuración"""
    chart_type = chart_config.get('chart_type', 'line')
    
    # Validar datos
    if not chart_data or not chart_data.get('labels') or not chart_data.get('datasets'):
        st.warning("No hay datos para mostrar en el gráfico")
        return None
    
    labels = chart_data['labels']
    datasets = chart_data['datasets']
    
    if not datasets or len(datasets) == 0 or not datasets[0].get('data'):
        st.warning("Dataset vacío")
        return None
    
    # Convertir labels a fechas si parecen fechas
    try:
        import pandas as pd
        df = pd.DataFrame({
            'x': labels,
            'y': datasets[0]['data']
        })
    except Exception as e:
        st.error(f"Error creando DataFrame: {e}")
        return None
    
    if chart_type == 'line':
        fig = px.line(df, x='x', y='y', 
                     title=chart_config.get('title', 'Gráfico'),
                     labels={'x': chart_config.get('x_axis', ''), 
                            'y': chart_config.get('y_axis', '')})
    elif chart_type == 'bar':
        fig = px.bar(df, x='x', y='y',
                    title=chart_config.get('title', 'Gráfico'),
                    labels={'x': chart_config.get('x_axis', ''),
                           'y': chart_config.get('y_axis', '')},
                    color_discrete_sequence=['#1f77b4'])
    elif chart_type == 'pie':
        fig = px.pie(df, names='x', values='y',
                    title=chart_config.get('title', 'Gráfico'))
    elif chart_type == 'area':
        fig = px.area(df, x='x', y='y',
                     title=chart_config.get('title', 'Gráfico'),
                     labels={'x': chart_config.get('x_axis', ''),
                            'y': chart_config.get('y_axis', '')})
    elif chart_type == 'gauge':
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = df['y'].iloc[0] if len(df) > 0 else 0,
            title = {'text': chart_config.get('title', 'Indicador')},
            gauge = {'axis': {'range': [None, 100]},
                    'bar': {'color': "#1f77b4"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 75], 'color': "yellow"},
                        {'range': [75, 100], 'color': "red"}],
                    'threshold': {'line': {'color': "red", 'width': 4},
                                 'thickness': 0.75, 'value': 90}}
        ))
    else:
        fig = px.bar(df, x='x', y='y',
                    title=chart_config.get('title', 'Gráfico'))
    
    fig.update_layout(
        template='plotly_white',
        height=500,
        title_font_size=18,
        title_x=0.5,
        xaxis_title_font_size=14,
        yaxis_title_font_size=14
    )
    
    return fig

def get_realtime_metrics():
    """Obtiene métricas en tiempo real"""
    try:
        response = requests.get(f"{API_URL}/api/v1/metrics/realtime", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def generate_chart_from_prompt(prompt: str) -> dict:
    """Llama al backend para generar gráfico desde prompt"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/charts/generate",
            json={"query": prompt, "user_id": "streamlit_user"},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

# =============================================================================
# COMPONENTES UI
# =============================================================================

def render_header():
    """Renderiza el header principal"""
    st.markdown('<div class="main-header">🏥 Hospital Dashboard AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Genera visualizaciones en tiempo real usando lenguaje natural</div>',
        unsafe_allow_html=True
    )

def render_sidebar():
    """Renderiza la barra lateral con información y controles"""
    st.sidebar.title("⚙️ Configuración")
    
    # Estado de la API
    api_online = check_api_status()
    st.sidebar.markdown(f"**Estado API:** {'🟢 Online' if api_online else '🔴 Offline'}")
    
    st.sidebar.markdown("---")
    
    # Información del modelo
    st.sidebar.subheader("🤖 Modelo IA")
    st.sidebar.markdown("- **Proveedor:** OpenRouter")
    st.sidebar.markdown("- **Modelo:** deepseek/deepseek-chat")
    st.sidebar.markdown("- **Estado:** Local/Fallback disponible")
    
    st.sidebar.markdown("---")
    
    # Áreas disponibles
    st.sidebar.subheader("📊 Áreas Monitorizadas")
    areas = ["🏥 Urgencias", "🔪 Quirófanos", "📋 Consultas Externas", "🛏️ Camas"]
    for area in areas:
        st.sidebar.markdown(area)
    
    st.sidebar.markdown("---")
    
    # Ejemplos de prompts
    st.sidebar.subheader("💡 Ejemplos de Preguntas")
    examples = [
        "Ocupación de urgencias esta semana",
        "Cirugías canceladas por motivo",
        "Tasa de no-show en consultas",
        "Tiempo medio de espera por triaje",
        "Evolución de ingresos último mes",
    ]
    
    for i, example in enumerate(examples):
        if st.sidebar.button(f"📊 {example}", key=f"example_{i}", use_container_width=True):
            st.session_state.user_input = example
            st.rerun()

def render_metrics_dashboard():
    """Renderiza el dashboard de métricas en tiempo real"""
    st.subheader("📈 Métricas en Tiempo Real")
    
    metrics = get_realtime_metrics()
    
    if metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Urgencias Hoy",
                value=metrics.get('total_urgencias_hoy', 'N/A'),
                delta=None
            )
            st.metric(
                label="Espera Media (min)",
                value=f"{metrics.get('espera_media_urgencias', 0):.0f}"
            )
        
        with col2:
            st.metric(
                label="Cirugías Programadas",
                value=metrics.get('cirugias_programadas_hoy', 0)
            )
            st.metric(
                label="Cirugías Completadas",
                value=metrics.get('cirugias_completadas_hoy', 0)
            )
        
        with col3:
            st.metric(
                label="Consultas Atendidas",
                value=metrics.get('consultas_atendidas_hoy', 0)
            )
            st.metric(
                label="No-Show",
                value=metrics.get('consultas_no_show_hoy', 0)
            )
        
        with col4:
            st.metric(
                label="Ocupación Camas",
                value=f"{metrics.get('ocupacion_urgencias', 0)}%"
            )
            st.metric(
                label="Camas Disponibles",
                value=metrics.get('camas_disponibles', 0)
            )
    else:
        st.info("Conectando a datos en tiempo real...")

def render_chat_interface():
    """Renderiza la interfaz de chat para generar gráficos"""
    st.markdown("---")
    st.subheader("💬 Pregunta a la IA y genera gráficos")
    
    # Historial de chat
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Mostrar historial
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "chart" in message:
                st.plotly_chart(message["chart"], use_container_width=True)
    
    # Input del usuario
    user_input = st.chat_input("¿Qué gráfico necesitas? Ej: 'Muéstrame la ocupación de urgencias esta semana'")
    
    if user_input:
        # Agregar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner("🤖 Analizando y generando gráfico..."):
                response = generate_chart_from_prompt(user_input)
                st.write(f"DEBUG - Respuesta recibida: {response.get('success')}")
                st.write(f"DEBUG - Keys: {list(response.keys())}")
                
                if response.get('success'):
                    config = response['configuration']
                    data = response.get('data', {})
                    
                    # Mostrar explicación
                    st.markdown(f"**📊 {config['title']}**")
                    if config.get('subtitle'):
                        st.markdown(f"*{config['subtitle']}*")
                    
                    # Crear y mostrar gráfico
                    try:
                        st.info(f"Generando gráfico tipo: {config.get('chart_type', 'desconocido')}")
                        st.write(f"Datos recibidos: {len(data.get('labels', []))} etiquetas, {len(data.get('datasets', []))} datasets")
                        if data.get('datasets'):
                            st.write(f"Primer dataset: {len(data['datasets'][0].get('data', []))} valores")
                        fig = create_chart(config, data)
                        st.write(f"Figura creada: {fig is not None}")
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, key=f"chart_{len(st.session_state.messages)}")
                        else:
                            st.warning("El gráfico no se pudo generar")
                        
                        # Guardar en historial
                        st.session_state.messages[-1]["chart_config"] = config
                        st.session_state.messages[-1]["chart_data"] = data
                        
                        # Sugerencias
                        if response.get('suggestions'):
                            st.markdown("**💡 También podrías preguntar:**")
                            cols = st.columns(min(len(response['suggestions']), 3))
                            for i, suggestion in enumerate(response['suggestions'][:3]):
                                with cols[i]:
                                    if st.button(suggestion, key=f"sugg_{len(st.session_state.messages)}_{i}"):
                                        st.session_state.user_input = suggestion
                                        st.rerun()
                        
                        # Mostrar SQL (opcional, en expander)
                        with st.expander("🔍 Ver SQL generado"):
                            st.code(config['query_sql'], language='sql')
                            
                    except Exception as e:
                        st.error(f"Error creando gráfico: {e}")
                else:
                    st.error(f"Error: {response.get('error', 'Desconocido')}")

def render_quick_access():
    """Renderiza accesos rápidos a gráficos comunes"""
    st.markdown("---")
    st.subheader("⚡ Accesos Rápidos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🏥 Urgencias**")
        if st.button("Ocupación últimos 7 días", key="quick_urg_1"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Ocupación de urgencias últimos 7 días"
            })
            st.rerun()
        if st.button("Distribución triaje", key="quick_urg_2"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Distribución de urgencias por nivel de triaje"
            })
            st.rerun()
    
    with col2:
        st.markdown("**🔪 Quirófanos**")
        if st.button("Cirugías por tipo", key="quick_quir_1"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Cirugías por tipo"
            })
            st.rerun()
        if st.button("Tasa cancelaciones", key="quick_quir_2"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Tasa de cancelaciones de cirugías"
            })
            st.rerun()
    
    with col3:
        st.markdown("**📋 Consultas**")
        if st.button("No-show por especialidad", key="quick_cons_1"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Tasa de no-show por especialidad"
            })
            st.rerun()
        if st.button("Consultas atendidas", key="quick_cons_2"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Número de consultas atendidas hoy"
            })
            st.rerun()

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Función principal"""
    render_header()
    render_sidebar()
    
    # Layout principal - métricas y accesos rápidos
    col_main, col_right = st.columns([3, 1])
    
    with col_main:
        render_metrics_dashboard()
    
    with col_right:
        render_quick_access()
    
    # Chat interface FUERA de columnas (st.chat_input no puede estar dentro de st.columns)
    render_chat_interface()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Hospital Dashboard AI PoC | Generado con Streamlit + FastAPI</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
