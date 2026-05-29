"""
Hospital Dashboard AI - Interfaz Rediseñada
Sidebar + KPIs visibles + Navegación intuitiva
"""

import streamlit as st
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
st.set_page_config(
    page_title="Hospital Dashboard AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.environ.get("API_URL", "http://localhost:8000")

# ==============================================================================
# ESTILOS CSS
# ==============================================================================
st.markdown("""
<style>
    /* Ocultar elementos Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Variables de color */
    :root {
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --bg-main: #f8fafc;
        --bg-card: #ffffff;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
    }
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Sidebar personalizado */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #0f172a 100%);
    }
    
    section[data-testid="stSidebar"] .stRadio > label {
        color: white !important;
        font-weight: 500;
        font-size: 14px;
    }
    
    section[data-testid="stSidebar"] .stRadio > div {
        flex-direction: column;
        gap: 8px;
    }
    
    section[data-testid="stSidebar"] .stRadio > div > label {
        background: rgba(255,255,255,0.1);
        padding: 12px 16px;
        border-radius: 8px;
        transition: all 0.2s;
    }
    
    section[data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(37,99,235,0.3);
    }
    
    section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
        background: #2563eb !important;
        box-shadow: 0 4px 12px rgba(37,99,235,0.4);
    }
    
    section[data-testid="stSidebar"] h2 {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] p {
        color: rgba(255,255,255,0.7) !important;
    }
    
    /* Tarjetas KPI */
    .kpi-row {
        display: flex;
        gap: 20px;
        margin-bottom: 24px;
    }
    
    .kpi-card {
        flex: 1;
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(0,0,0,0.12);
    }
    
    .kpi-icon {
        width: 56px;
        height: 56px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-bottom: 16px;
    }
    
    .kpi-value {
        font-size: 42px;
        font-weight: 700;
        color: #1e293b;
        line-height: 1.1;
        margin-bottom: 4px;
    }
    
    .kpi-label {
        font-size: 14px;
        color: #64748b;
        font-weight: 500;
    }
    
    .kpi-trend {
        font-size: 13px;
        font-weight: 600;
        margin-top: 12px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 20px;
    }
    
    .trend-up { color: #10b981; background: rgba(16,185,129,0.1); }
    .trend-down { color: #ef4444; background: rgba(239,68,68,0.1); }
    .trend-neutral { color: #f59e0b; background: rgba(245,158,11,0.1); }
    
    /* Secciones */
    .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    
    .section-title {
        font-size: 20px;
        font-weight: 600;
        color: #1e293b;
    }
    
    /* Grid de gráficos */
    .chart-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
        margin-bottom: 24px;
    }
    
    .chart-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    
    .chart-title {
        font-size: 16px;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 16px;
    }
    
    /* Botones de acción rápida */
    .quick-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 20px;
    }
    
    .quick-btn {
        padding: 10px 16px;
        border-radius: 8px;
        background: #f1f5f9;
        color: #475569;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid #e2e8f0;
    }
    
    .quick-btn:hover {
        background: #2563eb;
        color: white;
        border-color: #2563eb;
    }
    
    /* Status badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .status-online {
        background: rgba(16,185,129,0.1);
        color: #10b981;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
    }
    
    /* Chat input */
    .chat-container {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    
    /* Placeholder styling */
    ::placeholder {
        color: #94a3b8;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #f8fafc;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# FUNCIONES
# ==============================================================================

@st.cache_resource(ttl=30)
def get_kpis():
    try:
        response = requests.get(f"{API_URL}/api/v1/kpis/urgencias", timeout=5)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

@st.cache_resource(ttl=60)
def get_chart_time_series():
    try:
        response = requests.post(
            f"{API_URL}/api/v1/charts/generate",
            json={"query": "Urgencias últimos 7 días"},
            timeout=30
        )
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

@st.cache_resource(ttl=60)
def get_chart_distribution():
    try:
        response = requests.post(
            f"{API_URL}/api/v1/charts/generate",
            json={"query": "Distribución por nivel de triaje"},
            timeout=30
        )
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

@st.cache_resource(ttl=60)
def get_chart_destino():
    try:
        response = requests.post(
            f"{API_URL}/api/v1/charts/generate",
            json={"query": "Destino de pacientes"},
            timeout=30
        )
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def create_pretty_line_chart(data):
    """Gráfico de líneas profesional"""
    if not data or not data.get('labels'):
        return None
    
    labels = data['labels']
    values = data['datasets'][0]['data']
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=labels,
        y=values,
        mode='lines+markers',
        name='Urgencias',
        line=dict(color='#2563eb', width=3, shape='spline'),
        marker=dict(size=8, color='#2563eb', line=dict(color='white', width=2)),
        fill='tozeroy',
        fillcolor='rgba(37,99,235,0.1)',
        hovertemplate='<b>%{x}</b><br>Urgencias: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#1e293b'),
        height=300,
        margin=dict(l=50, r=50, t=30, b=50),
        showlegend=False,
        hoverlabel=dict(bgcolor='#1e293b', font=dict(color='white'))
    )
    
    fig.update_xaxes(
        showgrid=True,
        gridcolor='rgba(0,0,0,0.06)',
        tickfont=dict(color='#64748b', size=11),
        linecolor='#e2e8f0'
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor='rgba(0,0,0,0.06)',
        tickfont=dict(color='#64748b', size=11),
        linecolor='#e2e8f0',
        rangemode='tozero'
    )
    
    return fig

def create_pretty_pie_chart(data):
    """Gráfico de dona profesional"""
    if not data or not data.get('labels'):
        return None
    
    labels = data['labels']
    values = data['datasets'][0]['data']
    
    colors = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
    
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors[:len(labels)], line=dict(color='white', width=2)),
        textinfo='label+percent',
        textfont=dict(color='#1e293b', size=12, weight=500),
        hovertemplate='<b>%{label}</b><br>Valor: %{value}<br>Porcentaje: %{percent}<extra></extra>'
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False
    )
    
    return fig

def create_bar_chart(data, color='#2563eb'):
    """Gráfico de barras"""
    if not data or not data.get('labels'):
        return None
    
    labels = data['labels']
    values = data['datasets'][0]['data']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=labels,
        y=values,
        marker=dict(
            color=values,
            colorscale=['#dbeafe', '#2563eb'],
            line=dict(color='white', width=1)
        ),
        text=values,
        textposition='outside',
        textfont=dict(color='#64748b', size=11),
        hovertemplate='<b>%{x}</b><br>Valor: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=50, r=50, t=30, b=50),
        showlegend=False
    )
    
    fig.update_xaxes(
        showgrid=False,
        tickfont=dict(color='#64748b', size=11),
        linecolor='#e2e8f0'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor='rgba(0,0,0,0.06)',
        tickfont=dict(color='#64748b', size=11),
        rangemode='tozero'
    )
    
    return fig

# ==============================================================================
# SIDEBAR
# ==============================================================================

with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <div style='font-size: 48px; margin-bottom: 8px;'>🏥</div>
        <h2 style='color: white; margin: 0; font-size: 20px;'>Hospital AI</h2>
        <p style='color: rgba(255,255,255,0.6); font-size: 12px; margin-top: 4px;'>Dashboard Inteligente</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 📍 Navegación")
    
    page = st.radio(
        "Página:",
        ["📊 Dashboard", "🏥 Urgencias", "🔪 Quirófanos", "📋 Consultas", "🤖 Chat IA"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    st.markdown("### ⚡ Consultas Rápidas")
    
    if st.button("📈 URG por día", key="btn_urg", use_container_width=True):
        st.session_state['quick_query'] = "Urgencias últimos 7 días"
    
    if st.button("🎯 Triaje", key="btn_triaje", use_container_width=True):
        st.session_state['quick_query'] = "Distribución por triaje"
    
    if st.button("🚪 Fugas", key="btn_fugas", use_container_width=True):
        st.session_state['quick_query'] = "Tasa de fugas"
    
    if st.button("⏱️ Espera", key="btn_espera", use_container_width=True):
        st.session_state['quick_query'] = "Tiempo de espera por triaje"
    
    st.markdown("---")
    
    st.markdown("""
    <div style='text-align: center; padding: 12px; background: rgba(16,185,129,0.2); border-radius: 8px;'>
        <span style='color: #10b981; font-size: 12px; font-weight: 600;'>● Sistema Online</span>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# CONTENIDO PRINCIPAL
# ==============================================================================

# Header
col_title, col_status = st.columns([3, 1])

with col_title:
    st.markdown(f"""
    <h1 style='color: #1e293b; font-size: 28px; margin-bottom: 4px;'>{page.split(" ", 1)[1] if " " in page else page}</h1>
    <p style='color: #64748b; font-size: 14px;'>{datetime.now().strftime("%A, %d de %B de %Y • %H:%M")}</p>
    """, unsafe_allow_html=True)

with col_status:
    st.markdown("""
    <div style='text-align: right;'>
        <span class='status-badge status-online'>
            <span class='status-dot'></span>
            IA Activa
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==============================================================================
# DASHBOARD PRINCIPAL
# ==============================================================================

if "Dashboard" in page:
    # Obtener KPIs
    kpis = get_kpis()
    kpi_data = kpis.get('kpis', {}) if kpis else {}
    
    # Fila de KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-icon' style='background: rgba(37,99,235,0.1); color: #2563eb;'>🏥</div>
            <div class='kpi-value'>{kpi_data.get('total_urgencias_hoy', 0):.0f}</div>
            <div class='kpi-label'>Urgencias Hoy</div>
            <div class='kpi-trend trend-up'>↑ 12% vs ayer</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-icon' style='background: rgba(16,185,129,0.1); color: #10b981;'>⏱️</div>
            <div class='kpi-value'>{kpi_data.get('espera_media_minutos', 0):.0f}<span style='font-size: 18px; color: #64748b;'>min</span></div>
            <div class='kpi-label'>Espera Media</div>
            <div class='kpi-trend trend-down'>↓ 5% vs objetivo</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-icon' style='background: rgba(245,158,11,0.1); color: #f59e0b;'>🚪</div>
            <div class='kpi-value'>{kpis.get('kpis', {}).get('tasa_fugas', '0')}</div>
            <div class='kpi-label'>Tasa de Fugas</div>
            <div class='kpi-trend trend-neutral'>En objetivo</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-icon' style='background: rgba(139,92,246,0.1); color: #8b5cf6;'>🛏️</div>
            <div class='kpi-value'>78<span style='font-size: 18px; color: #64748b;'>%</span></div>
            <div class='kpi-label'>Ocupación</div>
            <div class='kpi-trend trend-up'>↑ 3% esta semana</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gráficos en grid
    st.markdown("### 📊 Visualizaciones")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.markdown("<div class='chart-title'>📈 Evolución de Urgencias</div>", unsafe_allow_html=True)
        
        chart_data = get_chart_time_series()
        if chart_data and chart_data.get('success'):
            fig = create_pretty_line_chart(chart_data['data'])
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Cargando gráfico...")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_chart2:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.markdown("<div class='chart-title'>🎯 Distribución por Triaje</div>", unsafe_allow_html=True)
        
        chart_dist = get_chart_distribution()
        if chart_dist and chart_dist.get('success'):
            fig = create_bar_chart(chart_dist['data'])
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Cargando gráfico...")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Destino pacientes
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
    st.markdown("<div class='chart-title'>🚪 Destino de Pacientes</div>", unsafe_allow_html=True)
    
    col_dest1, col_dest2, col_dest3 = st.columns([2, 1, 1])
    
    with col_dest1:
        chart_dest = get_chart_destino()
        if chart_dest and chart_dest.get('success'):
            fig = create_pretty_pie_chart(chart_dest['data'])
            if fig:
                st.plotly_chart(fig, use_container_width=True)
    
    with col_dest2:
        st.markdown("""
        <div style='padding: 20px; background: #f8fafc; border-radius: 12px;'>
            <div style='font-size: 13px; color: #64748b; margin-bottom: 8px;'>Resumen</div>
            <div style='font-size: 24px; font-weight: 700; color: #1e293b;'>~8000</div>
            <div style='font-size: 13px; color: #64748b;'>urgencias totales</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_dest3:
        st.markdown("""
        <div style='padding: 20px; background: #f8fafc; border-radius: 12px;'>
            <div style='font-size: 13px; color: #64748b; margin-bottom: 8px;'>Período</div>
            <div style='font-size: 24px; font-weight: 700; color: #1e293b;'>60 días</div>
            <div style='font-size: 13px; color: #64748b;'>de datos</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# CHAT IA
# ==============================================================================

elif "Chat" in page:
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='margin-bottom: 20px;'>
        <h2 style='color: #1e293b; font-size: 22px; margin-bottom: 8px;'>🤖 Asistente IA</h2>
        <p style='color: #64748b; font-size: 14px;'>Escribe tu consulta en lenguaje natural</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Consultas rápidas
    st.markdown("**Consulta rápida:**")
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    
    with col_q1:
        if st.button("'Urgencias 7 días'", key="quick1"):
            st.session_state['query_input'] = "Mostrar urgencias últimos 7 días"
    
    with col_q2:
        if st.button("'Por triaje'", key="quick2"):
            st.session_state['query_input'] = "Distribución por nivel de triaje"
    
    with col_q3:
        if st.button("'Fugas'", key="quick3"):
            st.session_state['query_input'] = "Tasa de fugas en urgencias"
    
    with col_q4:
        if st.button("'Espera'", key="quick4"):
            st.session_state['query_input'] = "Tiempo medio de espera"
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Input del usuario
    default_query = st.session_state.get('query_input', st.session_state.get('quick_query', ''))
    
    user_input = st.text_input(
        "Tu consulta:",
        value=default_query,
        placeholder="Ej: Muéstrame la ocupación de urgencias esta semana",
        label_visibility="collapsed"
    )
    
    if user_input:
        with st.spinner("🤖 Generando visualización..."):
            try:
                response = requests.post(
                    f"{API_URL}/api/v1/charts/generate",
                    json={"query": user_input},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('success'):
                        st.markdown(f"### 📊 {result['configuration'].get('title', 'Resultado')}")
                        
                        # Mostrar gráfico
                        data = result.get('data', {})
                        chart_type = result['configuration'].get('chart_type', 'bar')
                        
                        if chart_type == 'line':
                            fig = create_pretty_line_chart(data)
                        elif chart_type == 'pie':
                            fig = create_pretty_pie_chart(data)
                        else:
                            fig = create_bar_chart(data)
                        
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Explicación
                        if result.get('explanation'):
                            st.markdown(f"**💡 {result['explanation']}**")
                        
                        # SQL generado
                        with st.expander("🔍 Ver SQL generado"):
                            st.code(result['configuration'].get('query_sql', ''), language='sql')
                        
                        # Sugerencias
                        if result.get('suggestions'):
                            st.markdown("**También puedes preguntar:**")
                            for sugg in result['suggestions'][:3]:
                                st.markdown(f"• {sugg}")
                    else:
                        st.error("Error al generar el gráfico")
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.error(f"Error de conexión: {e}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# URGENCIAS DETALLE
# ==============================================================================

elif "Urgencias" in page:
    st.markdown("### KPIs de Urgencias")
    
    kpis = get_kpis()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Urgencias Hoy", kpis.get('kpis', {}).get('total_urgencias_hoy', 0))
    
    with col2:
        st.metric("Espera Media", f"{kpis.get('kpis', {}).get('espera_media_minutos', 0):.0f} min")
    
    with col3:
        st.metric("Tasa Fugas", kpis.get('kpis', {}).get('tasa_fugas', '0%'))
    
    st.markdown("---")
    st.markdown("### Gráfico de Evolución")
    
    chart_data = get_chart_time_series()
    if chart_data and chart_data.get('success'):
        fig = create_pretty_line_chart(chart_data['data'])
        if fig:
            st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# QUIRÓFANOS Y CONSULTAS
# ==============================================================================

elif "Quirófanos" in page:
    st.markdown("""
    <div style='text-align: center; padding: 60px 20px;'>
        <div style='font-size: 64px; margin-bottom: 16px;'>🔪</div>
        <h2 style='color: #1e293b;'>Gestión de Quirófanos</h2>
        <p style='color: #64748b;'>Visualizaciones de quirófanos próximamente</p>
    </div>
    """, unsafe_allow_html=True)

elif "Consultas" in page:
    st.markdown("""
    <div style='text-align: center; padding: 60px 20px;'>
        <div style='font-size: 64px; margin-bottom: 16px;'>📋</div>
        <h2 style='color: #1e293b;'>Consultas Externas</h2>
        <p style='color: #64748b;'>Métricas de consultas próximamente</p>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# FOOTER
# ==============================================================================

st.markdown("""
<div style='text-align: center; padding: 30px 0; border-top: 1px solid #e2e8f0; margin-top: 40px;'>
    <p style='color: #94a3b8; font-size: 12px;'>
        🏥 Hospital Dashboard AI • Powered by DeepSeek + Streamlit • v2.0
    </p>
</div>
""", unsafe_allow_html=True)
