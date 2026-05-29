# Hospital Dashboard AI - Guía de Uso

## 🚀 Inicio Rápido

### 1. Desplegar con Docker Compose

```bash
cd hospital-dashboard-ai-poc/docker
docker-compose up -d
```

### 2. Acceder a los Servicios

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Dashboard** | http://localhost:8501 | Interfaz Streamlit con chat IA |
| **API** | http://localhost:8000 | Documentación Swagger UI |
| **Admin DB** | http://localhost:8080 | Gestor de PostgreSQL |

---

## 💬 Uso del Chat IA

### Ejemplos de Preguntas

| Área | Pregunta | Resultado Esperado |
|------|----------|-------------------|
| **Urgencias** | "Muéstrame la ocupación de urgencias esta semana" | Gráfico de línea con ingresos diarios |
| **Urgencias** | "Distribución de pacientes por nivel de triaje" | Gráfico de barras o pie |
| **Quirófanos** | "Cirugías canceladas por motivo hoy" | Gráfico de barras agrupado |
| **Consultas** | "Especialidades con mayor tasa de no-show" | Ranking de especialidades |
| **Global** | "Evolución mensual de ingresos hospitalarios" | Tendencia anual |

### Patrones que Funcionan Bien

✅ **Funciona:**
- "Ocupación de [área] en [período]"
- "Comparar [métrica] por [dimensión]"
- "Evolución/tendencia de [dato]"
- "Distribución de [categoría]"

⚠️ **Mejorar especificidad:**
- "Gráfico de urgencias" → "Ocupación de urgencias por día"
- "Datos de cirugías" → "Tasa de completitud de cirugías"

---

## 🎨 Tipos de Gráficos Soportados

| Tipo | Mejor para | Ejemplo |
|------|-----------|---------|
| **Línea** | Evolución temporal | Ingresos diarios |
| **Barras** | Comparaciones | Cancelaciones por motivo |
| **Pie** | Distribución porcentual | Triaje |
| **Área** | Tendencias acumuladas | Ocupación acumulada |
| **Gauge** | Indicador único | % Ocupación UCI |
| **Tabla** | Detalle individual | Lista de pacientes |

---

## 📊 Métricas en Tiempo Real

El dashboard superior muestra:

- 🏥 **Urgencias Hoy**
- ⏱️ **Espera Media** (minutos)
- 🔪 **Cirugías Programadas** / Completadas
- 📋 **Consultas Atendidas** / No-show
- 🛏️ **Ocupación de Camas** (%)

---

## 🔧 Configuración Avanzada

### Variables de Entorno

Crear archivo `.env` en carpeta `docker/`:

```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxx

# Opcional: Modelo preferido
AI_MODEL=deepseek/deepseek-chat

# Base de datos personalizada
DATABASE_URL=postgresql://user:pass@host:5432/db

# Configuración Redis
REDIS_URL=redis://localhost:6379/0
```

### Sin Conexión Externa (Modo Fallback)

Si no tienes API key de OpenRouter, el sistema funciona automáticamente en **modo fallback** con generación basada en reglas que no requiere conexión externa.

---

## 🔒 Seguridad On-Premise

### Consideraciones Importantes:

1. **Todo se ejecuta localmente** - Sin datos en la nube
2. **Base de datos PostgreSQL** - En contenedor propio
3. **Red de Docker aislada** - Solo accesible desde el host
4. **Volumen persistente** - Datos guardados en `postgres_data`

### Acceso Remoto (opcional):

Si necesitas acceso externo, configura un reverse proxy con Nginx:

```nginx
server {
    listen 80;
    server_name dashboard.hospital.local;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }
}
```

---

## 🐛 Troubleshooting

### Error: "No se puede conectar al backend"

```bash
# Verificar contenedores
docker-compose ps

# Ver logs
docker-compose logs backend

# Reiniciar
docker-compose restart
```

### Error: "Base de datos vacía"

```bash
# Regenerar datos
cd database && python3 generate_data.py

# Recargar en DB
docker cp seed_data.sql hospital-dashboard-db:/tmp/
docker exec hospital-dashboard-db psql -U hospital -d hospital -f /tmp/seed_data.sql
```

### Error: "IA no responde"

- Verifica `OPENROUTER_API_KEY` en `.env`
- El sistema usará **fallback automáticamente**
- No es necesario para funcionar

---

## 📁 Estructura del Proyecto

```
hospital-dashboard-ai-poc/
├── backend/           # FastAPI + IA
│   ├── main.py
│   ├── ai_generator.py
│   └── models.py
├── frontend/          # Streamlit
│   ├── app.py
│   └── requirements.txt
├── database/          # PostgreSQL
│   ├── schema.sql
│   └── generate_data.py
├── docker/            # Docker Compose
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
└── docs/              # Documentación
    └── USAGE.md
```

---

## 📞 Soporte

Para problemas o mejoras:
1. Revisar logs: `docker-compose logs -f`
2. Verificar estado: `docker-compose ps`
3. Consultar documentación de FastAPI: http://localhost:8000/docs
