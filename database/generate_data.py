#!/usr/bin/env python3
"""
Generador de datos sintéticos para Hospital Dashboard AI PoC
Genera datos realistas de urgencias, quirófanos, consultas y camas
"""

import random
import datetime
from datetime import timedelta
import json

# Configuración
random.seed(42)
# Generar datos desde hace 60 días hasta hoy (para que las queries de "últimos 7 días" funcionen)
FECHA_FIN = datetime.datetime.now()
FECHA_INICIO = FECHA_FIN - datetime.timedelta(days=60)
NUM_PACIENTES = 5000
NUM_URGENCIAS = 8000
NUM_CIRUGIAS = 2500
NUM_CONSULTAS = 12000
NUM_QUIROFANOS = 10

# Listas de datos
NOMBRES_M = ['Carlos', 'Juan', 'José', 'Antonio', 'Manuel', 'Francisco', 'David', 'Javier', 'Daniel', 'Miguel']
NOMBRES_F = ['María', 'Carmen', 'Ana', 'Isabel', 'Laura', 'Dolores', 'Pilar', 'Rosa', 'Cristina', 'Marta']
APELLIDOS = ['García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez', 'Sánchez', 'Pérez', 'Gómez', 'Martín']

ESPECIALIDADES = ['Cardiología', 'Traumatología', 'Cirugía General', 'Neurología', 'Oncología', 
                  'Pediatría', 'Ginecología', 'Urología', 'Oftalmología', 'Otorrino']

QUIROFANOS_ESPECIALIDAD = [
    ('Q-01', 'Cirugía General'),
    ('Q-02', 'Traumatología'),
    ('Q-03', 'Cardiología'),
    ('Q-04', 'Neurología'),
    ('Q-05', 'Ginecología'),
    ('Q-06', 'Oncología'),
    ('Q-07', 'Urología'),
    ('Q-08', 'Pediatría'),
    ('Q-09', 'Oftalmología'),
    ('Q-10', 'Otorrino'),
]

MOTIVOS_URGENCIA = ['Dolor torácico', 'Fractura', 'Accidente vascular', 'Dificultad respiratoria', 
                    'Traumatismo craneoencefálico', 'Intoxicación', 'Alergia', 'Golpe', 'Fiebre alta', 'Síncope']

TIPOS_CIRUGIA = ['Apendicitis', 'Hernia inguinal', 'Colecistectomía', 'Reemplazo cadera', 'Cataratas',
                 'Artroscopia rodilla', 'Bypass gástrico', 'Prostatectomía', 'Histerectomía', 'Cesárea']

CIRUJANOS = ['Dr. López Martínez', 'Dra. García Ruiz', 'Dr. Hernández Silva', 'Dr. Moreno Gómez', 
             'Dra. Sánchez Torres', 'Dr. Romero Castro', 'Dra. Vázquez Jiménez', 'Dr. Delgado Flores']

def random_fecha_inicio():
    """Genera fecha aleatoria entre inicio y fin"""
    dias_totales = (FECHA_FIN - FECHA_INICIO).days
    dias_random = random.randint(0, dias_totales)
    return FECHA_INICIO + timedelta(days=dias_random)

def generar_quirofano(id_quirofano, numero, especialidad):
    """Genera un quirófano"""
    return {
        'id': id_quirofano,
        'numero': numero,
        'especialidad': especialidad,
        'estado': random.choice(['DISPONIBLE', 'OCUPADO', 'LIMPIEZA'])
    }

def generar_paciente(id_paciente):
    """Genera un paciente sintético"""
    genero = random.choice(['M', 'F', 'O'])
    if genero == 'M':
        nombre = f"{random.choice(NOMBRES_M)} {random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
    elif genero == 'F':
        nombre = f"{random.choice(NOMBRES_F)} {random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
    else:
        nombre = f"{random.choice(NOMBRES_M)} {random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
    
    return {
        'id': id_paciente,
        'nombre': nombre,
        'edad': random.randint(0, 95),
        'genero': genero,
        'fecha_registro': random_fecha_inicio().isoformat(),
        'tipo_ingreso': random.choice(['URGENCIA', 'CONSULTA_EXTERNA', 'CIRUGIA_PROGRAMADA'])
    }

def generar_urgencia(id_urgencia, paciente_id):
    """Genera un registro de urgencias sintético"""
    fecha_entrada = random_fecha_inicio()
    
    # Triaje: 80% son niveles 3-5 (menos urgentes), 20% niveles 1-2 (urgentes)
    if random.random() < 0.2:
        triaje = random.randint(1, 2)
    else:
        triaje = random.randint(3, 5)
    
    # Tiempo de espera basado en triaje (nivel 1 = inmediato, nivel 5 = hasta 2 horas)
    if triaje == 1:
        espera_min = random.randint(0, 5)
    elif triaje == 2:
        espera_min = random.randint(5, 30)
    elif triaje == 3:
        espera_min = random.randint(30, 90)
    elif triaje == 4:
        espera_min = random.randint(60, 180)
    else:
        espera_min = random.randint(120, 300)
    
    fecha_atencion = fecha_entrada + timedelta(minutes=espera_min + random.randint(5, 60))
    
    # Destino
    destino_weights = [0.6, 0.25, 0.01, 0.14]  # ALTA, INGRESO, FALLECIMIENTO, FUGA
    destino = random.choices(['ALTA', 'INGRESO', 'FALLECIMIENTO', 'FUGA'], weights=destino_weights)[0]
    
    if destino == 'ALTA':
        estancia = random.randint(30, 240)  # minutos
        fecha_alta = fecha_atencion + timedelta(minutes=estancia)
    elif destino == 'INGRESO':
        estancia = random.randint(60, 10080)  # 1 hora a 1 semana
        fecha_alta = fecha_atencion + timedelta(minutes=estancia)
    else:
        fecha_alta = None
    
    return {
        'id': id_urgencia,
        'paciente_id': paciente_id,
        'fecha_entrada': fecha_entrada.isoformat(),
        'fecha_atencion_medica': fecha_atencion.isoformat(),
        'fecha_alta': fecha_alta.isoformat() if fecha_alta else None,
        'triaje_nivel': triaje,
        'motivo': random.choice(MOTIVOS_URGENCIA),
        'diagnostico': f"Diagnóstico {random.randint(1, 100)}",
        'destino': destino,
        'box': random.randint(1, 20)
    }

def generar_cirugia(id_cirugia, paciente_id):
    """Genera una cirugía sintética"""
    fecha_programada = random_fecha_inicio()
    hora_programada = datetime.time(random.randint(7, 17), random.choice([0, 15, 30, 45]))
    
    # 15% cancelaciones
    if random.random() < 0.15:
        motivos_cancela = ['Paciente no apto', 'Falta personal', 'Emergencia previa', 'Material no disponible']
        return {
            'id': id_cirugia,
            'paciente_id': paciente_id,
            'quirofano_id': random.randint(1, 10),
            'fecha_programada': fecha_programada.strftime('%Y-%m-%d'),
            'hora_inicio_programada': hora_programada.strftime('%H:%M'),
            'hora_inicio_real': None,
            'hora_fin': None,
            'tipo_cirugia': random.choice(TIPOS_CIRUGIA),
            'cirujano': random.choice(CIRUJANOS),
            'estado': 'CANCELADA',
            'motivo_cancelacion': random.choice(motivos_cancela)
        }
    
    # Retraso en inicio (0-60 min)
    retraso = random.randint(0, 60)
    hora_inicio_real = datetime.datetime.combine(fecha_programada.date(), hora_programada) + timedelta(minutes=retraso)
    
    # Duración de cirugía según tipo
    duracion = random.randint(45, 240)
    hora_fin = hora_inicio_real + timedelta(minutes=duracion)
    
    return {
        'id': id_cirugia,
        'paciente_id': paciente_id,
        'quirofano_id': random.randint(1, 10),
        'fecha_programada': fecha_programada.strftime('%Y-%m-%d'),
        'hora_inicio_programada': hora_programada.strftime('%H:%M'),
        'hora_inicio_real': hora_inicio_real.strftime('%H:%M'),
        'hora_fin': hora_fin.strftime('%H:%M'),
        'tipo_cirugia': random.choice(TIPOS_CIRUGIA),
        'cirujano': random.choice(CIRUJANOS),
        'estado': 'COMPLETADA',
        'motivo_cancelacion': None
    }

def generar_consulta(id_consulta, paciente_id):
    """Genera una consulta externa sintética"""
    fecha_sol = random_fecha_inicio()
    
    # Tiempo de espera (días hasta cita)
    espera_dias = random.choices([7, 14, 30, 60, 90], weights=[30, 40, 20, 7, 3])[0]
    fecha_cita = fecha_sol + timedelta(days=espera_dias)
    
    # 20% no-show
    if random.random() < 0.2:
        return {
            'id': id_consulta,
            'paciente_id': paciente_id,
            'especialidad': random.choice(ESPECIALIDADES),
            'medico': random.choice(CIRUJANOS),
            'fecha_cita': fecha_cita.isoformat(),
            'fecha_atencion': None,
            'estado': 'NO_SHOW',
            'tipo': random.choice(['PRIMERA_VISITA', 'REVISIT', 'CONTROL'])
        }
    elif random.random() < 0.1:
        return {
            'id': id_consulta,
            'paciente_id': paciente_id,
            'especialidad': random.choice(ESPECIALIDADES),
            'medico': random.choice(CIRUJANOS),
            'fecha_cita': fecha_cita.isoformat(),
            'fecha_atencion': None,
            'estado': 'CANCELADA',
            'tipo': random.choice(['PRIMERA_VISITA', 'REVISIT', 'CONTROL'])
        }
    
    fecha_atencion = fecha_cita + timedelta(minutes=random.randint(-5, 15))
    
    return {
        'id': id_consulta,
        'paciente_id': paciente_id,
        'especialidad': random.choice(ESPECIALIDADES),
        'medico': random.choice(CIRUJANOS),
        'fecha_cita': fecha_cita.isoformat(),
        'fecha_atencion': fecha_atencion.isoformat(),
        'estado': 'ATENDIDA',
        'tipo': random.choice(['PRIMERA_VISITA', 'REVISIT', 'CONTROL'])
    }

def generar_camas(num_camas=120):
    camas = []
    servicios = ['UCI', 'Medicina Interna', 'Pediatría', 'Cirugía', 'Urgencias']
    
    for i in range(1, num_camas + 1):
        servicio = servicios[(i - 1) % len(servicios)]
        r = random.random()
        if r < 0.65:
            estado = 'OCUPADA'
            paciente_id = random.randint(1, NUM_PACIENTES)
            fecha_ocu = (FECHA_FIN - datetime.timedelta(days=random.randint(1, 10))).date().isoformat()
        elif r < 0.90:
            estado = 'LIBRE'
            paciente_id = None
            fecha_ocu = None
        else:
            estado = 'LIMPIEZA'
            paciente_id = None
            fecha_ocu = None
            
        camas.append({
            'numero': 100 + i,
            'servicio': servicio,
            'estado': estado,
            'paciente_id': paciente_id,
            'fecha_ocupacion': fecha_ocu
        })
    return camas

def generar_todos_los_datos():
    """Genera el dataset completo"""
    print("Generando datos sintéticos del hospital...")
    
    # Quirófanos (PRIMERO)
    print(f"Generando {NUM_QUIROFANOS} quirófanos...")
    quirofanos = [generar_quirofano(i+1, QUIROFANOS_ESPECIALIDAD[i][0], QUIROFANOS_ESPECIALIDAD[i][1]) 
                  for i in range(NUM_QUIROFANOS)]
    
    # Pacientes
    print(f"Generando {NUM_PACIENTES} pacientes...")
    pacientes = [generar_paciente(i+1) for i in range(NUM_PACIENTES)]
    
    # Urgencias
    print(f"Generando {NUM_URGENCIAS} registros de urgencias...")
    urgencias = [generar_urgencia(i+1, random.randint(1, NUM_PACIENTES)) for i in range(NUM_URGENCIAS)]
    
    # Cirugías
    print(f"Generando {NUM_CIRUGIAS} cirugías...")
    cirugias = [generar_cirugia(i+1, random.randint(1, NUM_PACIENTES)) for i in range(NUM_CIRUGIAS)]
    
    # Consultas
    print(f"Generando {NUM_CONSULTAS} consultas externas...")
    consultas = [generar_consulta(i+1, random.randint(1, NUM_PACIENTES)) for i in range(NUM_CONSULTAS)]
    
    # Camas (NEW)
    print("Generando 120 camas...")
    camas = generar_camas(120)
    
    return {
        'quirofanos': quirofanos,
        'pacientes': pacientes,
        'urgencias': urgencias,
        'cirugias': cirugias,
        'consultas': consultas,
        'camas': camas
    }

def exportar_a_sql(datos, archivo_salida):
    """Exporta los datos a INSERTs SQL"""
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write("-- Datos sintéticos generados para Hospital Dashboard AI\n\n")
        
        # Quirófanos (PRIMERO - required by cirugias)
        f.write("\n-- Insert Quirófanos\n")
        for q in datos.get('quirofanos', []):
            f.write(f"INSERT INTO quirofanos (id, numero, especialidad, estado) VALUES ({q['id']}, '{q['numero']}', '{q['especialidad']}', '{q['estado']}');\n")
        
        # Pacientes
        f.write("\n-- Insert Pacientes\n")
        for p in datos['pacientes']:
            nombre_clean = p['nombre'].replace("'", "''")
            f.write(f"INSERT INTO pacientes (id, nombre, edad, genero, fecha_registro, tipo_ingreso) VALUES ({p['id']}, '{nombre_clean}', {p['edad']}, '{p['genero']}', '{p['fecha_registro']}', '{p['tipo_ingreso']}');\n")
        
        f.write("\n-- Insert Urgencias\n")
        for u in datos['urgencias']:
            fecha_alta = f"'{u['fecha_alta']}'" if u['fecha_alta'] else 'NULL'
            f.write(f"INSERT INTO urgencias (id, paciente_id, fecha_entrada, fecha_atencion_medica, fecha_alta, triaje_nivel, motivo, diagnostico, destino, box) VALUES ({u['id']}, {u['paciente_id']}, '{u['fecha_entrada']}', '{u['fecha_atencion_medica']}', {fecha_alta}, {u['triaje_nivel']}, '{u['motivo']}', '{u['diagnostico']}', '{u['destino']}', {u['box']});\n")
        
        f.write("\n-- Insert Cirugias\n")
        for c in datos['cirugias']:
            hora_real = f"'{c['hora_inicio_real']}'" if c['hora_inicio_real'] else 'NULL'
            hora_fin = f"'{c['hora_fin']}'" if c['hora_fin'] else 'NULL'
            motivo_clean = c['motivo_cancelacion'].replace("'", "''") if c['motivo_cancelacion'] else None
            motivo = f"'{motivo_clean}'" if motivo_clean else 'NULL'
            f.write(f"INSERT INTO cirugias (id, paciente_id, quirofano_id, fecha_programada, hora_inicio_programada, hora_inicio_real, hora_fin, tipo_cirugia, cirujano, estado, motivo_cancelacion) VALUES ({c['id']}, {c['paciente_id']}, {c['quirofano_id']}, '{c['fecha_programada']}', '{c['hora_inicio_programada']}', {hora_real}, {hora_fin}, '{c['tipo_cirugia']}', '{c['cirujano']}', '{c['estado']}', {motivo});\n")
        
        f.write("\n-- Insert Consultas Externas\n")
        for c in datos['consultas']:
            fecha_atencion = f"'{c['fecha_atencion']}'" if c['fecha_atencion'] else 'NULL'
            medico_clean = c['medico'].replace("'", "''")
            f.write(f"INSERT INTO consultas_externas (id, paciente_id, especialidad, medico, fecha_cita, fecha_atencion, estado, tipo) VALUES ({c['id']}, {c['paciente_id']}, '{c['especialidad']}', '{medico_clean}', '{c['fecha_cita']}', {fecha_atencion}, '{c['estado']}', '{c['tipo']}');\n")
            
        f.write("\n-- Insert Camas\n")
        for c in datos.get('camas', []):
            paciente_id = c['paciente_id'] if c['paciente_id'] else 'NULL'
            fecha_ocu = f"'{c['fecha_ocupacion']}'" if c['fecha_ocupacion'] else 'NULL'
            f.write(f"INSERT INTO camas (numero, servicio, estado, paciente_id, fecha_ocupacion) VALUES ({c['numero']}, '{c['servicio']}', '{c['estado']}', {paciente_id}, {fecha_ocu});\n")
    
    
    print(f"Datos exportados a {archivo_salida}")

if __name__ == '__main__':
    datos = generar_todos_los_datos()
    exportar_a_sql(datos, '../docker/seed_data.sql')
    print("\n✅ Generación completada!")
