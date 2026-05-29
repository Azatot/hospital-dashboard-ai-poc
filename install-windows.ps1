# 🏥 Hospital Dashboard AI - Script de Instalación Windows
# Ejecutar en PowerShell como Administrador

param(
    [string]$InstallPath = "C:\proyectos\hospital-dashboard",
    [string]$OpenRouterKey = ""
)

# Colores para output
function Write-Success { Write-Host "$args" -ForegroundColor Green }
function Write-Info { Write-Host "$args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "$args" -ForegroundColor Yellow }
function Write-Error { Write-Host "$args" -ForegroundColor Red }

# Banner
Write-Info @"
========================================
  🏥 Hospital Dashboard AI Installer
  Instalador para Windows
========================================
"@

# Verificar Docker
Write-Info "Verificando Docker..."
try {
    $dockerVersion = docker --version
    Write-Success "✓ Docker instalado: $dockerVersion"
} catch {
    Write-Error "✗ Docker no está instalado o no está en el PATH"
    Write-Info "Descarga Docker Desktop desde: https://www.docker.com/products/docker-desktop"
    exit 1
}

# Verificar Docker Desktop corriendo
try {
    docker ps | Out-Null
    Write-Success "✓ Docker Desktop está corriendo"
} catch {
    Write-Error "✗ Docker Desktop no está corriendo"
    Write-Info "Inicia Docker Desktop y vuelve a ejecutar este script"
    exit 1
}

# Crear directorio de instalación
Write-Info "Creando directorio de instalación..."
if (Test-Path $InstallPath) {
    Write-Warning "El directorio ya existe: $InstallPath"
    $response = Read-Host "¿Deseas sobrescribir? (S/N)"
    if ($response -ne "S") {
        Write-Info "Instalación cancelada"
        exit 0
    }
    Remove-Item -Recurse -Force $InstallPath
}

New-Item -ItemType Directory -Path $InstallPath | Out-Null
Write-Success "✓ Directorio creado: $InstallPath"

# Solicitar API Key si no se proporcionó
if ([string]::IsNullOrEmpty($OpenRouterKey)) {
    Write-Info @"
Para usar el chat IA, necesitas una API Key de OpenRouter:
1. Ve a https://openrouter.ai
2. Crea una cuenta
3. Genera una API Key (empieza con sk-or-v1-)
"@
    $OpenRouterKey = Read-Host "Introduce tu API Key de OpenRouter (o Enter para omitir)"
}

# Crear archivo .env
Write-Info "Configurando variables de entorno..."
$envContent = "OPENROUTER_API_KEY=$OpenRouterKey`nAPI_ENV=production"
Set-Content -Path "$InstallPath\docker\.env" -Value $envContent
Write-Success "✓ Archivo .env creado"

# Copiar archivos del proyecto
Write-Info "Los archivos del proyecto deben copiarse desde el servidor o descomprimirse desde el ZIP."
Write-Info "Ubicación del ZIP en el servidor: /home/ubuntu/hospital-dashboard-windows.tar.gz"

# Si los archivos ya existen en el directorio actual
if (Test-Path ".\hospital-dashboard-ai-poc") {
    Write-Info "Copiando archivos del proyecto..."
    Copy-Item -Recurse -Force ".\hospital-dashboard-ai-poc\*" $InstallPath
    Write-Success "✓ Archivos copiados"
}

# Construir imágenes Docker
if (Test-Path "$InstallPath\docker\docker-compose.yml") {
    Write-Info "Construyendo imágenes Docker..."
    Set-Location "$InstallPath\docker"
    
    try {
        docker-compose build 2>&1 | Out-Null
        Write-Success "✓ Imágenes construidas"
    } catch {
        Write-Error "✗ Error construyendo imágenes: $_"
        exit 1
    }
    
    # Iniciar servicios
    Write-Info "Iniciando servicios..."
    try {
        docker-compose up -d
        Write-Success "✓ Servicios iniciados"
    } catch {
        Write-Error "✗ Error iniciando servicios: $_"
        exit 1
    }
    
    # Esperar a que los servicios estén listos
    Write-Info "Esperando a que los servicios estén listos..."
    Start-Sleep -Seconds 15
    
    # Health check
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
        Write-Success "✓ API funcionando: $($health.status)"
    } catch {
        Write-Warning "⚠ La API podría no estar lista aún. Espera unos segundos."
    }
} else {
    Write-Warning "Los archivos del proyecto no están en $InstallPath"
    Write-Info "Descarga el ZIP y descomprime en $InstallPath"
}

# Resumen
Write-Success @"
========================================
  ✅ INSTALACIÓN COMPLETADA
========================================

📂 Ubicación: $InstallPath

🌐 URLs de acceso:
   Dashboard:  http://localhost:8501
   API Docs:   http://localhost:8000/docs
   Adminer:    http://localhost:8080

🗄️ Base de datos:
   Usuario: hospital
   Password: hospital123
   Database: hospital

📋 Próximos pasos:
1. Abre http://localhost:8501 en tu navegador
2. Ve al tab "Chat IA"
3. Escribe: "Ocupación de urgencias últimos 7 días"
4. ¡Disfruta tu dashboard!

🛑 Para detener:
   cd $InstallPath\docker
   docker-compose down

========================================
"@

# Abrir navegador
$startBrowser = Read-Host "¿Abrir el dashboard en el navegador? (S/N)"
if ($startBrowser -eq "S") {
    Start-Process "http://localhost:8501"
}
