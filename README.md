# 🏥 Hospital Dashboard AI

Sistema de cuadro de mandos hospitalario con **generación de gráficos mediante IA** y **lenguaje natural**. Diseñado para despliegue **100% on-premise** sin necesidad de subir datos a la nube.

---

## ✨ Características

### 🤖 Integración de IA
- **Chat natural** para generar gráficos
- Conversión de descripciones a SQL automáticamente
- Fallback basado en reglas si no hay API externa
- Sugerencias inteligentes de visualizaciones

### 📊 Áreas Cubiertas
| Área | Indicadores |
|------|-------------|
| 🏥 **Urgencias** | Ocupación, tiempos de espera, triaje, fugas |
| 🔪 **Quirófanos** | Utilización, cancelaciones, tipos de cirugía |
| 📋 **Consultas Externas** | No-show, especialidades, tiempos |
| 🛏️ **Camas** | Ocupación, disponibilidad, estancia media |

### 🏗️ Arquitectura On-Premise
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit     │────▶│   FastAPI       │────▶│   PostgreSQL    │
│   Frontend      │     │   Backend + IA  │     │   (datos)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        └───────────────────────────────────────────────┘
                    Todo dentro de tu red local
```

---

## 🚀 Instalación Rápida

### Requisitos
- Docker & Docker Compose
- 4GB RAM libre
- 10GB espacio en disco

### Paso 1: Clonar y Entrar
```bash
cd hospital-dashboard-ai-poc/docker
```

### Paso 2: Iniciar Servicios
```bash
# Primera vez (construye imágenes)
docker-compose up --build -d

# Siguientes veces
docker-compose up -d
```

### Paso 3: Verificar Estado
```bash
# Ver todos los servicios
docker-compose ps

# Ver logs
docker-compose logs -f
```

---

## 🖥️ Acceso

| Servicio | URL | Usuario | Contraseña |
|----------|-----|---------|------------|
| **Dashboard** | http://localhost:8501 | - | - |
| **API Docs** | http://localhost:8000/docs | - | - |
| **Admin DB** | http://localhost:8080 | hospital | hospital123 |

---

## 💬 Ejemplos de Uso

### Preguntas que Puedes Hacer

```
"Muéstrame la ocupación de urgencias esta semana"
→ Gráfico de línea con ingresos diarios

"Distribución de cirugías por tipo y estado"
→ Barras agrupadas por completadas/canceladas

"Especialidades con mayor tasa de no-show"
→ Ranking con porcentajes

"Evolución del tiempo medio de espera en urgencias"
→ Tendencia temporal
```

---

## 🔧 Configuración

### Opcional: Activar IA Avanzada (OpenRouter)

1. Obtener API key en [openrouter.ai](https://openrouter.ai)
2. Crear archivo `docker/.env`:

```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxx
```

3. Reiniciar:
```bash
docker-compose restart backend
```

> **Nota:** Sin API key, el sistema funciona perfectamente con generación basada en reglas.

---

## 📊 Capturas de Pantalla

### Dashboard Principal
- KPIs en tiempo real
- Accesos rápidos por área
- Chat con IA integrado

### Generación de Gráficos
1. Escribe tu pregunta
2. La IA analiza y genera SQL
3. Visualización automática
4. Sugerencias de gráficos relacionados

---

## 🛡️ Seguridad

✅ **Todo On-Premise:**
- Datos nunca salen de tu red
- PostgreSQL en contenedor privado
- Sin conexión a servicios cloud obligatoria
- Red Docker aislada

---

## 📁 Estructura del Proyecto

```
hospital-dashboard-ai-poc/
├── backend/              # FastAPI + IA
│   ├── main.py          # API REST
│   ├── ai_generator.py  # Generador IA/Reglas
│   └── models.py        # Schemas Pydantic
├── frontend/            # Streamlit
│   ├── app.py          # Dashboard UI
│   └── requirements.txt
├── database/           # PostgreSQL
│   ├── schema.sql     # Esquema
│   └── generate_data.py # Datos sintéticos
├── docker/             # Docker Compose
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
└── docs/               # Documentación
    └── USAGE.md
```

---

## 🔍 Troubleshooting

**Errores comunes:**

| Problema | Solución |
|----------|----------|
| "Connection refused" | Esperar a que PostgreSQL esté listo: `docker-compose logs db` |
| "No data" | Regenerar datos: `python database/generate_data.py` |
| Frontend no carga | Verificar backend: http://localhost:8000/health |

---

## 📝 Licencia

MIT License - Uso libre para hospitales y centros de salud.

---

## 🤝 Contribuciones

¿Ideas para mejorar? Abre un issue o PR con:
- Nuevos tipos de gráficos
- Integración con HIS específicos
- Modelos de IA locales (llama.cpp, etc.)

---

<div align="center">

**[⬆ Volver al Inicio](#hospital-dashboard-ai)**

Made with 💙 for healthcare professionals

</div>
