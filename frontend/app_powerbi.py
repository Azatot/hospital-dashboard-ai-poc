"""
Hospital Dashboard AI - Estilo Power BI
Diseño moderno con tarjetas interactivas, KPIs y visualizaciones dinámicas
"""

import streamlit as st
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import os

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Hospital Dashboard AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

API_URL = os.environ.get("API_URL", "http://localhost:8000")

# ==============================================================================
# ESTILOS CSS - TEMA OSCURO MODERNO POWER BI
# ==============================================================================
st.markdown("""
<style>
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Variables CSS */
    :root {
        --bg-primary: #1a1a2e;
        --bg-secondary: #16213e;
        --bg-card: #0f3460;
        --accent-blue: #0078d4;
        --accent-green: #10b981;
        --accent-orange: #f59e0b;
        --accent-red: #ef4444;
        --accent-purple: #8b5cf6;
        --text-primary: #ffffff;
        --text-secondary: #94a3b8;
    }
    
    /* Fondo principal */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    /* Cards de KPIs */
    .kpi-card {
        background: linear-gradient(145deg, rgba(15, 52, 96, 0.8), rgba(22, 33, 62, 0.9));
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 120, 212, 0.3);
        border-color: rgba(0, 120, 212, 0.5);
    }
    
    .kpi-value {
        font-size: 42px;
        font-weight: 700;
        background: linear-gradient(135deg, #0078d4, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 8px 0;
    }
    
    .kpi-label {
        font-size: 14px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .kpi-delta {
        font-size: 14px;
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    
    .kpi-delta.positive {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    
    .kpi-delta.negative {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    
    /* Status badges */
    .status-badge {
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-online {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(90deg, #0078d4, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    
    .sub-header {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 0;
    }
    
    /* Chat container */
    .chat-container {
        background: rgba(15, 52, 96, 0.5);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Sidebar navigation */
    .nav-item {
        padding: 12px 20px;
        border-radius: 12px;
        margin: 4px 0;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .nav-item:hover {
        background: rgba(0, 120, 212, 0.2);
    }
    
    .nav-item.active {
        background: linear-gradient(90deg, rgba(0, 120, 212, 0.3), rgba(139, 92, 246, 0.3));
        border-left: 3px solid #0078d4;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0078d4, #8b5cf6);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 120, 212, 0.4);
    }
    
    /* Input */
    .stTextInput > div > div > input {
        background: rgba(15, 52, 96, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
        padding: 16px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #0078d4;
        box-shadow: 0 0 0 3px rgba(0, 120, 212, 0.3);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(15, 52, 96, 0.5);
        border-radius: 16px;
        padding: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 12px 24px;
        color: #94a3b8;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0078d4, #8b5cf6);
        color: white;
    }
    
    /* Animación de pulso */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    /* Spinner personalizado */
    .custom-spinner {
        width: 40px;
        height: 40px;
        border: 3px solid rgba(0, 120, 212, 0.3);
        border-top-color: #0078d4;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Charts container */
    .chart-container {
        background: rgba(15, 52, 96, 0.5);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Quick actions */
    .quick-action {
        background: rgba(0, 120, 212, 0.1);
        border: 1px solid rgba(0, 120, 212, 0.3);
        border-radius: 12px;
        padding: 16px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .quick-action:hover {
        background: rgba(0, 120, 212, 0.2);
        transform: translateX(5px);
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def get_kpis():
    """Obtiene KPIs de todas las áreas"""
    try:
        response = requests.get(f"{API_URL}/api/v1/kpis/urgencias", timeout=5)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def generate_chart(prompt):
    """Genera gráfico desde prompt"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/charts/generate",
            json={"query": prompt, "user_id": "powerbi_user"},
            timeout=30
        )
        return response.json() if response.status_code == 200 else None
    except:
        return None

def create_powerbi_chart(config, data):
    """Crea gráfico estilo Power BI"""
    if not data or not data.get('labels') or not data.get('datasets'):
        return None
    
    labels = data['labels']
    values = data['datasets'][0]['data']
    chart_type = config.get('chart_type', 'bar')
    
    # Colores estilo Power BI
    colors = ['#0078d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
    
    fig = go.Figure()
    
    if chart_type == 'line':
        fig.add_trace(go.Scatter(
            x=labels,
            y=values,
            mode='lines+markers',
            line=dict(color='#0078d4', width=3),
            marker=dict(size=10, color='#0078d4'),
            fill='tozeroy',
            fillcolor='rgba(0, 120, 212, 0.2)',
            name=config.get('y_axis', 'Valor')
        ))
    elif chart_type == 'bar':
        fig.add_trace(go.Bar(
            x=labels,
            y=values,
            marker=dict(
                color=values,
                colorscale='Blues',
                line=dict(color='rgba(0, 120, 212, 0.8)', width=1)
            ),
            text=values,
            textposition='outside',
            name=config.get('y_axis', 'Valor')
        ))
    elif chart_type == 'pie':
        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            hole=0.5,
            marker=dict(colors=colors[:len(labels)]),
            textinfo='label+percent',
            textposition='outside'
        ))
    else:
        fig.add_trace(go.Bar(x=labels, y=values))
    
    # Layout estilo Power BI
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Segoe UI'),
        title=dict(
            text=config.get('title', ''),
            font=dict(size=20, color='white'),
            x=0.5
        ),
        height=400,
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            title=config.get('x_axis', '')
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            title=config.get('y_axis', '')
        ),
        showlegend=False
    )
    
    return fig

def create_gauge(value, title, max_val=100, color='#0078d4'):
    """Crea un gauge/kPI circular"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={'text': title, 'font': {'color': 'white', 'size': 16}},
        gauge={
            'axis': {'range': [0, max_val], 'tickcolor': 'white'},
            'bar': {'color': color},
            'bgcolor': 'rgba(0,0,0,0.3)',
            'steps': [
                {'range': [0, max_val*0.5], 'color': 'rgba(255,255,255,0.05)'},
                {'range': [max_val*0.5, max_val*0.8], 'color': 'rgba(255,255,255,0.1)'},
                {'range': [max_val*0.8, max_val], 'color': 'rgba(255,255,255,0.15)'}
            ],
            'threshold': {
                'line': {'color': 'white', 'width': 2},
                'thickness': 0.75,
                'value': max_val * 0.7
            }
        },
        number={'font': {'color': 'white', 'size': 32}},
        delta={'reference': max_val * 0.8, 'font': {'color': '#10b981'}}
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        height=200,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    
    return fig

# ==============================================================================
# COMPONENTES UI
# ==============================================================================

def render_header():
    """Header principal"""
    col1, col2, col3 = st.columns([2, 3, 1])
    
    with col1:
        st.markdown("""
        <div style='display: flex; align-items: center; gap: 20px;'>
            <div style='font-size: 50px;'>🏥</div>
            <div>
                <h1 class='main-header'>Hospital Dashboard</h1>
                <p class='sub-header'>Inteligencia Artificial para Gestión Hospitalaria</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='text-align: right; padding: 20px;'>
            <span class='status-badge status-online'>🟢 Sistema Online</span>
            <br><br>
            <span style='color: #94a3b8; font-size: 12px;'>Actualizado: {}</span>
        </div>
        """.format(datetime.now().strftime("%H:%M:%S")), unsafe_allow_html=True)

def render_kpi_cards():
    """Tarjetas de KPIs principales"""
    kpis = get_kpis()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Urgencias hoy
    with col1:
        st.markdown("""
        <div class='kpi-card'>
            <div class='kpi-label'>🏥 Urgencias Hoy</div>
            <div class='kpi-value'>{}</div>
            <span class='kpi-delta positive'>↑ 12% vs ayer</span>
        </div>
        """.format(kpis.get('kpis', {}).get('total_urgencias_hoy', 0) if kpis else 0), unsafe_allow_html=True)
    
    # Espera media
    with col2:
        espera = kpis.get('kpis', {}).get('espera_media_minutos', 0) if kpis else 0
        st.markdown("""
        <div class='kpi-card'>
            <div class='kpi-label'>⏱️ Espera Media</div>
            <div class='kpi-value'>{:.0f} min</div>
            <span class='kpi-delta {}'>{} 5% vs objetivo</span>
        </div>
        """.format(espera, 'positive' if espera < 120 else 'negative', '↓' if espera < 120 else '↑'), unsafe_allow_html=True)
    
    # Tasa fugas
    with col3:
        fugas = kpis.get('kpis', {}).get('tasa_fugas', '0%') if kpis else '0%'
        st.markdown("""
        <div class='kpi-card'>
            <div class='kpi-label'>🚪 Tasa Fugas</div>
            <div class='kpi-value'>{}</div>
            <span class='kpi-delta positive'>↓ En objetivo</span>
        </div>
        """.format(fugas), unsafe_allow_html=True)
    
    # Cirugías
    with col4:
        st.markdown("""
        <div class='kpi-card'>
            <div class='kpi-label'>🔪 Cirugías Hoy</div>
            <div class='kpi-value'>23</div>
            <span class='kpi-delta positive'>✓ 87% completadas</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Camas
    with col5:
        st.markdown("""
        <div class='kpi-card'>
            <div class='kpi-label'>🛏️ Ocupación</div>
            <div class='kpi-value'>78%</div>
            <span class='kpi-delta negative'>↑ 3% vs ayer</span>
        </div>
        """, unsafe_allow_html=True)

def render_quick_charts():
    """Gráficos predefinidos"""
    st.markdown("### 📊 Visualizaciones")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏥 Urgencias", "🔪 Quirófanos", "📋 Consultas", "🛏️ Camas"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de ocupación
            result = generate_chart("Urgencias últimos 7 días")
            if result and result.get('success'):
                fig = create_powerbi_chart(result['configuration'], result['data'])
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gauge de ocupación
            fig_gauge = create_gauge(78, "Ocupación Actual", 100, '#10b981')
            st.plotly_chart(fig_gauge, use_container_width=True)
    
    with tab2:
        st.markdown("""
        <div style='text-align: center; padding: 50px; color: #94a3b8;'>
            <h3>🔧 Quirófanos</h3>
            <p>Datos de quirófanos disponibles</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown("""
        <div style='text-align: center; padding: 50px; color: #94a3b8;'>
            <h3>📋 Consultas Externas</h3>
            <p>Datos de consultas disponibles</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab4:
        st.markdown("""
        <div style='text-align: center; padding: 50px; color: #94a3b8;'>
            <h3>🛏️ Gestión de Camas</h3>
            <p>Datos de ocupación disponibles</p>
        </div>
        """, unsafe_allow_html=True)

def render_chat():
    """Interfaz de chat"""
    st.markdown("---")
    st.markdown("### 🤖 Asistente IA")
    
    # Quick actions
    st.markdown("**💡 Consultas rápidas:**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    quick_prompts = [
        ("📈 Ocupación urgencias", "Ocupación de urgencias últimos 7 días"),
        ("🎯 Triaje distribución", "Distribución por nivel de triaje"),
        ("🚪 Tasa fugas", "Tasa de fugas en urgencias"),
        ("⏱️ Tiempo espera", "Tiempo medio de espera por triaje")
    ]
    
    for i, (label, prompt) in enumerate(quick_prompts):
        with [col1, col2, col3, col4][i]:
            if st.button(label, key=f"quick_{i}"):
                st.session_state.chat_prompt = prompt
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Chat input
    user_input = st.text_input(
        "Escribe tu consulta...",
        value=st.session_state.get('chat_prompt', ''),
        key="chat_input",
        placeholder="Ej: Muéstrame la ocupación de urgencias esta semana"
    )
    
    if user_input:
        with st.spinner("🤖 Generando visualización..."):
            result = generate_chart(user_input)
            
            if result and result.get('success'):
                config = result['configuration']
                data = result['data']
                
                st.markdown(f"**📊 {config.get('title', 'Gráfico')}**")
                
                fig = create_powerbi_chart(config, data)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("🔍 Ver SQL generado"):
                    st.code(config.get('query_sql', ''), language='sql')
                
                if result.get('suggestions'):
                    st.markdown("**💡 Sugerencias:**")
                    for sugg in result['suggestions'][:3]:
                        st.markdown(f"• {sugg}")
            else:
                st.error("Error generando el gráfico")

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    render_header()
    st.markdown("<br>", unsafe_allow_html=True)
    render_kpi_cards()
    st.markdown("<br>", unsafe_allow_html=True)
    render_quick_charts()
    render_chat()
    
    # Footer
    st.markdown("""
    <div style='text-align: center; padding: 20px; color: #94a3b8; font-size: 12px;'>
        🏥 Hospital Dashboard AI PoC | Powered by Streamlit + FastAPI + DeepSeek
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
