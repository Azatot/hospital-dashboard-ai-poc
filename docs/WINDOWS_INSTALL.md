# 🏥 Hospital Dashboard AI - Instalación en Windows

Guía completa para desplegar el dashboard en tu equipo Windows 11.

---

## 📋 Requisitos Previos

| Requisito | Versión | Enlace |
|-----------|---------|--------|
| **Docker Desktop** | 4.x+ | https://www.docker.com/products/docker-desktop |
| **Git** | 2.x+ | https://git-scm.com/download/win |
| **PowerShell** | 7.x+ (opcional) | https://github.com/PowerShell/PowerShell |
| **OpenRouter API Key** | - | https://openrouter.ai |

---

## 🚀 Instalación Rápida (5 minutos)

### Paso 1: Clonar el Proyecto

Abre **PowerShell** o **CMD** y ejecuta:

```powershell
# Crear directorio de proyectos
mkdir C:\proyectos
cd C:\proyectos

# Clonar desde el servidor (requiere acceso SSH)
# Opción A: Si tienes acceso SSH al servidor
scp ubuntu@141.253.193.207:/home/ubuntu/hospital-dashboard-ai-poc C:\proyectos\hospital-dashboard

# Opción B: Descargar archivo ZIP
# (Te lo proporcionaré)
```

### Paso 2: Configurar Variables de Entorno

Crea un archivo `.env` en `C:\proyectos\hospital-dashboard\docker\`:

```env
OPENROUTER_API_KEY=sk-or-v1-TU_API_KEY_AQUI
```

### Paso 3: Iniciar con Docker

```powershell
cd C:\proyectos\hospital-dashboard\docker
docker-compose up -d
```

### Paso 4: Acceder al Dashboard

- **Dashboard:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs
- **Base de datos (Adminer):** http://localhost:8080

---

## 📦 Descarga del Proyecto

### Opción 1: Archivo ZIP desde el servidor

Te he preparado un paquete completo:

```bash
# Ejecutar en el servidor Ubuntu:
cd /home/ubuntu
tar -czvf hospital-dashboard-windows.tar.gz hospital-dashboard-ai-poc/
```

Descarga el archivo y descomprime en Windows.

### Opción 2: Copiar archivos directamente

```powershell
# Desde PowerShell con WinSCP o MobaXterm
# Descarga la carpeta completa
```

---

## 🔧 Estructura del Proyecto

```
hospital-dashboard-ai-poc/
├── backend/
│   ├── main.py              # API FastAPI
│   ├── ai_generator.py      # Generador de SQL con IA
│   ├── models.py            # Modelos Pydantic
│   └── requirements.txt     # Dependencias Python
│
├── frontend/
│   ├── app.py               # Dashboard Streamlit (Power BI Style)
│   └── requirements.txt     # Dependencias Streamlit
│
├── database/
│   ├── schema.sql           # Esquema PostgreSQL
│   ├── seed_data.sql        # Datos de prueba
│   └── generate_data.py     # Generador de datos sintéticos
│
├── docker/
│   ├── docker-compose.yml   # Orquestación de servicios
│   ├── Dockerfile.backend   # Imagen FastAPI
│   └── Dockerfile.frontend  # Imagen Streamlit
│
└── docs/
    └── WINDOWS_INSTALL.md   # Esta guía
```

---

## 🛠️ Instalación Detallada

### 1. Instalar Docker Desktop

1. Descarga Docker Desktop: https://www.docker.com/products/docker-desktop
2. Ejecuta el instalador
3. **Importante:** Habilita WSL 2 cuando lo solicite
4. Reinicia el equipo si es necesario
5. Verifica la instalación:

```powershell
docker --version
docker-compose --version
```

### 2. Configurar Docker Desktop

1. Abre Docker Desktop
2. Ve a **Settings** > **Resources**
3. Asigna al menos:
   - **Memory:** 4 GB
   - **CPU:** 2 cores
   - **Disk:** 20 GB
4. Guarda y reinicia Docker

### 3. Obtener API Key de OpenRouter

1.Ve a https://openrouter.ai
2. Crea una cuenta o inicia sesión
3. Ve a **Keys** > **Create Key**
4. Copia la API Key (empieza con `sk-or-v1-`)

### 4. Configurar el Proyecto

Crea el archivo `.env`:

```powershell
cd C:\proyectos\hospital-dashboard\docker
notepad .env
```

Contenido del `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-TU_API_KEY_REAL
API_ENV=production
```

### 5. Construir e Iniciar

```powershell
# Ir al directorio docker
cd C:\proyectos\hospital-dashboard\docker

# Construir imágenes (solo la primera vez)
docker-compose build

# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver estado de los servicios
docker-compose ps
```

### 6. Verificar que Funciona

```powershell
# Health check de la API
curl http://localhost:8000/health

# Health check de Streamlit
curl http://localhost:8501/_stcore/health

# Health check de la base de datos
curl http://localhost:8080
```

---

## 🌐 URLs de Acceso

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **📊 Dashboard** | http://localhost:8501 | Interfaz principal Power BI Style |
| **📡 API Docs** | http://localhost:8000/docs | Documentación Swagger |
| **🗄️ Adminer** | http://localhost:8080 | Gestor de base de datos |
| **🔴 Redis** | localhost:6379 | Cache (CLI) |

### Credenciales de Base de Datos

Para acceder via Adminer:
- **Sistema:** PostgreSQL
- **Servidor:** db
- **Usuario:** hospital
- **Contraseña:** hospital123
- **Base de datos:** hospital

---

## 📊 Usar el Dashboard

### Chat IA

1. Abre http://localhost:8501
2. Ve al tab **"🤖 Chat IA"**
3. Escribe consultas como:
   - "Ocupación de urgencias últimos 7 días"
   - "Distribución por nivel de triaje"
   - "Tasa de fugas por día"

### Navegación por Tabs

- **🏥 Urgencias:** KPIs y gráficos de urgencias
- **🔪 Quirófanos:** Gestión de cirugías
- **📋 Consultas:** Consultas externas
- **🛏️ Camas:** Ocupación hospitalaria
- **🤖 Chat IA:** Consultas en lenguaje natural

### Funcionalidades

- **📅 Filtros de fecha:** Selecciona el período en el sidebar
- **📊 Drill-down:** Click en los KPIs para ver detalles
- **📥 Exportar:** Botones Excel y PDF
- **🔔 Alertas:** Panel de alertas automáticas

---

## 🔄 Regenerar Datos de Prueba

Si necesitas datos actualizados:

```powershell
# Entrar al contenedor de la base de datos
docker exec -it hospital-dashboard-db bash

# Dentro del contenedor:
psql -U hospital -d hospital -c "TRUNCATE TABLE consultas_externas, cirugias, urgencias, pacientes CASCADE;"

# Salir del contenedor
exit

# Regenerar datos (desde PowerShell en el host)
cd C:\proyectos\hospital-dashboard\database
python generate_data.py

# Cargar nuevos datos
docker exec -i hospital-dashboard-db psql -U hospital -d hospital < ../docker/seed_data.sql
```

---

## 🛑 Comandos Útiles

### Detener el Dashboard

```powershell
cd C:\proyectos\hospital-dashboard\docker
docker-compose down
```

### Reiniciar

```powershell
docker-compose restart
```

### Ver Logs

```powershell
# Todos los servicios
docker-compose logs -f

# Solo frontend
docker-compose logs -f frontend

# Solo backend
docker-compose logs -f backend
```

### Limpiar Todo

```powershell
docker-compose down -v  # Elimina volúmenes
docker-compose down --rmi all  # Elimina imágenes
```

---

## ❓ Solución de Problemas

### Puerto en Uso

Si el puerto 8501 está ocupado:

```powershell
# Ver qué proceso usa el puerto
netstat -ano | findstr :8501

# Matar el proceso (reemplaza PID)
taskkill /PID <PID> /F
```

### Docker Desktop No Inicia

1. Verifica que WSL 2 esté instalado:
```powershell
wsl --list --verbose
```

2. Si no aparece, instala WSL 2:
```powershell
wsl --install
```

### Error de Conexión a la Base de Datos

```powershell
# Verificar que el contenedor está sano
docker ps | findstr hospital-dashboard-db

# Reiniciar solo la base de datos
docker-compose restart db

# Esperar 10 segundos y reiniciar el backend
docker-compose restart backend
```

### API Key No Funciona

1. Verifica que OpenRouter tenga créditos
2. Comprueba que la key empieza con `sk-or-v1-`
3. Asegúrate de que el `.env` está en `docker/`

---

## 📱 Acceso desde Móvil (Opcional)

Si quieres acceder desde otros dispositivos en tu red local:

1. Abre el puerto en el Firewall de Windows:
```powershell
New-NetFirewallRule -DisplayName "Hospital Dashboard" -Direction Inbound -LocalPort 8501,8000 -Protocol TCP -Action Allow
```

2. Accede desde otro dispositivo:
```
http://TU_IP_LOCAL:8501
```

Para encontrar tu IP local:
```powershell
ipconfig | findstr "IPv4"
```

---

## 🔐 Seguridad (Importante)

### Cambiar Contraseñas por Defecto

Edita `docker-compose.yml` y cambia:

```yaml
environment:
  POSTGRES_PASSWORD: TU_PASSWORD_SEGURO
```

### No Exponer en Internet

Este proyecto es para **uso local/educativo**. No lo expongas a internet sin:
- HTTPS
- Autenticación
- Firewall apropiado

---

## 📞 Soporte

Si tienes problemas:

1. **Logs:** `docker-compose logs -f`
2. **Estado:** `docker-compose ps`
3. **Health checks:**
   - API: http://localhost:8000/health
   - Streamlit: http://localhost:8501/_stcore/health

---

## ✅ Checklist de Instalación

- [ ] Docker Desktop instalado y corriendo
- [ ] Proyecto clonado/descargado
- [ ] Archivo `.env` configurado con API Key
- [ ] Imágenes construidas (`docker-compose build`)
- [ ] Servicios iniciados (`docker-compose up -d`)
- [ ] Dashboard accesible en http://localhost:8501
- [ ] API accesible en http://localhost:8000/docs
- [ ] Base de datos accesible en http://localhost:8080

---

**¡Listo!** Tu dashboard debería estar funcionando en http://localhost:8501
